import re, sys, pathlib, ast
from typing import List, Tuple

PAT = re.compile(r'\b(new\s+ObjectInputStream|readObject\s*\()')
SQL_PATTERN = re.compile(r'createStatement\(|executeQuery\(|createQuery\(|\"SELECT.*%\"|\+ *[a-zA-Z0-9_\.]+ *\+')

class FindJavaWeakpoint:
    def __init__(self):
        self.findings = []
        
    @staticmethod
    #Sql인젝션
    def scan_java_sql(p: pathlib.Path) -> List[Tuple[int, str]]:
        s = p.read_text(errors='ignore')
        hits = []
        for i, line in enumerate(s.splitlines(), start=1):
            if SQL_PATTERN.search(line):
                hits.append((i, f"Possible SQL usage: {line.strip()}"))
        return hits
    
    #역 직렬화
    def scan_file_deserialization(path: pathlib.Path) -> List[Tuple[int, str]]:
        s = path.read_text(encoding='utf-8', errors='ignore')
        hits = []
        for m in PAT.finditer(s):
            line = s.count('\n', 0, m.start()) + 1
            hits.append((line, s.splitlines()[line-1].strip()))
        return hits
    
    #runtime injection with AST
    def visit_Call(self, node):
        # eval / exec
        if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
            self.findings.append((node.lineno, f'Call to {node.func.id}'))
        # subprocess(..., shell=True)
        if getattr(node.func, 'attr', '') == 'Popen' or getattr(node.func, 'id', '') == 'Popen':
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append((node.lineno, 'subprocess shell=True'))
        self.generic_visit(node)

    #부적절한 인증/ 권한검사
    def scan_insecure_auth(path: pathlib.Path) -> List[Tuple[int, str]]:
        """
        검사 항목(예시):
         - 하드코딩된 비밀번호/시크릿 (password = "xxx", "secret", API_KEY = "...")
         - HTTP Basic Authorization 문자열 하드코딩
         - 인증 검사 없이 getParameter() 등을 바로 사용한 흔적(간단 탐지)
         - Java에서 문자열 비교에 == 사용한 경우(문자열 비교 오류 가능성)
        """
        text = path.read_text(errors='ignore')
        hits = []

        # 하드코딩된 비밀번호/토큰/키
        for m in re.finditer(r'\b(password|passwd|pwd|secret|api[_-]?key|token)\b\s*[=:]\s*["\'](.{1,200}?)["\']', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            keyname = m.group(1)
            hits.append((line, f"Hardcoded secret-like identifier '{keyname}'"))

        # request.getParameter("password") 같은 패턴 (인증검사 없이 파라미터 활용 가능성)
        for m in re.finditer(r'\bgetParameter\s*\(\s*["\']?(password|passwd|token|auth)[\'"]?\s*\)', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, f"Direct use of request parameter '{m.group(1)}' - ensure proper auth/validation"))

        # Java에서 문자열 비교에 == 사용 (문자열 비교 오류 가능성)
        for m in re.finditer(r'\".*?\" *== *[A-Za-z0-9_\.]+|[A-Za-z0-9_\.]+ *== *\".*?\"', text):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "Possible string comparison using '==' in Java - use .equals(...)"))

        # Basic Authorization 헤더 하드코딩
        for m in re.finditer(r'Authorization\s*:\s*["\']?Basic\s+[A-Za-z0-9=+/]+["\']?', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "Hardcoded Basic Authorization header detected"))

        return hits
    
    #불완전한 TLS/증명서 검증
    def scan_weak_tls(path: pathlib.Path) -> List[Tuple[int, str]]:
        """
        검사 항목(예시):
         - Java: HostnameVerifier that returns true, TrustManager that accepts all certs, setHostnameVerifier with permissive lambda
         - Python: requests(..., verify=False), ssl._create_unverified_context(), urllib3.disable_warnings(InsecureRequestWarning)
        """
        text = path.read_text(errors='ignore')
        hits = []

        # Java: HostnameVerifier 구현에서 always true
        for m in re.finditer(r'new\s+HostnameVerifier\s*\(\s*\)\s*{\s*public\s+boolean\s+verify\s*\(.*\)\s*{\s*return\s+true\s*;?', text, flags=re.S):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "HostnameVerifier.verify(...) returns true (accepts any host)"))

        # Java: setHostnameVerifier(... -> true) 또는 lambda returning true
        for m in re.finditer(r'\.setHostnameVerifier\s*\(\s*.*?->\s*true\s*\)', text, flags=re.S):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "setHostnameVerifier with permissive lambda (accepts any host)"))

        # Java: TrustManager that doesn't validate (All-trusting X509TrustManager)
        for m in re.finditer(r'X509TrustManager[\s\S]{0,200}?public\s+void\s+checkClientTrusted\s*\(.*\)\s*{\s*}', text, flags=re.S):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "Custom X509TrustManager with empty checkClientTrusted -> accepts any certificate"))

        # Python requests: verify=False
        for m in re.finditer(r'requests\.[a-zA-Z]+\([^)]*verify\s*=\s*False', text):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "requests(..., verify=False) - disables TLS certificate verification"))

        # Python: ssl._create_unverified_context()
        for m in re.finditer(r'ssl\._create_unverified_context\s*\(', text):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "ssl._create_unverified_context() used - disables TLS verification"))

        # urllib3 disable warnings (흔히 insecure 사용 표시)
        for m in re.finditer(r'urllib3\.disable_warnings\s*\(', text):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "urllib3.disable_warnings() used - check for verify=False usage elsewhere"))

        return hits
    
    #과도한 검증/ 민감정보 로그 노출
    def scan_sensitive_logging(path: pathlib.Path) -> List[Tuple[int, str]]:
        """
        검사 항목:
         - 로그 문자열에 'password', 'ssn', 'credit', 'card', 'secret', 'token' 등 포함
         - System.out.println/printf/print에서 민감정보 출력
         - logger.info/debug/error 으로 민감 키워드 출력
        """
        text = path.read_text(errors='ignore')
        hits = []
        sensitive_keywords = r'(password|passwd|pwd|secret|token|ssn|socialsecurity|creditcard|cardnum|ccnum|privatekey|apikey)'
        # Java logging: logger.info("password="+ pwd)
        for m in re.finditer(r'(logger\.(?:info|debug|warn|error|trace)\s*\([^)]*' + sensitive_keywords + r'[^)]*\))', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "Logging call contains sensitive keyword - avoid logging secrets"))

        # System.out / System.err prints
        for m in re.finditer(r'(System\.(?:out|err)\.(?:println|print|printf)\s*\([^)]*' + sensitive_keywords + r'[^)]*\))', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "System.out/System.err prints contain sensitive keyword - avoid printing secrets"))

        # Python logging / print
        for m in re.finditer(r'(logging\.(?:info|debug|warning|error)\s*\([^)]*' + sensitive_keywords + r'[^)]*\))', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "Python logging contains sensitive keyword - avoid logging secrets"))

        for m in re.finditer(r'(print\s*\([^)]*' + sensitive_keywords + r'[^)]*\))', text, flags=re.I):
            line = text.count('\n', 0, m.start()) + 1
            hits.append((line, "print() contains sensitive keyword - avoid printing secrets"))

        return hits
    
    #디렉토리 전체 스캔
    def scan_path(path: pathlib.Path) -> List[Tuple[pathlib.Path, int, str]]:
        """
        path가 파일이면 해당 파일 검사, 디렉토리면 재귀적으로 .java/.py 파일 검사하여 (file, lineno, message) 리스트 반환
        """
        results = []
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob('*'))
        for f in files:
            if not f.is_file():
                continue
            if f.suffix.lower() in ('.java', '.jsp', '.jspx'):
                # java 텍스트 기반 검사
                for (ln, msg) in (FindJavaWeakpoint.scan_java_sql(f) +
                                  FindJavaWeakpoint.scan_file_deserialization(f) +
                                  FindJavaWeakpoint.scan_insecure_auth(f) +
                                  FindJavaWeakpoint.scan_weak_tls(f) +
                                  FindJavaWeakpoint.scan_sensitive_logging(f)):
                    results.append((f, ln, msg))
            elif f.suffix.lower() in ('.py',):
                # python: 텍스트 검사 + ast 검사
                text = f.read_text(errors='ignore')
                # 텍스트 기반 유틸 검사 (민감로그, tls, auth)
                for (ln, msg) in (FindJavaWeakpoint.scan_insecure_auth(f) +
                                  FindJavaWeakpoint.scan_weak_tls(f) +
                                  FindJavaWeakpoint.scan_sensitive_logging(f)):
                    results.append((f, ln, msg))
                # AST 기반 검사
                try:
                    tree = ast.parse(text)
                    v = FindJavaWeakpoint()
                    v.visit(tree)
                    for ln, msg in v.findings:
                        results.append((f, ln, msg))
                except Exception:
                    # 파싱 실패(문법 오류 등)는 무시하되 필요시 로깅 가능
                    pass
            else:
                # 기타 확장자: 간단 텍스트 기반 검사(로그/ tls / auth 패턴만)
                try:
                    for (ln, msg) in (FindJavaWeakpoint.scan_insecure_auth(f) +
                                      FindJavaWeakpoint.scan_weak_tls(f) +
                                      FindJavaWeakpoint.scan_sensitive_logging(f)):
                        results.append((f, ln, msg))
                except Exception:
                    continue
        return results
    
if __name__ == '__main__':
    # 테스트용 절대경로를 직접 지정
    path = pathlib.Path("C:/taintboom/javaWeak.java").resolve()  # 원하는 절대경로로 수정

    if not path.exists():
        print(f"Error: path does not exist -> {path}")
        sys.exit(1)

    out = FindJavaWeakpoint.scan_path(path)
    for f, ln, msg in out:
        print(f"{f.resolve()}:{ln}: {msg}")