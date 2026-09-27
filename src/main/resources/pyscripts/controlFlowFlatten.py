r"""제어 흐름 평탄화 (control-flow flattening) — 보수적/안전 우선 버전.

메서드 본문이 "단순 문장들의 직선 시퀀스"일 때만, 디스패처 switch-loop 로 재작성한다:

    원본:
        public int f(int a) {
            int b = a + 1;
            b = b * 2;
            return b;
        }

    평탄화:
        public int f(int a) {
            int _s = 7;            // 무작위 시작 상태
            while (true) {
                switch (_s) {
                    case 7: { int b = a + 1; b = b * 2; return b; }
                    default: throw new RuntimeException();
                }
            }
        }

설계상 안전장치(하나라도 위반하면 None 반환 → 오케스트레이터가 원본 유지):
- 본문에 제어문(if/for/while/switch/try/do/synchronized) 또는 중괄호/람다/익명클래스(`{`)가
  있으면 평탄화하지 않는다.
- 지역 변수 선언부터 이어지는 문장들은 한 case 블록으로 묶어 원래 스코프, `final`,
  초기화 순서와 definite-assignment 의미를 유지한다.
- 상태값은 무작위로 섞어 의미 분석을 어렵게 한다.
- `return` 문 뒤에는 상태 전이를 붙이지 않는다(도달 불가 코드 컴파일 에러 방지).
- 최종 산출물은 levelObfuscate 의 javaValidate 안전망을 반드시 통과해야 적용된다.

이 변환은 import 가 필요 없다(java.lang.RuntimeException 만 사용).
"""

import re
import secrets

import javalang

_CONTROL_KEYWORDS = ("if", "for", "while", "switch", "try", "do",
                     "synchronized", "else", "case", "default", "catch",
                     "finally")

# 지역 변수 선언 시작점: 초기화 유무와 다중 선언자를 모두 tail-group 대상으로 본다.
_DECL_RE = re.compile(
    r'^\s*(?:final\s+)?'
    r'([A-Za-z_$][\w$.]*(?:\s*<[^;{}]*>)?(?:\s*\[\s*\])*)'  # 타입(제네릭/배열 허용)
    r'\s+([A-Za-z_$]\w*)(?:\s*\[\s*\])*'
    r'(?:\s*=\s*.+)?(?:\s*,\s*.+)*$'
)


class ControlFlowFlatten:
    def __init__(self, code):
        self.code = code
        self.obfuscated = self._flatten(code)

    def _flatten(self, code):
        if not code:
            return None

        try:
            member = javalang.parse.parse(
                "class __TaintBombFlowProbe__ { " + code + " }"
            ).types[0].body[0]
        except (javalang.parser.JavaSyntaxError, javalang.parser.JavaParserError,
                javalang.tokenizer.LexerError, IndexError):
            return None
        if isinstance(member, javalang.tree.ConstructorDeclaration):
            return None  # Constructor invocation/initialization order must stay intact.

        parsed = self._extract_method(code)
        if parsed is None:
            return None
        header, body = parsed

        statements = self._split_statements(body)
        if len(statements) < 2:
            return None  # 평탄화 가치 없음

        normalized = []
        for stmt in statements:
            s = stmt.strip().rstrip(";").strip()
            if s == "":
                continue
            if self._is_unsafe(s):
                return None
            if re.match(r'^\s*(?:final\s+)?var\s+', s):
                return None
            normalized.append(s)

        first_decl = next((index for index, stmt in enumerate(normalized)
                           if self._is_local_declaration(stmt)), None)
        ops = []
        prefix = normalized if first_decl is None else normalized[:first_decl]
        for stmt in prefix:
            ops.append((stmt + ";", self._is_terminal(stmt), False))
        if first_decl is not None:
            tail = normalized[first_decl:]
            # ponytail: group the declaration tail; add lexical last-use analysis only if
            # finer dispatcher granularity becomes necessary.
            ops.append((" ".join(stmt + ";" for stmt in tail),
                        self._is_terminal(tail[-1]), True))

        if not ops:
            return None

        return self._build(header, ops)

    @staticmethod
    def _is_terminal(stmt):
        return bool(re.match(r'^(return|throw)\b', stmt)) or stmt == "return"

    @staticmethod
    def _is_local_declaration(stmt):
        try:
            tree = javalang.parse.parse(
                "class __TaintBombFlowProbe__ { void f() { " + stmt + "; } }"
            )
            parsed = tree.types[0].body[0].body
            return bool(parsed and isinstance(parsed[0], javalang.tree.LocalVariableDeclaration))
        except Exception:
            return bool(_DECL_RE.match(stmt))

    @staticmethod
    def _is_unsafe(stmt):
        """평탄화하면 위험한 문장인지."""
        if "{" in stmt or "}" in stmt:
            return True
        if "->" in stmt:           # 람다
            return True
        # 제어 키워드로 시작하는 문장
        first = re.match(r'^\s*([A-Za-z_]\w*)', stmt)
        if first and first.group(1) in _CONTROL_KEYWORDS:
            return True
        if "::" in stmt:           # 메서드 레퍼런스는 보수적으로 허용해도 되지만 일단 안전 위주
            pass
        return False

    def _build(self, header, ops):
        # 고유한 무작위 상태 id 생성
        n = len(ops)
        ids = self._unique_states(n + 1)  # 마지막 하나는 terminal
        reserved = set(re.findall(
            r'\b[A-Za-z_$][\w$]*\b',
            header + " " + " ".join(stmt for stmt, _, _ in ops),
        ))
        state_var = "_s" + str(secrets.randbelow(100000))
        while state_var in reserved:
            state_var = "_s" + str(secrets.randbelow(100000))

        lines = []
        lines.append(f"    int {state_var} = {ids[0]};")
        lines.append("    while (true) {")
        lines.append(f"        switch ({state_var}) {{")
        for i, (stmt, is_return, grouped) in enumerate(ops):
            cur = ids[i]
            nxt = ids[i + 1]
            if grouped and is_return:
                lines.append(f"            case {cur}: {{ {stmt} }}")
            elif grouped:
                lines.append(
                    f"            case {cur}: {{ {stmt} {state_var} = {nxt}; break; }}"
                )
            elif is_return:
                # return 문 뒤에는 어떤 코드도 오면 안 된다(도달 불가).
                lines.append(f"            case {cur}: {stmt}")
            else:
                lines.append(f"            case {cur}: {stmt} {state_var} = {nxt}; break;")
        # terminal: 마지막 op 가 return 이 아니었다면 void 메서드이므로 return; 으로 종료
        if not ops[-1][1]:
            lines.append(f"            case {ids[n]}: return;")
        lines.append("            default: throw new RuntimeException();")
        lines.append("        }")
        lines.append("    }")

        body = "\n".join(lines)
        return f"{header} {{\n{body}\n}}\n"


    @staticmethod
    def _unique_states(k):
        pool = set()
        out = []
        while len(out) < k:
            v = secrets.randbelow(9000) + 1000
            if v not in pool:
                pool.add(v)
                out.append(v)
        return out

    @staticmethod
    def _extract_method(code):
        """메서드 헤더(시그니처)와 본문(중괄호 내부)을 분리.

        반환: (header_without_brace, body_without_outer_braces) 또는 None
        """
        brace = ControlFlowFlatten._find_char(code, "{")
        if brace == -1:
            return None
        header = code[:brace].strip()
        # 헤더가 메서드 시그니처처럼 보이는지 최소 확인 (괄호 포함)
        if "(" not in header or ")" not in header:
            return None
        # 본문 끝(짝 맞는 닫는 중괄호) 찾기
        depth = 0
        in_str = False
        str_ch = ""
        i = brace
        n = len(code)
        while i < n:
            ch = code[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == str_ch:
                    in_str = False
            else:
                if ch in ("\"", "'"):
                    in_str = True
                    str_ch = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        body = code[brace + 1:i]
                        # 본문 뒤에 다른 코드가 더 있으면(여러 메서드) 보수적으로 거부
                        if code[i + 1:].strip() != "":
                            return None
                        return header, body
            i += 1
        return None

    @staticmethod
    def _find_char(code, target):
        in_str = False
        str_ch = ""
        i = 0
        n = len(code)
        while i < n:
            ch = code[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == str_ch:
                    in_str = False
            else:
                if ch in ("\"", "'"):
                    in_str = True
                    str_ch = ch
                elif ch == target:
                    return i
            i += 1
        return -1

    @staticmethod
    def _split_statements(body):
        stmts = []
        buf = []
        brace = paren = 0
        in_str = False
        str_ch = ""
        i = 0
        n = len(body)
        while i < n:
            ch = body[i]
            if in_str:
                buf.append(ch)
                if ch == "\\" and i + 1 < n:
                    buf.append(body[i + 1])
                    i += 2
                    continue
                if ch == str_ch:
                    in_str = False
                i += 1
                continue
            if ch in ("\"", "'"):
                in_str = True
                str_ch = ch
                buf.append(ch)
            elif ch == "{":
                brace += 1
                buf.append(ch)
            elif ch == "}":
                brace -= 1
                buf.append(ch)
            elif ch == "(":
                paren += 1
                buf.append(ch)
            elif ch == ")":
                paren -= 1
                buf.append(ch)
            elif ch == ";" and paren == 0 and brace == 0:
                stmts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
            i += 1
        tail = "".join(buf).strip()
        if tail:
            stmts.append(tail)
        return [s for s in stmts if s]

    def get_obfuscated_code(self):
        return self.obfuscated


if __name__ == "__main__":
    sample = (
        "public int f(int a) {\n"
        "    int b = a + 1;\n"
        "    b = b * 2;\n"
        "    return b;\n"
        "}\n"
    )
    print(ControlFlowFlatten(sample).get_obfuscated_code())
