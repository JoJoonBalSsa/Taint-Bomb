from re import sub
import os

class removeComments:
    def __init__(self, project_path):
        print("주석 제거 작업 시작...")
        self.__find_java_files(project_path)
        print("주석 제거 완료.")


    def __find_java_files(self, project_path):
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    self.__process_file(file_path)


    def __process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            java_code = file.read()

        cleaned_code = self.__remove_comments(java_code)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_code)

        print(f"Processed: {file_path}")

    
    def __remove_comments(self, java_code):
        # 문자열 내부의 주석 기호를 임시로 대체
        code = sub(r'(".*?(?<!\\)")', lambda m: m.group(0).replace('//', '@@').replace('/*', '##').replace('*/', '%%'),
                    java_code)

        # 한 줄 주석 제거
        code = sub(r'//.*', '', code)

        # 여러 줄 주석 제거
        code = sub(r'/\*[\s\S]*?\*/', '', code)

        # 임시로 대체했던 문자열 내부의 기호들을 원래대로 복구
        code = code.replace('@@', '//').replace('##', '/*').replace('%%', '*/')

        # 빈 줄 제거
        code = '\n'.join(line for line in code.splitlines() if line.strip())

        return code



