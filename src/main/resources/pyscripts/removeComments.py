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
        in_declaration = False
        declaration_lines = []

        for i in range(len(lines)):
            current_line = lines[i].rstrip()

            if in_declaration:
                if current_line.strip() == '{':
                    # 선언부 끝에 중괄호 추가
                    declaration_lines[-1] += ' {'
                    result.extend(declaration_lines)
                    in_declaration = False
                    declaration_lines = []
                elif '{' in current_line.strip():
                    declaration_lines[-1] += current_line
                    result.extend(declaration_lines)
                    in_declaration = False
                    declaration_lines = []
                else:
                    declaration_lines.append(current_line)
            elif ('class ' in current_line or 'interface ' in current_line) and not current_line.endswith('{'):
                # 새로운 선언부 시작
                in_declaration = True
                declaration_lines.append(current_line)
            else:
                result.append(current_line)

        # 파일 끝에 미완성 선언부가 있는 경우 처리
        if declaration_lines:
            result.extend(declaration_lines)


        result.append("\n\n\n")
        return '\n'.join(result)

if __name__ == '__main__':
    import sys

    RemoveComments(sys.argv[1])