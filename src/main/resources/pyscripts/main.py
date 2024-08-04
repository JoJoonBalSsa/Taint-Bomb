import sys

from taintAnalysis import TaintAnalysis
from removeComments import RemoveComments
from stringObfuscate import StringObfuscate


def create_taint_result(output_path, flows):
    with open(output_path + "/result.txt", 'w', encoding='utf-8') as file:  # 결과 파일 생성
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


def main(output_folder, keyDecryptJava, stringDecryptJava):
    tainted = TaintAnalysis(output_folder)
    print_taint_result(tainted.flows)
    create_taint_result(output_folder, tainted.flows)

    RemoveComments(output_folder)
    StringObfuscate(output_folder, keyDecryptJava, stringDecryptJava)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python main.py <output_folder> <keyDecryptJava> <stringDecryptJava>")
        exit(1)

    output_folder = sys.argv[1]
    keyDecryptJava = sys.argv[2]
    stringDecryptJava = sys.argv[3]

    main(output_folder, keyDecryptJava, stringDecryptJava)