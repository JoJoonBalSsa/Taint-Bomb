import javalang
import os
from collections import defaultdict

class TaintAnalysis:
    __methods = defaultdict(list)
    __source_functions = [
        # 사용자 입력
        'next',
        'nextLine',
        'nextInt',
        'nextDouble',
        'readLine',


        # 네트워크 입력
        'getInputStream',
        'getParameter',
        'getParameterMap',
        'getHeader',
        'getCookies',

        # 환경 변수
        'getenv',
        'getProperty',

        # 데이터베이스 입력
        'getString',
        'getInt',
        'getDouble',

        # API 및 라이브러리 호출
        'getData', # 예시: 외부 API 호출 반환값

        # 세션 데이터
        'getAttribute'
    ]
    __sink_functions = [
        # 콘솔 출력
        'print',
        'println',
        'printf',
        'write',

        # 파일 출력
        'FileOutputStream',
        'FileWriter',
        'BufferedWriter',
        'PrintWriter',
        'OutputStreamWriter',
        'DataOutputStream',
        'writeBytes',
        'writeChars',
        'writeUTF',

        # 네트워크 출력
        'getOutputStream',
        'write',

        # 데이터베이스 업데이트
        'executeUpdate',
        'execute',

        # 로그 출력
        'log',
        'info',
        'warn',
        'error',

        # API 응답
        'getWriter',
        'getOutputStream',
        'write',
        'sendRedirect',
        'addHeader',
        'setHeader',
        'setStatus',
        'setContentType',

        # GUI 출력
        'setText',
        'append'
    ]
    __tainted_variables = []
    __flow = []
    flows = defaultdict(list)
    source_check = []

    #메서드 단위로 AST 노드 저장, Taint 변수 탐색 및 저장
    def __init__(self, java_folder_path): 
        # Step 1: Parse all Java files
        trees = self.__parse_java_files(java_folder_path)

        # Step 2: Extract methods and find tainted variables
        self.__taint_analysis(trees)

        # Step 3: Append flow
        self.__append_flow()


    def __parse_java_files(self, folder_path):
        """ Parse all Java files in the given folder and return a list of parsed ASTs. """
        trees = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.java'):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        source_code = file.read()
                    tree = javalang.parse.parse(source_code)
                    trees.append((file_path, tree))
        return trees


    def __taint_analysis(self, trees):
        for file_path, tree in trees:
            current_class = "UnknownClass"
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    current_class = node.name

                elif isinstance(node, javalang.tree.MethodDeclaration):
                    self.__extract_methods(node, current_class, file_path)
                
                elif isinstance(node, javalang.tree.ConstructorDeclaration):
                    self.__extract_methods(node, current_class, file_path)





    def __extract_methods(self, node, current_class, file_path):
        method_name = node.name
        self.__methods[(current_class, method_name)].append((file_path, node))

        count = 0
        for sub_path, sub_node in node:
            count +=1 # 각각의 taint 변수가 생겨난 지점 식별
            self.__extract_variables(sub_node, current_class, method_name, count)
            
    
    def __extract_variables(self, sub_node, current_class, method_name, count):
        # 변수 선언 및 정의일 때
        if isinstance(sub_node, javalang.tree.VariableDeclarator): 
            if isinstance(sub_node.initializer, javalang.tree.MethodInvocation):
                if sub_node.initializer.member in self.__source_functions:  
                    self.__tainted_variables.append((f"{current_class}.{method_name}", sub_node.name , count))
                    self.source_check.append((sub_node.name,sub_node.initializer.member,sub_node.initializer.qualifier))
                
            elif isinstance(sub_node.initializer, javalang.tree.ClassCreator):
                for arg in sub_node.initializer.arguments:
                    if isinstance(arg, javalang.tree.ClassCreator):
                        for inner_arg in arg.arguments:
                            if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                if inner_arg.member in self.__source_functions:
                                    self.__tainted_variables.append((f"{current_class}.{method_name}", sub_node.name, count))
                                    self.source_check.append((sub_node.name, inner_arg.member, inner_arg.qualifier))

        #변수 할당일 때
        elif isinstance(sub_node, javalang.tree.Assignment): 
            if isinstance(sub_node.value, javalang.tree.MethodInvocation):
                if sub_node.value.member in self.__source_functions: 
                    self.__tainted_variables.append((f"{current_class}.{method_name}", sub_node.expressionl.member , count))
                    self.source_check.append((sub_node.expressionl.member,sub_node.value.member,sub_node.value.qualifier))


    def __append_flow(self):
        for class_method, var, count in self.__tainted_variables:
            self.__flow.clear()
            self.__track_variable_flow(class_method, var, count)


    def __numbering(self, d, key_tuple):
        if key_tuple in d:
            base_key1, base_key2 = key_tuple
            i = 1
            new_key = (base_key1, f"{base_key2}_{i}")
            while new_key in d:
                i += 1
                new_key = (base_key1, f"{base_key2}_{i}")
            return new_key
        else:
            return key_tuple
    
 
    def __track_variable_flow(self, class_method, var_name, count=0): #변수 흐름 추적. (계속 추가 가능)
        class_name, method_name = class_method.split('.')
        self.__flow.append([class_method,var_name]) # 흐름 추가
        method_nodes = self.__methods.get((class_name, method_name), []) #메서드 단위로 저장해둔 노드로 바로바로 접근가능
        
        current_count=0
        for file_path, method_node in method_nodes:
            for path, node in method_node: #노드 내부 탐색
                current_count +=1

                # sink 탐색
                if isinstance(node, javalang.tree.MethodInvocation):
                    self.__if_find_sink(node, class_method, var_name, count, current_count)

                #변수 할당일 때
                if isinstance(node, javalang.tree.Assignment): 
                    self.__if_variable_assignment(node, class_method, var_name, count, current_count)

                # 지역변수 선언일 때
                elif isinstance(node, javalang.tree.LocalVariableDeclaration):  
                    self.__if_local_variable_declaration(node, class_method, var_name, count, current_count)

                # 메서드 호출일 때
                elif isinstance(node, javalang.tree.MethodInvocation):
                    self.__if_call_method(node, var_name, count, current_count)

                # for 문일 때
                elif isinstance(node, javalang.tree.ForStatement): 
                    self.__if_for_statement(node, class_method, var_name, count, current_count)

        if self.__flow:
            self.__flow.pop()
            
        
    def __if_find_sink(self, node, class_method, var_name, count, current_count):
        if count>current_count:
                return
        
        if node.member in self.__sink_functions and node.arguments:
            flow_added = False
            
            for arg in node.arguments:
                # 인자가 하나일 때
                if isinstance(arg, javalang.tree.MemberReference):
                    if arg.member == var_name:
                        flow_added = True
                        break
                # 인자가 피연산자 중 하나일 때
                else:
                    flow_added = self.__judge_binary_operation(arg, flow_added, var_name)
                    if flow_added == True:
                       break

            if flow_added:
                self.__flow.append([f"{node.member}------>"])
                # 새로운 키를 생성하고, 기존 키가 존재하면 새 키를 사용
                existing_key = (class_method, var_name)
                new_key = self.__numbering(self.flows, existing_key)
                if new_key not in self.flows:
                    self.flows[new_key] = []
                # flows에 __flow 복사
                self.flows[new_key].append(self.__flow[:])
                self.__flow.pop()      


    def __judge_binary_operation(self, arg, flow_added, var_name):
        if isinstance(arg, javalang.tree.BinaryOperation):
            if isinstance(arg.operandl, javalang.tree.MemberReference):
                if arg.operandl.member == var_name:
                    flow_added = True
                    return  flow_added# 하나의 인자만 확인하면 충분
            elif isinstance(arg.operandr, javalang.tree.MemberReference):
                if arg.operandr.member == var_name:
                    flow_added = True
                    return  flow_added# 하나의 인자만 확인하면 충분
            elif isinstance(arg.operandl, javalang.tree.BinaryOperation):
                flow_added = self.__judge_binary_operation(arg.operandl, flow_added, var_name)
                return flow_added


    def __if_variable_assignment(self, node, class_method, var_name, count, current_count):
        if isinstance(node.value, javalang.tree.MethodInvocation): # 2-2
            if node.value.arguments:
                for arg_index, arg in enumerate(node.value.arguments):
                    if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name and (count<current_count):      
                        self.__flow.append([node.value.member,var_name])
                        self.__track_variable_flow(class_method,node.expressionl.member,current_count) # 같은 메서드에서 추적

        if isinstance(node.value, javalang.tree.MethodInvocation) and (node.value.qualifier == var_name) and (count<current_count):
            self.__flow.append([node.value.member,var_name])
            self.__track_variable_flow(class_method,node.expressionl.member,current_count) # 같은 메서드에서 추적

        if isinstance(node.expressionl, javalang.tree.MemberReference) and node.value.member == var_name and (count<current_count) : # 1-1
            self.__track_variable_flow(class_method,node.expressionl.member,current_count)

        if isinstance(node.expressionl, javalang.tree.MemberReference) and node.expressionl.member == var_name and (count<current_count) : # 1-2
            #초기화 값이 Source 함수일 경우 추가 필요
            if count<current_count :
                return
    

    def __if_local_variable_declaration(self, node, class_method, var_name, count, current_count):
        for var_decl in node.declarators:
            if isinstance(var_decl.initializer, javalang.tree.MethodInvocation): # 2-2
                if var_decl.initializer.arguments:
                    for arg_index, arg in enumerate(var_decl.initializer.arguments):
                        if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name and (count<current_count):
                            #flow.append([class_method,var_name]) 이건 MethodInvocation 노드에서 추가할 듯
                            self.__track_variable_flow(class_method,var_decl.name,current_count) # 같은 메서드에서 추적

            if isinstance(var_decl.initializer, javalang.tree.MethodInvocation):
                if (var_decl.initializer.qualifier == var_name) and (count<current_count) : # 2-1
                    self.__flow.append([var_decl.initializer.member,var_name])
                    self.__track_variable_flow(class_method,var_decl.name,current_count) # 같은 메서드에서 추적

            if isinstance(var_decl.initializer, javalang.tree.MemberReference) and var_decl.initializer.member == var_name and (count<current_count) :  # 1-1
                self.__track_variable_flow(class_method, var_decl.name,current_count)


    def __if_call_method(self, node, var_name, count, current_count):
       if node.arguments: 
            for arg_index, arg in enumerate(node.arguments):
                if isinstance(arg, javalang.tree.MemberReference):
                    if arg.member == var_name and (count<current_count) : # 4-1                                            
                        class_method_2, var_name_2 = self.__call2method(node,arg_index)
                        var_name_2 = var_name if var_name_2 == None else var_name_2 # 소스코드에 없는 메서드 호출시 var_name_2 가 None 이 되는경우 방지
                        self.__track_variable_flow(class_method_2,var_name_2)
                        
                elif isinstance(arg, javalang.tree.BinaryOperation):
                    self.__process_binary_operation(arg, node, var_name, count, current_count)


    def __process_binary_operation(self, binary_op, node, var_name, count, current_count):
        # 재귀적으로 BinaryOperation을 탐색하여 모든 오퍼랜드를 처리
        if isinstance(binary_op.operandl, javalang.tree.BinaryOperation):
            self.__process_binary_operation(binary_op.operandl, node, var_name, count, current_count)
        elif isinstance(binary_op.operandl, javalang.tree.MemberReference):
            if binary_op.operandl.member == var_name:
                self.__track_variable_flow(f"{type(node).__name__}.{node.member}", binary_op.operandl.member)

        if isinstance(binary_op.operandr, javalang.tree.BinaryOperation):
            self.__process_binary_operation(binary_op.operandr, node, var_name, count, current_count)
        elif isinstance(binary_op.operandr, javalang.tree.MemberReference):
            if binary_op.operandr.member == var_name:
                self.__track_variable_flow(f"{type(node).__name__}.{node.member}", binary_op.operandr.member)
    
    def __call2method(self, node, arg_index):
        invoked_method = node.member
        for target_class_method, target_method_nodes in self.__methods.items():
            target_class_name, target_method_name = target_class_method
            if target_method_name == invoked_method:  # 문제: 메서드 이름은 같은데 클래스가 다르다면?
                for target_file_path, target_method_node in target_method_nodes:
                    if len(target_method_node.parameters) > arg_index:
                        new_var_name = target_method_node.parameters[arg_index].name
                        return f"{target_class_name}.{invoked_method}", new_var_name
        return "UnknownClass." + invoked_method, None  # 만약 소스코드에 정의되지 않은 함수라면


    def __if_for_statement(self, node, class_method, var_name, count, current_count):
        if isinstance(node.control, javalang.tree.EnhancedForControl):
            EFC = node.control
            if EFC.iterable.member == var_name:
                for var_decl in EFC.var.declarators:
                    if isinstance(var_decl, javalang.tree.VariableDeclarator) and (count<current_count) :
                        var_name_2 = var_decl.name
                        self.__track_variable_flow(class_method, var_name_2,current_count) # for 문 끝날때 까지만 추적하도록 수정 필요
