import re

class ApplyObfuscated:
    def __init__(self, file_path, method_code, obfuscated_code):
        self.content = re.sub(r'\s+', ' ', method_code.strip())

        self.content = self.open_file(file_path)
        self.content = self.replace_method(self.content, method_code, obfuscated_code)
        self.write_file(file_path, self.content)


    def open_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()


    def write_file(self, file_path, content):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)


    def replace_method(self, content, method_code, obfuscated_code):
        # 메소드 코드 정규화 (공백 제거)
        normalized_method_code = re.sub(r'\s+', '', method_code)

        # 메소드 이름 추출
        method_name = re.search(r'\w+\s*\(', method_code)
        if method_name:
            print(f"메소드 이름: {method_name.group().strip('(').strip()}")
            method_name = method_name.group().strip('(').strip()
        else:
            raise ValueError("메소드 이름을 찾을 수 없습니다.")

        # 메소드를 찾기 위한 정규 표현식 패턴
        pattern = r'(public|protected|private|static|\s)* +[\w\<\>\[\]]+\s+' + re.escape(method_name) + r'\s*\([^\)]*\)\s*\{'

        matches = list(re.finditer(pattern, content))
        if not matches:
            print(f"메소드 '{method_name}'를 찾을 수 없습니다.")
            return content

        for match in matches:
            start = match.start()
            end = self.find_method_end(content, start)

            if end == -1:
                print(f"메소드 '{method_name}'의 끝을 찾을 수 없습니다.")
                continue

            # 현재 메소드의 내용 추출 및 정규화
            current_method = content[start:end]
            normalized_current_method = re.sub(r'\s+', '', current_method)

            print("current : " + normalized_current_method)
            print("source : " + normalized_method_code)

            # 메소드 내용이 일치하는지 확인
            if normalized_current_method == normalized_method_code:
                content = content[:start] + obfuscated_code.strip() + content[end:]
                print(f"메소드 '{method_name}'가 성공적으로 대체되었습니다.\n")

                return content

        print(f"일치하는 내용의 메소드 '{method_name}'를 찾을 수 없습니다.")
        return content


    def find_method_end(self, content, start):
        brace_count = 0
        in_string = False
        string_char = ''

        for i in range(start, len(content)):
            if content[i] == '"' or content[i] == "'":
                if not in_string:
                    in_string = True
                    string_char = content[i]
                elif string_char == content[i] and content[i-1] != '\\':
                    in_string = False

            if not in_string:
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return i + 1

        return -1