from re import sub

from obfuscateTool import obfuscateTool


class RemoveComments:
    def __init__(self, project_path):
        print("주석 제거 작업 시작...")
        self.__process_file(project_path)
        print("주석 제거 완료.")

    def __process_file(self, project_path):
        java_files = obfuscateTool.parse_java_files(project_path)

        for path, tree, source_code in java_files:
            cleaned_code = self.__remove_comments(source_code)
            with open(path, 'w', encoding='utf-8') as file:
                file.write(cleaned_code)
            print(f"Processed: {path}")

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
