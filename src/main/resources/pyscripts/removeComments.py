import sys
import os
import re
import shutil

def remove_comments(java_code):
    # 문자열 내부의 주석 기호를 임시로 대체
    code = re.sub(r'(".*?(?<!\\)")', lambda m: m.group(0).replace('//', '@@').replace('/*', '##').replace('*/', '%%'), java_code)

    # 한 줄 주석 제거
    code = re.sub(r'//.*', '', code)

    # 여러 줄 주석 제거
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)

    # 임시로 대체했던 문자열 내부의 기호들을 원래대로 복구
    code = code.replace('@@', '//').replace('##', '/*').replace('%%', '*/')

    # 빈 줄 제거
    code = '\n'.join(line for line in code.splitlines() if line.strip())

    return code


def copy_folder_structure(input_path, output_folder):
    of_project_path = os.path.join(output_folder, 'ofProject')

    print("복사 시작...")
    if os.path.isdir(input_path):
        shutil.copytree(input_path, of_project_path)
    else:
        os.makedirs(of_project_path)
        shutil.copy2(input_path, of_project_path)
    print("복사 완료.")

    return of_project_path

def process_java_files(of_project_path):
    for root, _, files in os.walk(of_project_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                process_single_file(file_path)

def process_single_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()

    cleaned_code = remove_comments(java_code)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_code)

    print(f"Processed: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_path> <output_folder>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_folder = sys.argv[2]

    # of_project_path = copy_folder_structure(input_path, output_folder)

    print("주석 제거 작업 시작...")
    process_java_files(input_path)
    print("모든 파일 처리 완료.")
