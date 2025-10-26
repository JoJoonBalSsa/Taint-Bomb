import re


class ExtractOperations:
    def __init__(self, method_code):
        self.method_code = method_code
        self.expressions = self.extract_all_conditions()

    def extract_parentheses_content(self, code, start_index):
        """
        괄호 안의 내용을 수동으로 추출 (catastrophic backtracking 방지)
        Returns: (content, end_index) or (None, -1) if failed
        """
        if start_index >= len(code) or code[start_index] != '(':
            return None, -1

        depth = 0
        start = start_index
        max_iterations = len(code) * 2  # 안전장치
        iterations = 0

        for i in range(start_index, len(code)):
            iterations += 1
            if iterations > max_iterations:
                return None, -1

            if code[i] == '(':
                depth += 1
            elif code[i] == ')':
                depth -= 1
                if depth == 0:
                    return code[start + 1:i], i

        return None, -1  # 매칭되는 괄호 없음

    def find_if_conditions(self):
        results = []
        pattern = re.compile(r'\bif\s*\(')

        for match in pattern.finditer(self.method_code):
            paren_start = match.end() - 1  # '(' 위치
            content, _ = self.extract_parentheses_content(self.method_code, paren_start)
            if content is not None:
                results.append(content)

        return results

    def find_for_conditions(self):
        results = []
        pattern = re.compile(r'\bfor\s*\(')

        for match in pattern.finditer(self.method_code):
            paren_start = match.end() - 1
            content, _ = self.extract_parentheses_content(self.method_code, paren_start)
            if content is not None:
                results.append(content)

        return results

    def find_while_conditions(self):
        results = []
        pattern = re.compile(r'\bwhile\s*\(')

        for match in pattern.finditer(self.method_code):
            paren_start = match.end() - 1
            content, _ = self.extract_parentheses_content(self.method_code, paren_start)
            if content is not None:
                results.append(content)

        return results

    def find_do_while_conditions(self):
        do_while_pattern = re.compile(r'\bdo\s*\{.*?\}\s*while\s*\(', re.DOTALL)
        results = []

        for match in do_while_pattern.finditer(self.method_code):
            paren_start = match.end() - 1
            content, _ = self.extract_parentheses_content(self.method_code, paren_start)
            if content is not None:
                results.append(content)

        return results

    def extract_all_conditions(self):
        expressions = [self.find_if_conditions(), self.find_for_conditions(), self.find_while_conditions(),
                       self.find_do_while_conditions()]
        print(f"expressions : {expressions}")
        return expressions