import re, sys, pathlib, ast, bisect
from typing import List, Tuple

PAT = re.compile(r'\b(new\s+ObjectInputStream|readObject\s*\()')
SQL_PATTERN = re.compile(r'createStatement\(|executeQuery\(|createQuery\(|\"SELECT.*%\"|\+ *[a-zA-Z0-9_\.]+ *\+')

# 사전 컴파일: 동일 패턴을 매 호출마다 컴파일하던 비용을 제거.
_RE_HARDCODED_SECRET = re.compile(
    r'\b(password|passwd|pwd|secret|api[_-]?key|token)\b\s*[=:]\s*["\'](.{1,200}?)["\']',
    re.I,
)
_RE_GET_PARAMETER = re.compile(
    r'\bgetParameter\s*\(\s*["\']?(password|passwd|token|auth)[\'"]?\s*\)',
    re.I,
)
_RE_JAVA_EQ_STRING = re.compile(r'\".*?\" *== *[A-Za-z0-9_\.]+|[A-Za-z0-9_\.]+ *== *\".*?\"')
_RE_BASIC_AUTH = re.compile(r'Authorization\s*:\s*["\']?Basic\s+[A-Za-z0-9=+/]+["\']?', re.I)

_RE_HOSTNAME_VERIFIER = re.compile(
    r'new\s+HostnameVerifier\s*\(\s*\)\s*{\s*public\s+boolean\s+verify\s*\(.*\)\s*{\s*return\s+true\s*;?',
    re.S,
)
_RE_SET_HOSTNAME_VERIFIER = re.compile(r'\.setHostnameVerifier\s*\(\s*.*?->\s*true\s*\)', re.S)
_RE_X509_TRUST = re.compile(
    r'X509TrustManager[\s\S]{0,200}?public\s+void\s+checkClientTrusted\s*\(.*\)\s*{\s*}',
    re.S,
)
_RE_REQUESTS_VERIFY_FALSE = re.compile(r'requests\.[a-zA-Z]+\([^)]*verify\s*=\s*False')
_RE_SSL_UNVERIFIED = re.compile(r'ssl\._create_unverified_context\s*\(')
_RE_URLLIB3_DISABLE = re.compile(r'urllib3\.disable_warnings\s*\(')

_SENS_KW = r'(password|passwd|pwd|secret|token|ssn|socialsecurity|creditcard|cardnum|ccnum|privatekey|apikey)'
_RE_LOG_JAVA = re.compile(r'(logger\.(?:info|debug|warn|error|trace)\s*\([^)]*' + _SENS_KW + r'[^)]*\))', re.I)
_RE_LOG_SYSOUT = re.compile(r'(System\.(?:out|err)\.(?:println|print|printf)\s*\([^)]*' + _SENS_KW + r'[^)]*\))', re.I)
_RE_LOG_PY = re.compile(r'(logging\.(?:info|debug|warning|error)\s*\([^)]*' + _SENS_KW + r'[^)]*\))', re.I)
_RE_LOG_PRINT = re.compile(r'(print\s*\([^)]*' + _SENS_KW + r'[^)]*\))', re.I)


def _line_offsets(text: str):
    """줄 시작 오프셋 목록을 한 번만 만들어두면, 매 매치마다 O(log N) 으로 줄번호 변환이 가능."""
    offsets = [0]
    append = offsets.append
    pos = 0
    n = len(text)
    while pos < n:
        nl = text.find('\n', pos)
        if nl == -1:
            break
        append(nl + 1)
        pos = nl + 1
    return offsets


def _line_at(offsets, idx):
    return bisect.bisect_right(offsets, idx)


class FindJavaWeakpoint(ast.NodeVisitor):
    def __init__(self):
        self.findings = []

    @staticmethod
    def scan_java_sql(text: str, offsets) -> List[Tuple[int, str]]:
        hits = []
        for i, line in enumerate(text.splitlines(), start=1):
            if SQL_PATTERN.search(line):
                hits.append((i, f"Possible SQL usage: {line.strip()}"))
        return hits

    @staticmethod
    def scan_file_deserialization(text: str, offsets) -> List[Tuple[int, str]]:
        lines = text.splitlines()
        hits = []
        for m in PAT.finditer(text):
            ln = _line_at(offsets, m.start())
            if 1 <= ln <= len(lines):
                hits.append((ln, lines[ln - 1].strip()))
        return hits

    @staticmethod
    def scan_insecure_auth(text: str, offsets) -> List[Tuple[int, str]]:
        hits = []
        for m in _RE_HARDCODED_SECRET.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         f"Hardcoded secret-like identifier '{m.group(1)}'"))
        for m in _RE_GET_PARAMETER.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         f"Direct use of request parameter '{m.group(1)}' - ensure proper auth/validation"))
        for m in _RE_JAVA_EQ_STRING.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "Possible string comparison using '==' in Java - use .equals(...)"))
        for m in _RE_BASIC_AUTH.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "Hardcoded Basic Authorization header detected"))
        return hits

    @staticmethod
    def scan_weak_tls(text: str, offsets) -> List[Tuple[int, str]]:
        hits = []
        for m in _RE_HOSTNAME_VERIFIER.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "HostnameVerifier.verify(...) returns true (accepts any host)"))
        for m in _RE_SET_HOSTNAME_VERIFIER.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "setHostnameVerifier with permissive lambda (accepts any host)"))
        for m in _RE_X509_TRUST.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "Custom X509TrustManager with empty checkClientTrusted -> accepts any certificate"))
        for m in _RE_REQUESTS_VERIFY_FALSE.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "requests(..., verify=False) - disables TLS certificate verification"))
        for m in _RE_SSL_UNVERIFIED.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "ssl._create_unverified_context() used - disables TLS verification"))
        for m in _RE_URLLIB3_DISABLE.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "urllib3.disable_warnings() used - check for verify=False usage elsewhere"))
        return hits

    @staticmethod
    def scan_sensitive_logging(text: str, offsets) -> List[Tuple[int, str]]:
        hits = []
        for m in _RE_LOG_JAVA.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "Logging call contains sensitive keyword - avoid logging secrets"))
        for m in _RE_LOG_SYSOUT.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "System.out/System.err prints contain sensitive keyword - avoid printing secrets"))
        for m in _RE_LOG_PY.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "Python logging contains sensitive keyword - avoid logging secrets"))
        for m in _RE_LOG_PRINT.finditer(text):
            hits.append((_line_at(offsets, m.start()),
                         "print() contains sensitive keyword - avoid printing secrets"))
        return hits

    # runtime injection with AST (Python only)
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
            self.findings.append((node.lineno, f'Call to {node.func.id}'))
        if getattr(node.func, 'attr', '') == 'Popen' or getattr(node.func, 'id', '') == 'Popen':
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append((node.lineno, 'subprocess shell=True'))
        self.generic_visit(node)

    @staticmethod
    def scan_path(path: pathlib.Path) -> List[Tuple[pathlib.Path, int, str]]:
        results = []
        files = [path] if path.is_file() else list(path.rglob('*'))

        for f in files:
            if not f.is_file():
                continue
            suffix = f.suffix.lower()

            try:
                text = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            offsets = _line_offsets(text)

            if suffix in ('.java', '.jsp', '.jspx'):
                scanners = (
                    FindJavaWeakpoint.scan_java_sql,
                    FindJavaWeakpoint.scan_file_deserialization,
                    FindJavaWeakpoint.scan_insecure_auth,
                    FindJavaWeakpoint.scan_weak_tls,
                    FindJavaWeakpoint.scan_sensitive_logging,
                )
                for scan in scanners:
                    for ln, msg in scan(text, offsets):
                        results.append((f, ln, msg))
            elif suffix == '.py':
                for scan in (FindJavaWeakpoint.scan_insecure_auth,
                             FindJavaWeakpoint.scan_weak_tls,
                             FindJavaWeakpoint.scan_sensitive_logging):
                    for ln, msg in scan(text, offsets):
                        results.append((f, ln, msg))
                try:
                    tree = ast.parse(text)
                    v = FindJavaWeakpoint()
                    v.visit(tree)
                    for ln, msg in v.findings:
                        results.append((f, ln, msg))
                except Exception:
                    pass
            else:
                for scan in (FindJavaWeakpoint.scan_insecure_auth,
                             FindJavaWeakpoint.scan_weak_tls,
                             FindJavaWeakpoint.scan_sensitive_logging):
                    try:
                        for ln, msg in scan(text, offsets):
                            results.append((f, ln, msg))
                    except Exception:
                        continue

        return results


if __name__ == '__main__':
    path = pathlib.Path("C:/taintboom/javaWeak.java").resolve()
    if not path.exists():
        print(f"Error: path does not exist -> {path}")
        sys.exit(1)
    out = FindJavaWeakpoint.scan_path(path)
    for f, ln, msg in out:
        print(f"{f.resolve()}:{ln}: {msg}")
