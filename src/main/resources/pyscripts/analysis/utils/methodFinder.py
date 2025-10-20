class MethodEndLineFinder:
    def __init__(self, source_lines):
        if isinstance(source_lines, str):
            self.source_lines = source_lines.splitlines()
        elif isinstance(source_lines, list):
            if all(isinstance(line, str) for line in source_lines):
                self.source_lines = source_lines
            else:
                self.source_lines = [''.join(line) if isinstance(line, list) else str(line) for line in source_lines]
        else:
            raise ValueError("Invalid source_lines format")

    def find_method_end_line(self, start_line):
        start_index = start_line - 1
        total_lines = len(self.source_lines)
        indent_level = self._get_indent_level(self.source_lines[start_index])
        brace_count = 0
        in_method = False

        for i in range(start_index, total_lines):
            line = self.source_lines[i]
            stripped_line = line.strip()

            # 빈 줄이나 주석은 건너뛰기
            if not stripped_line or stripped_line.startswith('//'):
                continue

            # 메소드 시작 확인
            if not in_method and '{' in line:
                in_method = True

            # 중괄호 카운트
            brace_count += self.count_braces(line)

            # 메소드 끝 조건 확인
            if in_method and brace_count == 0 and self._get_indent_level(line) <= indent_level and '}' in line:
                return i + 1  # 1-based line numbering

        return total_lines  # 파일 끝에 도달한 경우

    def count_braces(self, line):
        count = 0
        in_string = False
        in_char = False
        escape = False

        for char in line:
            if escape:
                escape = False
                continue

            if char == '\\':
                escape = True
            elif char == '"' and not in_char:
                in_string = not in_string
            elif char == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if char == '{':
                    count += 1
                elif char == '}':
                    count -= 1

        return count

    def _get_indent_level(self, line):
        return len(line) - len(line.lstrip())