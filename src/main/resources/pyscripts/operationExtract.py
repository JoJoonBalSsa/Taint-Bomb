import javalang


class ExtractOperations:
    def __init__(self, method_code):
        self.method_code = method_code
        self.conditions = self._extract_conditions()
        grouped = {"if": [], "for": [], "while": [], "do_while": []}
        for kind, start, end in self.conditions:
            grouped[kind].append(method_code[start:end])
        self.expressions = [
            grouped["if"], grouped["for"], grouped["while"], grouped["do_while"]
        ]

    @staticmethod
    def _line_offsets(code):
        offsets = [0]
        for index, char in enumerate(code):
            if char == "\n":
                offsets.append(index + 1)
        return offsets

    def _tokens(self):
        offsets = self._line_offsets(self.method_code)
        tokens = []
        try:
            raw_tokens = javalang.tokenizer.tokenize(self.method_code + "\n")
            for token in raw_tokens:
                start = offsets[token.position.line - 1] + token.position.column - 1
                if start >= len(self.method_code):
                    continue
                tokens.append((token.value, start, start + len(token.value)))
        except Exception:
            return []
        return tokens

    @staticmethod
    def _matching_paren(tokens, opening):
        depth = 0
        for index in range(opening, len(tokens)):
            value = tokens[index][0]
            if value == "(":
                depth += 1
            elif value == ")":
                depth -= 1
                if depth == 0:
                    return index
        return None

    @staticmethod
    def _for_condition(tokens, opening, closing):
        depth = 0
        semicolons = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        closers = set(pairs.values())
        for index in range(opening + 1, closing):
            value = tokens[index][0]
            if value in pairs:
                depth += 1
            elif value in closers:
                depth -= 1
            elif value == ";" and depth == 0:
                semicolons.append(index)
        if len(semicolons) != 2:
            return None
        return tokens[semicolons[0]][2], tokens[semicolons[1]][1]

    def _extract_conditions(self):
        tokens = self._tokens()
        conditions = []
        for index, (value, _, _) in enumerate(tokens[:-1]):
            if value not in {"if", "for", "while"} or tokens[index + 1][0] != "(":
                continue
            closing = self._matching_paren(tokens, index + 1)
            if closing is None:
                continue
            kind = value
            if value == "for":
                span = self._for_condition(tokens, index + 1, closing)
                if span is None:
                    continue
                start, end = span
            else:
                start, end = tokens[index + 1][2], tokens[closing][1]
                if value == "while" and index > 0:
                    kind = "do_while" if tokens[index - 1][0] == "}" else "while"
            if self.method_code[start:end].strip():
                conditions.append((kind, start, end))
        return conditions

    def extract_parentheses_content(self, code, start_index):
        if start_index >= len(code) or code[start_index] != "(":
            return None, -1
        depth = 0
        for index in range(start_index, len(code)):
            if code[index] == "(":
                depth += 1
            elif code[index] == ")":
                depth -= 1
                if depth == 0:
                    return code[start_index + 1:index], index
        return None, -1

    def find_if_conditions(self):
        return self.expressions[0]

    def find_for_conditions(self):
        return self.expressions[1]

    def find_while_conditions(self):
        return self.expressions[2]

    def find_do_while_conditions(self):
        return self.expressions[3]

    def extract_all_conditions(self):
        return self.expressions
