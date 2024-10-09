import os
import javalang
import sys

# 특정 디렉토리에서 모든 .java 파일을 찾아 파싱하는 함수
def parse_java_files_in_directory(directory_path):
    java_files = []

    # 디렉토리 내부 모든 파일 탐색
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                java_files.append(file_path)

    parsed_files = {}

    # 각 파일 파싱
    for java_file in java_files:
        with open(java_file, 'r', encoding='utf-8') as f:
            java_code = f.read()
            try:
                # Java 코드 파싱
                tree = javalang.parse.parse(java_code)
                parsed_files[java_file] = tree
            except javalang.parser.JavaSyntaxError as e:
                print(f"Error parsing {java_file}")
                exit(1)
            except javalang.parser.JavaParserError as e:
                print(f"Error parsing {java_file}")
                exit(1)
            except javalang.parser.JavaParserBaseException as e:
                print(f"Error parsing {java_file}")
                exit(1)
            except Exception as e:
                print(f"Error parsing {java_file} : {e}")
                exit(1)

    return parsed_files


# 실제로 디렉토리의 Java 파일을 파싱하고 결과 출력
if __name__ == "__main__":
    directory_path = sys.argv[1]
    parse_java_files_in_directory(directory_path)