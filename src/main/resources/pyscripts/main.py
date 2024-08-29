import sys

from taintAnalysis import TaintAnalysis
from removeComments import RemoveComments
from stringObfuscate import StringObfuscate
from analysisResultManager import AnalysisResultManager


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


def print_result(flows):
    for f in flows:
        print(f)
    print()



#
# def print_taint_result(flows, source):
#     for (class_method, var), value in flows.items():
#         print("Tainted Variable: ")
#         print(f"{class_method}, {var}")
#         print("흐름 파악")
#         for f in value:
#             if isinstance(f[0], list):  # 이중 리스트인 경우
#                 for sub_f in f:
#                     print(sub_f)
#                 else:
#                     print(f)
#         print()
#
#     for i,j,k in source:
#         print(i,j,k)
#         print()


def __analyze_method(output_folder, tainted):
    json_file_path = output_folder + "/analysis_result.json"
    result = AnalysisResultManager(json_file_path)

    flows = tainted._priority_flow()

    for flow in flows:
        sensitivity = flow[0]  # 민감도 값

        for count in range(1, len(flow)):
            method_full_path = flow[count]
            parts = method_full_path.split('.')
            method_name = parts[1]

            cut_tree = tainted._get_cut_tree(method_name)
            current_path = tainted._file_path
            tree_position = tainted._get_position
            source_code = tainted._extract_method_source_code()

            result.append(sensitivity, current_path, method_name, tree_position, cut_tree, source_code)
            method_name = method_full_path

    result.save_to_json()  # 결과를 JSON 파일로 저장



def main(output_folder, keyDecryptJava, stringDecryptJava):
    RemoveComments(output_folder)
    StringObfuscate(output_folder, keyDecryptJava, stringDecryptJava)

    tainted = TaintAnalysis(output_folder)

    print_result(tainted._priority_flow())
    create_taint_result(output_folder, tainted.flows)
    __analyze_method(output_folder, tainted)


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
