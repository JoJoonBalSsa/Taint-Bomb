import secrets
import javalang
import os
import secrets
import re


class ObfuscateTool:
    def random_class(class_list, random_count):
        leng = len(class_list)

        random_indices = [secrets.randbelow(leng) for _ in range(random_count)]
        random_class = [class_list[i] for i in random_indices]

        return random_class

    def overwrite_file(path, cleaned_code):
        with open(path, 'w', encoding='utf-8') as file:
            file.write(cleaned_code)

    def parse_java_files(folder_path):
        java_files = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.java'):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        source_code = file.read()

                    try:
                        tree = javalang.parse.parse(source_code)
                        java_files.append((file_path, tree, source_code))
                    except SyntaxError as e:  # 문법 오류는 파이썬의 SyntaxError로 처리
                         print(f"Syntax error in file {file_path}: {e}")
                    except javalang.parser.JavaSyntaxError as e:
                        print(f"Java syntax error in file {file_path}: {e}")

        return java_files

    def convert_unicode_literals(folder_path):
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.java'):
                    file_path = os.path.join(root, file_name)
                    content = None
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                    # 문자열 리터럴 찾기
                    string_literals = re.findall(r'"(.*?)"', content, re.DOTALL)

                    # 변환 결과를 저장할 리스트
                    modified_strings = []

                    for literal in string_literals:
                        modified_literal = ''
                        for char in literal:
                            # Unicode 범위에 해당하는 경우 \u 형식으로 변환
                            if ord(char) > 127:  # ASCII가 아닌 경우로 체크
                                modified_literal += f'\\u{ord(char):04x}'
                            else:
                                modified_literal += char
                        modified_strings.append(modified_literal)

                    # 원래 내용에서 문자열 리터럴을 변환한 내용으로 대체
                    for original, modified in zip(string_literals, modified_strings):
                        content = content.replace(f'"{original}"', f'"{modified}"')

                    # 변환된 내용을 파일에 덮어쓰기 (선택 사항)
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)


