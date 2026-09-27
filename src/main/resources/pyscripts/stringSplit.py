r"""문자열 리터럴 분해 인코딩 (string char-array / XOR split encoding).

메서드 본문 안의 단순 문자열 리터럴 `"text"` 를 런타임에 조립되는 문자 배열
표현식으로 치환한다:

    "abc"  ->  new String(new char[]{(char)(225 ^ 132), (char)(226 ^ 132), ...})

각 문자는 per-string 랜덤 키 K 로 XOR 되어 소스에는 평문이 남지 않는다. java.lang.String
만 사용하므로 import 가 필요 없고, 순수 식(expression)이라 어디에든 끼워 넣을 수 있다.
(기존 stringEncrypt 의 AES 방식과 달리 헬퍼 클래스/키 주입이 필요 없다.)

보수적 안전 장치:
- 백슬래시 이스케이프(\n, \", \uXXXX 등)가 포함된 리터럴은 건너뛴다(오인코딩 방지).
- BMP(<=0xFFFF) 밖 문자가 있으면 건너뛴다(char 캐스팅 안전).
- 애노테이션과 `switch` 라벨은 그대로 두고, `final` 상수와 문자열 상수 연결식은
  컴파일 타임 상수 XOR 표현식으로 치환한다.
- 주석/문자 리터럴 안의 따옴표는 토크나이저가 무시한다.
- 빈 문자열("")은 의미가 없으므로 건너뛴다.

결과는 항상 levelObfuscate 의 구문 검증 안전망(javaValidate)을 한 번 더 통과해야
실제 적용된다.
"""

import secrets

import javalang


class StringArraySplit:
    def __init__(self, code):
        self.code = code
        self.obfuscated = self._obfuscate(code)

    def _obfuscate(self, code):
        if not code:
            return None

        spans = self._find_string_literals(code)
        if not spans:
            return None

        constant_analysis = self._constant_expression_spans(code, spans)
        if constant_analysis is None:
            case_spans = self._case_label_spans(code)
            annotation_regions = self._annotation_regions(code)
            preserved_spans = case_spans | self._final_string_constant_spans(code, spans)
            preserved_spans |= self._literal_concat_spans(code, spans)
            constant_spans = set()
        else:
            constant_spans, preserved_spans = constant_analysis
            annotation_regions = []

        replaced_any = False
        # 오른쪽에서 왼쪽으로 치환해 인덱스가 밀리지 않게 한다.
        out = code
        for start, end, content in reversed(spans):
            if (start, end) in preserved_spans:
                continue
            # 애노테이션 인자(@Foo("x"))는 컴파일 타임 상수여야 하므로 건너뛴다.
            if self._in_any_region(start, annotation_regions):
                continue
            if "\\" in content:          # 이스케이프 포함 → 스킵
                continue
            if content == "":            # 빈 문자열 → 스킵
                continue
            if any(ord(ch) > 0xFFFF for ch in content):
                continue
            expr = (self._encode_constant(content)
                    if (start, end) in constant_spans else self._encode(content))
            out = out[:start] + expr + out[end:]
            replaced_any = True

        return out if replaced_any else None

    @staticmethod
    def _encode(text):
        key = secrets.randbelow(250) + 3  # 1..2 는 시각적으로 약하므로 3 이상
        parts = []
        for ch in text:
            enc = ord(ch) ^ key
            parts.append(f"(char)({enc} ^ {key})")
        return "new String(new char[]{" + ", ".join(parts) + "}).intern()"

    @staticmethod
    def _encode_constant(text):
        key = secrets.randbelow(250) + 3
        parts = [f"(char)({ord(ch) ^ key} ^ {key})" for ch in text]
        return "(\"\" + " + " + ".join(parts) + ")"

    @staticmethod
    def _find_string_literals(code):
        """(start, end, content) 목록. start 는 여는 따옴표, end 는 닫는 따옴표 다음 인덱스.

        주석(//, /* */), 문자 리터럴('x')을 인식해 그 안의 따옴표는 무시한다.
        """
        spans = []
        i = 0
        n = len(code)
        while i < n:
            ch = code[i]

            # 라인 주석
            if ch == "/" and i + 1 < n and code[i + 1] == "/":
                j = code.find("\n", i)
                i = n if j == -1 else j
                continue
            # 블록 주석
            if ch == "/" and i + 1 < n and code[i + 1] == "*":
                j = code.find("*/", i + 2)
                i = n if j == -1 else j + 2
                continue
            # 문자 리터럴 'x' / '\n'
            if ch == "'":
                j = i + 1
                while j < n:
                    if code[j] == "\\":
                        j += 2
                        continue
                    if code[j] == "'":
                        break
                    j += 1
                i = j + 1
                continue
            # 문자열 리터럴
            if ch == "\"":
                j = i + 1
                buf = []
                while j < n:
                    c = code[j]
                    if c == "\\":
                        buf.append(code[j:j + 2])
                        j += 2
                        continue
                    if c == "\"":
                        break
                    buf.append(c)
                    j += 1
                if j < n:  # 닫는 따옴표를 찾음
                    spans.append((i, j + 1, "".join(buf)))
                    i = j + 1
                    continue
                else:
                    break  # 닫히지 않은 문자열 → 중단
            i += 1
        return spans

    def _constant_expression_spans(self, code, spans):
        """String literals that must stay Java compile-time constants."""
        prefix = ""
        source = code
        try:
            tree = javalang.parse.parse(source)
        except Exception:
            prefix = "class __TaintBombStringProbe__ {\n"
            source = prefix + code + "\n}\n"
            try:
                tree = javalang.parse.parse(source)
            except Exception:
                return None

        offsets = [0]
        for index, char in enumerate(source):
            if char == "\n":
                offsets.append(index + 1)
        by_start = {start: (start, end) for start, end, _ in spans}

        def literal_span(node):
            if not node.position:
                return None
            wrapped_start = offsets[node.position.line - 1] + node.position.column - 1
            return by_start.get(wrapped_start - len(prefix))

        protected = set()
        preserved = set()
        for _, node in tree:
            if isinstance(node, javalang.tree.Annotation):
                preserved.update(self._literal_spans(node.element, literal_span))
            elif isinstance(node, javalang.tree.SwitchStatementCase):
                for label in node.case:
                    preserved.update(self._literal_spans(label, literal_span))
            elif (isinstance(node, (javalang.tree.FieldDeclaration,
                                    javalang.tree.LocalVariableDeclaration))
                  and "final" in node.modifiers
                  and self._is_constant_type(node.type)):
                for declarator in node.declarators:
                    protected.update(self._literal_spans(declarator.initializer, literal_span))
            elif isinstance(node, javalang.tree.BinaryOperation) and node.operator == "+":
                protected.update(self._literal_spans(node, literal_span))

        return protected, preserved

    @staticmethod
    def _type_name(type_node):
        names = []
        while type_node is not None:
            names.append(type_node.name)
            type_node = getattr(type_node, "sub_type", None)
        return names[-1] if names else ""

    @classmethod
    def _is_constant_type(cls, type_node):
        return cls._type_name(type_node) in {
            "byte", "short", "int", "long", "char", "float", "double",
            "boolean", "String",
        }

    @classmethod
    def _literal_spans(cls, node, span_for):
        spans = set()
        if isinstance(node, (list, tuple)):
            for item in node:
                spans.update(cls._literal_spans(item, span_for))
            return spans
        if isinstance(node, javalang.tree.Literal) and str(node.value).startswith('"'):
            span = span_for(node)
            if span:
                spans.add(span)
        for child in cls._node_children(node):
            spans.update(cls._literal_spans(child, span_for))
        return spans

    @staticmethod
    def _node_children(node):
        if not isinstance(node, javalang.ast.Node):
            return []
        children = []
        for child in node.children:
            if isinstance(child, (list, tuple)):
                children.extend(item for item in child if isinstance(item, javalang.ast.Node))
            elif isinstance(child, javalang.ast.Node):
                children.append(child)
        return children

    @staticmethod
    def _final_string_constant_spans(code, spans):
        """Common `final String name = "...";` initializer literals."""
        import re
        preserved = set()
        for start, end, _ in spans:
            statement_start = max(
                code.rfind(";", 0, start),
                code.rfind("{", 0, start),
                code.rfind("}", 0, start),
            )
            prefix = code[statement_start + 1:start]
            if (re.search(r'\bfinal\b', prefix)
                    and re.search(r'\b(?:java\.lang\.)?String\b', prefix)
                    and "=" in prefix):
                preserved.add((start, end))
        return preserved

    @staticmethod
    def _literal_concat_spans(code, spans):
        """Literal operands joined directly by `+` remain compile-time constants."""
        import re
        preserved = set()
        for left, right in zip(spans, spans[1:]):
            gap = code[left[1]:right[0]]
            gap = re.sub(r'/\*.*?\*/|//[^\n]*', '', gap, flags=re.DOTALL)
            if re.fullmatch(r'\s*\+\s*', gap):
                preserved.add((left[0], left[1]))
                preserved.add((right[0], right[1]))
        # ponytail: lexical guards cover common constant forms; use a Java parser for full JLS coverage.
        return preserved

    @staticmethod
    def _annotation_regions(code):
        """`@Name( ... )` 의 괄호 영역 (start, end) 목록.

        애노테이션 인자 안의 문자열 리터럴은 상수여야 하므로 치환 대상에서 제외한다.
        문자열/문자 리터럴을 인식해 괄호 균형을 정확히 맞춘다.
        """
        import re
        regions = []
        for m in re.finditer(r'@\s*[A-Za-z_$][\w$.]*\s*\(', code):
            open_paren = m.end() - 1
            depth = 0
            in_str = False
            str_ch = ""
            j = open_paren
            n = len(code)
            while j < n:
                ch = code[j]
                if in_str:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == str_ch:
                        in_str = False
                else:
                    if ch in ("\"", "'"):
                        in_str = True
                        str_ch = ch
                    elif ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            regions.append((open_paren, j))
                            break
                j += 1
        return regions

    @staticmethod
    def _in_any_region(pos, regions):
        for a, b in regions:
            if a <= pos <= b:
                return True
        return False

    @staticmethod
    def _case_label_spans(code):
        """`case "literal"` 의 문자열 리터럴 span 집합 (치환 제외 대상)."""
        import re
        spans = set()
        for m in re.finditer(r'\bcase\s*"', code):
            quote_pos = m.end() - 1  # 여는 따옴표 위치
            # 닫는 따옴표 탐색(이스케이프 고려)
            j = quote_pos + 1
            n = len(code)
            while j < n:
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "\"":
                    break
                j += 1
            if j < n:
                spans.add((quote_pos, j + 1))
        return spans

    def get_obfuscated_code(self):
        return self.obfuscated


if __name__ == "__main__":
    sample = (
        "public String greet(String who) {\n"
        '    String msg = "Hello, " + who;\n'
        '    String url = "https://example.com/api";\n'
        "    switch (who) {\n"
        '        case "admin": return "ADMIN";\n'
        "        default: return msg + url;\n"
        "    }\n"
        "}\n"
    )
    print(StringArraySplit(sample).get_obfuscated_code())
