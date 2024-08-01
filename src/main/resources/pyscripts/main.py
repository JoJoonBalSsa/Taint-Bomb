import sys

from taintAnalysis import taintAnalysis
from removeComments import removeComments

def create_taint_result(output_path, flows):
    with open(output_path + "result.txt", 'w', encoding='utf-8') as file:  # 결과 파일 생성
        for (class_method, var), value in flows.items():
            file.write("Tainted Variable:\n")
            file.write(f"{class_method}, {var}\n")
            file.write("흐름 파악\n")
            for f in value:
                file.write(f"{f}\n")
            file.write("\n")
    

def print_taint_result(flows):
    for (class_method, var), value in flows.items():
        print("Tainted Variable: ")
        print(f"{class_method}, {var}")
        print("흐름 파악")
        for f in flows[class_method, var]:
            print(f)
        print()


def main(java_folder_path, output_folder):
    # output_folder = copy_project_folder(java_folder_path, output_folder)

    tainted = taintAnalysis(java_folder_path)
    print_taint_result(tainted.flows)
    create_taint_result(output_folder, tainted.flows)

    removeComments(output_folder)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_path> <output_folder>")
        exit(1)

    input_path = sys.argv[1]
    output_folder = sys.argv[2]

    main(input_path, output_folder)