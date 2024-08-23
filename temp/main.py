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
                if isinstance(f[0], list):
                    for sub_f in f:
                        file.write(f"{sub_f}\n")
                    else:
                        file.write(f"{f}\n")
            file.write("\n")


def print_taint_result(flows, source):
    for (class_method, var), value in flows.items():
        print("Tainted Variable: ")
        print(f"{class_method}, {var}")
        print("흐름 파악")
        for f in value:
            if isinstance(f[0], list):  # 이중 리스트인 경우
                for sub_f in f:
                    print(sub_f)
                else:
                    print(f)
        print()
        
    for i,j,k in source:
        print(i,j,k)
        print()


def main(output_folder, keyDecryptJava, stringDecryptJava):
    tainted = TaintAnalysis(output_folder)
    print_taint_result(tainted.flows, tainted.source_check)
    create_taint_result(output_folder, tainted.flows)

    RemoveComments(output_folder)
    StringObfuscate(output_folder, keyDecryptJava, stringDecryptJava)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(len(sys.argv))
        for i in range(len(sys.argv)):
            print("arg : ", i)
            print(sys.argv[i])
            print(sys.argv[i])
        print("Usage: python main.py <output_folder> <keyDecryptJava> <stringDecryptJava>")
        exit(1)

    output_folder = sys.argv[1]
    keyDecryptJava = sys.argv[2]
    stringDecryptJava = sys.argv[3]

    main(output_folder, keyDecryptJava, stringDecryptJava)
