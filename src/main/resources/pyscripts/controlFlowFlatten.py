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
            int b;
            int _s = 7;            // 무작위 시작 상태
            while (true) {
                switch (_s) {
                    case 7: b = a + 1; _s = 3; break;
                    case 3: b = b * 2; _s = 9; break;
                    case 9: return b;
                    default: throw new RuntimeException();
                }
            }
        }

설계상 안전장치(하나라도 위반하면 None 반환 → 오케스트레이터가 원본 유지):
- 본문에 제어문(if/for/while/switch/try/do/synchronized) 또는 중괄호/람다/익명클래스(`{`)가
  있으면 평탄화하지 않는다.
- 지역 변수 선언은 단일 선언자(`Type name = expr;`)만 허용하고, 선언을 본문 위로 hoist 해
  case 간 스코프 문제를 없앤다. 다중 선언자/복잡한 선언은 거부.
- 상태값은 무작위로 섞어 의미 분석을 어렵게 한다.
- `return` 문 뒤에는 상태 전이를 붙이지 않는다(도달 불가 코드 컴파일 에러 방지).
- 최종 산출물은 levelObfuscate 의 javaValidate 안전망을 반드시 통과해야 적용된다.

이 변환은 import 가 필요 없다(java.lang.RuntimeException 만 사용).
"""

import re
import secrets

_CONTROL_KEYWORDS = ("if", "for", "while", "switch", "try", "do",
                     "synchronized", "else", "case", "default", "catch",
                     "finally")

# 단일 선언자 지역 변수 선언: "  final Map<String,Integer> name = expr"
_DECL_RE = re.compile(
    r'^\s*(?:final\s+)?'
    r'([A-Za-z_$][\w$.]*(?:\s*<[^;{}]*>)?(?:\s*\[\s*\])*)'  # 타입(제네릭/배열 허용)
    r'\s+([A-Za-z_$]\w*)\s*=\s*(.+)$'                       # 이름 = 초기화식
)


class ControlFlowFlatten:
    def __init__(self, code):
        self.code = code
        self.obfuscated = self._flatten(code)

    def _flatten(self, code):
        if not code:
            return None

        parsed = self._extract_method(code)
        if parsed is None:
            return None
        header, body = parsed

        statements = self._split_statements(body)
        if len(statements) < 2:
            return None  # 평탄화 가치 없음

        decls = []          # hoist 된 선언들: "Type name;"
        ops = []            # 각 case 본문: ("stmt", is_return)
        for stmt in statements:
            s = stmt.strip().rstrip(";").strip()
            if s == "":
                continue
            if self._is_unsafe(s):
                return None

            # 종결(terminal) 문장: 뒤에 코드가 오면 "도달 불가" 컴파일 에러가 난다.
            # return 뿐 아니라 throw 도 종결이므로 상태 전이를 붙이지 않는다.
            # (javalang 파싱은 도달 불가 코드를 잡지 못하므로 여기서 반드시 처리해야 한다.)
            is_terminal = bool(re.match(r'^(return|throw)\b', s)) or s == "return"
            m = None if is_terminal else _DECL_RE.match(s)
            if m:
                vtype, vname, init = m.group(1).strip(), m.group(2), m.group(3).strip()
                # `var` 는 초기화식 없이 재선언할 수 없다(`var x;` 는 컴파일 에러).
                # 안전하게 평탄화를 포기한다.
                if vtype == "var":
                    return None
                # ★ 핵심: hoist 한 선언은 기본값으로 "확정 초기화"해야 한다.
                # 디스패처(switch/while)를 통한 제어 흐름에서는 javac 의 definite-assignment
                # 분석이 "case A 가 case B 보다 먼저 실행됨"을 증명하지 못해
                # "variable might not have been initialized" 에러가 난다(javalang 은
                # 구문만 보므로 안전망이 못 잡는다). 직선 코드에서는 변수가 사용 전에
                # 반드시 대입되므로 기본값 초기화는 의미를 바꾸지 않는다.
                decls.append(f"{vtype} {vname} = {self._default_value(vtype)};")
                ops.append((f"{vname} = {init};", False))
            else:
                ops.append((s + ";", is_terminal))

        if not ops:
            return None

        return self._build(header, decls, ops)

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

    def _build(self, header, decls, ops):
        # 고유한 무작위 상태 id 생성
        n = len(ops)
        ids = self._unique_states(n + 1)  # 마지막 하나는 terminal
        state_var = "_s" + str(secrets.randbelow(100000))

        lines = []
        for d in decls:
            lines.append(f"    {d}")
        lines.append(f"    int {state_var} = {ids[0]};")
        lines.append("    while (true) {")
        lines.append(f"        switch ({state_var}) {{")
        for i, (stmt, is_return) in enumerate(ops):
            cur = ids[i]
            nxt = ids[i + 1]
            if is_return:
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
    def _default_value(vtype):
        """타입에 맞는 안전한 기본값 리터럴.

        배열/제네릭/참조 타입 → null, 숫자/문자 → 0, boolean → false.
        """
        base = vtype.strip()
        if base.endswith("]") or "<" in base:
            return "null"
        if base in ("int", "short", "byte", "long", "double", "float", "char"):
            return "0"
        if base == "boolean":
            return "false"
        return "null"

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
