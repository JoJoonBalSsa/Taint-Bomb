from re import sub

from obfuscateTool import ObfuscateTool


class RemoveComments:
    def __init__(self, project_path):
        print("주석 제거 및 스타일 통일 작업 시작...")

        java_files = ObfuscateTool.parse_java_files(project_path)
        self.__process_file(java_files)

        print("주석 제거 및 스타일 통일 완료.")


    def __process_file(self, java_files):
        for path, tree, source_code in java_files:
            cleaned_code = self.__remove_comments(source_code)
            formatted_code = self.__unify_brace_style(cleaned_code)
            ObfuscateTool.overwrite_file(path, formatted_code)
            print(f"processed: {path}")


    def __remove_comments(self, java_code):
        # 문자열 내부의 주석 기호를 임시로 대체
        code = sub(r'(".*?(?<!\\)")', lambda m: m.group(0).replace('//', '1^&32@16$').replace('/*', '1^&32@16&').replace('*/', '1^&32@16%'),
                   java_code)

        # 한 줄 주석 제거
        code = sub(r'//.*', '', code)

        # 여러 줄 주석 제거
        code = sub(r'/\*[\s\S]*?\*/', '', code)

        # 임시로 대체했던 문자열 내부의 기호들을 원래대로 복구
        code = code.replace('1^&32@16$', '//').replace('1^&32@16&', '/*').replace('1^&32@16%', '*/')

        # 빈 줄 제거
        code = '\n'.join(line for line in code.splitlines() if line.strip())

        return code


    def __unify_brace_style(self, code):
        lines = code.splitlines()
        result = []
        skip_next = False

        for i in range(len(lines)):
            if skip_next:
                skip_next = False
                continue

            current_line = lines[i].rstrip()

            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # class 선언부 패턴 확인
                if (('class ' in current_line or 'interface ' in current_line) and
                        not current_line.endswith('{') and
                        next_line == '{'):

                    # 클래스 선언부에 중괄호 추가
                    result.append(f"{current_line} {{")
                    skip_next = True
                else:
                    result.append(current_line)
            else:
                result.append(current_line)

        return '\n'.join(result)


if __name__ == '__main__':
    import sys

    RemoveComments(sys.argv[1])