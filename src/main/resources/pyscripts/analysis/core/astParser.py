import javalang
import os
import logging


class ASTParser:
    """Java 파일 AST 파싱을 담당하는 클래스"""

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def parse_java_files(self, folder_path):
        """주어진 폴더의 모든 Java 파일을 파싱하여 파일 경로, 소스 코드, AST를 반환"""
        trees = []
        source_codes = {}
        error_files = []
        success_files = []
        total_files = 0

        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.java'):
                    total_files += 1
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            source_code = file.read()
                        tree = javalang.parse.parse(source_code)
                        trees.append((file_path, tree))
                        source_codes[file_path] = source_code  # 파일 경로와 소스 코드를 딕셔너리에 저장
                        success_files.append(file_path)
                        self.logger.info(f"파싱 성공: {file_path}")
                    except SyntaxError as e:  # 문법 오류는 파이썬의 SyntaxError로 처리
                        print(f"Syntax error in file {file_path}: {e}")

                    except javalang.parser.JavaSyntaxError as e:
                        error_message = f"문법 오류 발생 in {file_path}: {str(e)}"
                        self.logger.error(error_message)
                        error_files.append((file_path, str(e)))

                    except javalang.parser.JavaParserError as e:
                        error_message = f"파싱 오류 발생 in {file_path}: {str(e)}"
                        self.logger.error(error_message)
                        error_files.append((file_path, str(e)))

        self.logger.info(f"총 {total_files}개의 파일 중 {len(success_files)}개 파싱 성공, {len(error_files)}개 파싱 실패")

        if error_files:
            self.logger.error("파싱 오류가 발생한 파일들:")
            for file_path, error in error_files:
                self.logger.error(f"  - {file_path}: {error}")

        return trees, source_codes  # 소스 코드와 AST를 함께 반환