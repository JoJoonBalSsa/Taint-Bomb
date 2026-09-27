import javalang

from operationExtract import ExtractOperations
from operationDB import OperationDB


_INTEGRAL = {"byte", "short", "char", "int", "long"}
_PRECEDENCE = [
    {"||"}, {"&&"}, {"|"}, {"^"}, {"&"}, {"==", "!="},
    {"<", "<=", ">", ">=", "instanceof"}, {"<<", ">>", ">>>"},
    {"+", "-"}, {"*", "/", "%"},
]
_ASSIGNMENTS = {
    "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "<<=", ">>=", ">>>=",
}
_PREFIX = {"!", "~", "+", "-"}


class _Node:
    def __init__(self, kind, start, end, value=None, left=None, right=None):
        self.kind = kind
        self.start = start
        self.end = end
        self.value = value
        self.left = left
        self.right = right


class _Expression:
    def __init__(self, source, symbols, templates):
        self.source = source
        self.symbols = symbols
        self.templates = templates
        self.tokens = self._tokenize()
        self.matches = self._delimiter_matches()

    @staticmethod
    def _line_offsets(source):
        offsets = [0]
        for index, char in enumerate(source):
            if char == "\n":
                offsets.append(index + 1)
        return offsets

    def _tokenize(self):
        offsets = self._line_offsets(self.source)
        raw = []
        for token in javalang.tokenizer.tokenize(self.source + "\n"):
            start = offsets[token.position.line - 1] + token.position.column - 1
            if start >= len(self.source):
                continue
            raw.append({
                "value": token.value,
                "kind": type(token).__name__,
                "start": start,
                "end": start + len(token.value),
            })

        tokens = []
        index = 0
        while index < len(raw):
            token = raw[index]
            if token["value"] == ">":
                count = 1
                while (
                    count < 3
                    and index + count < len(raw)
                    and raw[index + count]["value"] == ">"
                    and raw[index + count - 1]["end"] == raw[index + count]["start"]
                ):
                    count += 1
                if count > 1:
                    tokens.append({
                        "value": ">" * count,
                        "kind": "Operator",
                        "start": token["start"],
                        "end": raw[index + count - 1]["end"],
                    })
                    index += count
                    continue
            tokens.append(token)
            index += 1
        return tokens

    def _delimiter_matches(self):
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack = []
        matches = {}
        for index, token in enumerate(self.tokens):
            value = token["value"]
            if value in pairs:
                stack.append((value, index))
            elif value in pairs.values():
                if not stack or pairs[stack[-1][0]] != value:
                    return None
                _, opening = stack.pop()
                matches[opening] = index
                matches[index] = opening
        return matches if not stack else None

    def has_comments(self):
        if not self.tokens:
            return False
        gaps = [self.source[:self.tokens[0]["start"]]]
        gaps.extend(
            self.source[left["end"]:right["start"]]
            for left, right in zip(self.tokens, self.tokens[1:])
        )
        gaps.append(self.source[self.tokens[-1]["end"]:])
        return any(gap.strip() for gap in gaps)

    def parse(self):
        if not self.tokens or self.matches is None:
            return None
        return self._parse(0, len(self.tokens))

    def _parse(self, lower, upper):
        first = self.tokens[lower]
        last = self.tokens[upper - 1]
        if first["value"] == "(" and self.matches.get(lower) == upper - 1:
            child = self._parse(lower + 1, upper - 1)
            return _Node("group", first["start"], last["end"], left=child)

        top = self._top_level(lower, upper)
        if any(self.tokens[index]["value"] in _ASSIGNMENTS for index in top):
            return _Node("atom", first["start"], last["end"])
        if any(self.tokens[index]["value"] in {"?", ":", "->", "::"} for index in top):
            return _Node("atom", first["start"], last["end"])

        for operators in _PRECEDENCE:
            candidates = [
                index for index in top
                if self.tokens[index]["value"] in operators
                and self._is_binary(index, lower, upper)
            ]
            if candidates:
                operator = candidates[-1]
                left = self._parse(lower, operator)
                right = self._parse(operator + 1, upper)
                return _Node(
                    "binary", left.start, right.end,
                    value=self.tokens[operator]["value"], left=left, right=right,
                )

        if first["value"] in _PREFIX and lower + 1 < upper:
            child = self._parse(lower + 1, upper)
            return _Node("unary", first["start"], child.end, value=first["value"], left=child)
        return _Node("atom", first["start"], last["end"])

    def _top_level(self, lower, upper):
        result = []
        index = lower
        while index < upper:
            value = self.tokens[index]["value"]
            if value in {"(", "[", "{"}:
                closing = self.matches.get(index)
                if closing is None or closing >= upper:
                    return []
                index = closing + 1
                continue
            result.append(index)
            index += 1
        return result

    def _is_binary(self, index, lower, upper):
        value = self.tokens[index]["value"]
        if value not in {"+", "-"}:
            return index > lower and index + 1 < upper
        if index == lower:
            return False
        previous = self.tokens[index - 1]["value"]
        return previous not in (
            _ASSIGNMENTS | _PREFIX | {"(", "[", "{", ",", "?", ":", "&&", "||",
                                      "&", "|", "^", "==", "!=", "<", "<=", ">", ">=",
                                      "<<", ">>", ">>>", "*", "/", "%"}
        )

    def shape(self, node):
        if node.kind == "group":
            return self.shape(node.left)
        if node.kind == "binary":
            return (node.value, self.shape(node.left), self.shape(node.right))
        if node.kind == "unary":
            return (node.value, self.shape(node.left))
        return "atom"

    def render(self, node):
        if node.kind == "atom":
            return self.source[node.start:node.end]
        if node.kind == "group":
            return (
                self.source[node.start:node.left.start]
                + self.render(node.left)
                + self.source[node.left.end:node.end]
            )
        if node.kind == "unary":
            rendered = self.render(node.left)
            if node.value == "!":
                return self.templates["!"].format(a=rendered)
            if node.value == "~" and self.type_of(node.left) in _INTEGRAL:
                return self.templates["~"].format(a=rendered)
            return self.source[node.start:node.left.start] + rendered

        left = self.render(node.left)
        right = self.render(node.right)
        node_type = self.type_of(node)
        if node.value in {"+", "-", "*", "/", "%"} and node_type in {"int", "long"}:
            if node_type == "long":
                left = f"((long) ({left}))"
                right = f"((long) ({right}))"
            return self.templates[node.value].format(a=left, b=right)
        if node.value in {"&", "|", "^"} and node_type in {"int", "long"}:
            return self.templates[node.value + "_integral"].format(a=left, b=right)
        if node.value in {"&", "|", "^"} and node_type == "boolean":
            return self.templates[node.value + "_boolean"].format(a=left, b=right)
        if node.value in {"<<", ">>", ">>>"} and node_type in {"int", "long"}:
            return self.templates[node.value].format(a=left, b=right)
        if node.value in {"<", "<=", ">", ">="} and self._integral_operands(node):
            return self.templates[node.value].format(a=left, b=right)
        if node.value in {"==", "!=", "instanceof"}:
            return self.templates[node.value].format(a=left, b=right)
        if node.value in {"&&", "||"}:
            return self.templates[node.value].format(a=left, b=right)
        return left + self.source[node.left.end:node.right.start] + right

    def type_of(self, node):
        if node.kind == "group":
            return self.type_of(node.left)
        if node.kind == "atom":
            relevant = [
                token for token in self.tokens
                if token["start"] >= node.start and token["end"] <= node.end
            ]
            if len(relevant) != 1:
                return None
            token = relevant[0]
            if token["kind"] == "Identifier":
                return self.symbols.get(token["value"])
            if token["kind"] == "Boolean":
                return "boolean"
            if token["kind"] == "Character":
                return "int"
            if "Integer" in token["kind"]:
                return "long" if token["value"].lower().endswith("l") else "int"
            if "FloatingPoint" in token["kind"]:
                return "floating"
            return None
        if node.kind == "unary":
            operand = self.type_of(node.left)
            if node.value == "!":
                return "boolean" if operand == "boolean" else None
            if node.value in {"~", "+", "-"} and operand in _INTEGRAL:
                return "long" if operand == "long" else "int"
            return None

        left = self.type_of(node.left)
        right = self.type_of(node.right)
        if node.value in {"+", "-", "*", "/", "%", "&", "|", "^"}:
            if left in _INTEGRAL and right in _INTEGRAL:
                return "long" if "long" in {left, right} else "int"
            if node.value in {"&", "|", "^"} and left == right == "boolean":
                return "boolean"
        if node.value in {"<<", ">>", ">>>"} and left in _INTEGRAL and right in _INTEGRAL:
            return "long" if left == "long" else "int"
        if node.value in {"<", "<=", ">", ">=", "==", "!=", "instanceof", "&&", "||"}:
            return "boolean"
        return None

    def _integral_operands(self, node):
        return self.type_of(node.left) in _INTEGRAL and self.type_of(node.right) in _INTEGRAL


def _ast_shape(node):
    if isinstance(node, javalang.tree.BinaryOperation):
        shape = (node.operator, _ast_shape(node.operandl), _ast_shape(node.operandr))
    elif isinstance(node, (javalang.tree.TernaryExpression, javalang.tree.Assignment,
                           javalang.tree.LambdaExpression)):
        shape = (type(node).__name__,)
    else:
        shape = "atom"
    for operator in reversed(getattr(node, "prefix_operators", None) or []):
        shape = (operator, shape)
    return shape


def _symbol_types(source):
    symbols = {}
    try:
        tree = javalang.parse.parse("class __OperatorProbe__ {\n" + source + "\n}")
    except Exception:
        return symbols

    def record(name, type_node, extra_dimensions=False):
        name_type = getattr(type_node, "name", None)
        dimensions = getattr(type_node, "dimensions", None) or []
        primitive = name_type if name_type in _INTEGRAL | {"boolean", "float", "double"} else None
        if dimensions or extra_dimensions:
            primitive = None
        if name in symbols and symbols[name] != primitive:
            symbols[name] = None
        else:
            symbols[name] = primitive

    declarations = [
        node for node in tree.types[0].body
        if isinstance(node, (javalang.tree.MethodDeclaration, javalang.tree.ConstructorDeclaration))
    ]
    if len(declarations) != 1:
        return symbols

    declaration = declarations[0]
    direct_parameters = {id(parameter) for parameter in declaration.parameters}
    for parameter in declaration.parameters:
        record(parameter.name, parameter.type, parameter.varargs)

    # ponytail: without lexical scopes, any shadowing declaration makes the parameter unknown.
    for _, node in declaration:
        if isinstance(node, javalang.tree.FormalParameter) and id(node) not in direct_parameters:
            if node.name in symbols:
                symbols[node.name] = None
        elif isinstance(node, javalang.tree.LambdaExpression):
            for parameter in node.parameters:
                if (isinstance(parameter, javalang.tree.MemberReference)
                        and parameter.member in symbols):
                    symbols[parameter.member] = None
        elif isinstance(node, (javalang.tree.LocalVariableDeclaration,
                               javalang.tree.FieldDeclaration)):
            for declarator in node.declarators:
                if declarator.name in symbols:
                    symbols[declarator.name] = None
    return symbols


class ObfuscateOperations:
    def __init__(self, tainted):
        self.source_code = tainted["source_code"]
        self.op_json = OperationDB().op_db()
        self.symbols = _symbol_types(self.source_code)
        self.obfuscated = self._obfuscate()

    def return_obfuscated_code(self):
        return self.obfuscated

    def _obfuscate(self):
        result = self.source_code
        extractor = ExtractOperations(self.source_code)
        conditions = []
        for condition in sorted(extractor.conditions, key=lambda item: (item[1], -item[2])):
            if conditions and condition[1] < conditions[-1][2]:
                continue
            conditions.append(condition)
        for _, start, end in reversed(conditions):
            original = self.source_code[start:end]
            transformed = self.apply_operator_priority(original)
            result = result[:start] + transformed + result[end:]
        return result

    def apply_operator_priority(self, expression):
        try:
            parsed = javalang.parse.parse_expression(expression)
            tree = _Expression(expression, self.symbols, self.op_json)
            if tree.has_comments():
                return expression
            root = tree.parse()
            if root is None or tree.shape(root) != _ast_shape(parsed):
                return expression
            transformed = (
                expression[:root.start]
                + tree.render(root)
                + expression[root.end:]
            )
            javalang.parse.parse_expression(transformed)
            return transformed
        except Exception:
            return expression
