import javalang
import os
from collections import defaultdict
import sys

methods = []
flow = []

# 예제 Source 함수 배열, 나중에 변경 가능
source_functions = ['Console.readLine']


def call2method(node,arg_index):
    invoked_method = node.member
    for target_class_method, target_method_nodes in methods.items():
        target_class_name, target_method_name = target_class_method
        if target_method_name == invoked_method: # 문제 : 메서드이름은 같은데 클래스가 다르다면??
            for target_file_path, target_method_node in target_method_nodes:
                if len(target_method_node.parameters) > arg_index:
                    new_var_name = target_method_node.parameters[arg_index].name
                    return f"{target_class_name}.{invoked_method}", new_var_name
    return "UnknownClass."+invoked_method,None #만약 소스코드에 정의되지 않은 함수라면


def parse_java_files(folder_path):
    trees = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r',encoding='utf-8') as file:
                    source_code = file.read()
                tree = javalang.parse.parse(source_code)
                trees.append((file_path, tree))
    return trees


def extract_methods_and_find_tainted_variables(trees): #메서드 단위로 AST 노드 저장, Taint 변수 탐색 및 저장
    global methods

    methods = defaultdict(list)
    tainted_variables = []

    for file_path, tree in trees:
        current_class = "UnknownClass"
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                current_class = node.name
            elif isinstance(node, javalang.tree.MethodDeclaration):
                method_name = node.name
                methods[(current_class, method_name)].append((file_path, node))

                for sub_path, sub_node in node:
                    if isinstance(sub_node, javalang.tree.VariableDeclarator):
                        if isinstance(sub_node.initializer, javalang.tree.MethodInvocation):
                            invoked_method = f"{sub_node.initializer.qualifier}.{sub_node.initializer.member}" if sub_node.initializer.qualifier else sub_node.initializer.member
                            if invoked_method in source_functions:
                                tainted_variables.append((f"{current_class}.{method_name}", sub_node.name))

    return tainted_variables


def track_variable_flow(class_method, var_name, count=0): #변수 흐름 추적. (계속 추가 가능)
    global flow
    current_count=0
    # if (class_method == None): #예외처리
    #     flow.append(class_method,var_name)
    #     return


    class_name, method_name = class_method.split('.')
    flow.append([class_method,var_name]) # 흐름 추가

    method_nodes = methods.get((class_name, method_name), []) #메서드 단위로 저장해둔 노드로 바로바로 접근가능
    for file_path, method_node in method_nodes:
        for path, node in method_node: #노드 내부 탐색
            current_count +=1
            if isinstance(node, javalang.tree.Assignment): #변수 할당일 때

                # 클래스변수 할당일 때 b=taint (taint 늘어남)
                if isinstance(node.expressionl, javalang.tree.MemberReference) and node.value.member == var_name:
                    track_variable_flow(class_method,node.expressionl.member)

                #클래스변수 할당일 때 taint=b (taint 사라짐)
                if isinstance(node.expressionl, javalang.tree.MemberReference) and node.expressionl.member == var_name:
                    if(count>current_count):
                        return

            elif isinstance(node, javalang.tree.MethodInvocation): #메서드 호출일 때
                if node.arguments: # 메서드 호출할때 매개변수가 존재하는지
                    for arg_index, arg in enumerate(node.arguments):
                        if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name: #매개변수에 taint 변수가 있을 시
                            class_method_2, var_name_2 = call2method(node,arg_index) #매개변수로 넘어간경우
                            var_name_2 = var_name if var_name_2 == None else var_name_2 # 소스코드에 없는 메서드 호출시 var_name_2 가 None 이 되는경우 방지
                            track_variable_flow(class_method_2,var_name_2) # 재귀함수로 보내버리기~

            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                for var_decl in node.declarators:
                    if isinstance(var_decl.initializer, javalang.tree.MethodInvocation):
                        if var_decl.initializer.qualifier == var_name:
                            flow.append([var_decl.initializer.member,var_name])
                            track_variable_flow(class_method,var_decl.name) # 같은 메서드에서 추적

            elif isinstance(node, javalang.tree.ForStatement): #for
                if isinstance(node.control, javalang.tree.EnhancedForControl):
                    EFC = node.control
                    if EFC.iterable.member == var_name:
                        for var_decl in EFC.var.declarators:
                            if isinstance(var_decl, javalang.tree.VariableDeclarator):
                                var_name_2 = var_decl.name
                        track_variable_flow(class_method, var_name_2)



def main(java_folder_path, output_folder):
    global flow    

    # Step 1: Parse all Java files
    trees = parse_java_files(java_folder_path)
    # Step 2: Extract methods and find tainted variables
    tainted_variables = extract_methods_and_find_tainted_variables(trees)
    flows = {}

    for class_method, var in tainted_variables:
        flow = []
        track_variable_flow(class_method,var)
        flows[class_method,var] = flow # 다른 클래스의 같은이름의 메서드가 있을수 있기 때문에 key값은 두 변수 사용

    for class_method, var in tainted_variables: # 결과 print
        print("Tainted Variable: ")
        print(f"{class_method}, {var}")
        print("흐름 파악")
        for f in flows[class_method,var]:
            print(f)

        print()

    output_file = os.path.join(output_folder, 'ast_result.txt')

    with open(output_file, 'w') as file: # 결과 파일 생성

        for class_method, var in tainted_variables:
            file.write("Tainted Variable:\n")
            file.write(f"{class_method}, {var}\n")
            file.write("흐름 파악\n")
            for f in flows[class_method, var]:
                file.write(f"{f}\n")
            file.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <java_files_path> <output_folder>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
