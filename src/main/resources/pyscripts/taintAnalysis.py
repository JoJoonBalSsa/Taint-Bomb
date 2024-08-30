import javalang
import os
from collections import defaultdict
import logging
from sensitivityDB import SensitivityDB as S


class TaintAnalysis:
    __methods = defaultdict(list)

    __tainted_variables = []
    __flow = []
    _get_position=""
    _current_node=None
    _file_path=""
    source_codes = {}
    _t_tree=defaultdict(list)
    flows = defaultdict(list)
    method_check = []
    sink_check=[]

    #메서드 단위로 AST 노드 저장, Taint 변수 탐색 및 저장
    def __init__(self, java_folder_path):
        # Step 1: Parse all Java files
        trees = self.__parse_java_files(java_folder_path)

        # Step 2: Extract methods and find tainted variables
        self.__taint_analysis(trees)

        # Step 3: Append flow
        self.__append_flow()
        #self.__new_tree()


    def _priority_flow(self):
        prioritized_flows = []

        for (class_method, var), value in self.flows.items():
            for flow in self.flows[(class_method, var)]:
                # 흐름에서 첫 번째 항목 (source)와 마지막 항목 (sink)을 가져옴
                source_full = flow[0]  # 첫 번째 항목의 첫 번째 요소 추출
                sink_full = flow[-1]  # 마지막 항목의 첫 번째 요소 추출

                # 'a.b.c'에서 'c' 부분 추출
                source = source_full.split('.')[-1]
                sink = sink_full.split('.')[-1]

                # source와 sink의 민감도 값을 가져옴
                source_sensitivity = S.source_functions.get(source, 0)  # 기본값 0
                sink_sensitivity = S.sink_functions.get(sink, 0)        # 기본값 0

                # 민감도를 더함
                total_sensitivity = source_sensitivity + sink_sensitivity

                # 민감도를 0.5 단위로 반올림하여 1, 2, 3 중 하나로 설정
                rounded_sensitivity = round(total_sensitivity / 1.5) * 1.5

                # 민감도를 흐름 앞에 삽입
                prioritized_flow = [int(round(rounded_sensitivity))] + flow
                prioritized_flows.append(prioritized_flow)

        # 우선순위에 따라 flows를 정렬
        prioritized_flows.sort(reverse=True, key=lambda x: x[0])
        '''
        # 최종 결과 출력 (필요에 따라 반환하거나 다른 용도로 사용)
        for flow in prioritized_flows:
            print(flow)
        '''
        return prioritized_flows


    def __parse_java_files(self, folder_path):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        """ Parse all Java files in the given folder and return a dictionary of file paths to source codes and ASTs. """
        trees = []
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
                        self.source_codes[file_path] = source_code  # 파일 경로와 소스 코드를 딕셔너리에 저장
                        success_files.append(file_path)
                        logger.info(f"파싱 성공: {file_path}")
                    except Exception as e:
                        error_message = f"파싱 오류 발생 in {file_path}: {str(e)}"
                        logger.error(error_message)
                        error_files.append((file_path, str(e)))

        logger.info(f"총 {total_files}개의 파일 중 {len(success_files)}개 파싱 성공, {len(error_files)}개 파싱 실패")

        if error_files:
            logger.error("파싱 오류가 발생한 파일들:")
            for file_path, error in error_files:
                logger.error(f"  - {file_path}: {error}")

        return trees  # 소스 코드와 AST를 함께 반환


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
                if sub_node.initializer.member in S.source_functions.keys():
                    self.__tainted_variables.append((f"{current_class}.{method_name}.{sub_node.initializer.member}", sub_node.name , count))
                    self.method_check.append(method_name)

            elif isinstance(sub_node.initializer, javalang.tree.ClassCreator):
                for arg in sub_node.initializer.arguments:
                    if isinstance(arg, javalang.tree.ClassCreator):
                        for inner_arg in arg.arguments:
                            if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                if inner_arg.member in S.source_functions:
                                    self.__tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", sub_node.name, count))
                                    self.method_check.append(method_name)

        #변수 할당일 때
        elif isinstance(sub_node, javalang.tree.Assignment):
            if isinstance(sub_node.value, javalang.tree.MethodInvocation):
                if sub_node.value.member in S.source_functions:
                    self.__tainted_variables.append((f"{current_class}.{method_name}.{sub_node.value.member}", sub_node.expressionl.member , count))

        #TRY문
        elif isinstance(sub_node, javalang.tree.TryResource):
            if isinstance(sub_node.value, javalang.tree.ClassCreator):
                for arg in sub_node.value.arguments:
                    if isinstance(arg, javalang.tree.ClassCreator):
                        for inner_arg in arg.arguments:
                            if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                if inner_arg.member in S.source_functions:
                                    self.__tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", sub_node.name, count))


    def __append_flow(self):
        print("Tainted Variables: ", self.__tainted_variables)
        for class_method, var, count in self.__tainted_variables:
            self.__flow.clear()
            self.__track_variable_flow(class_method, var, count)


    def __numbering(self, d, key_tuple,node):
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


    def _get_end_line(self, node):
        """
        재귀적으로 노드의 마지막 줄을 찾는 함수.
        """
        if not hasattr(node, 'position') or node.position is None:
            return 0

        end_line = node.position.line

        # TryStatement 특별 처리
        if isinstance(node, javalang.tree.TryStatement):
            # try 블록 확인
            end_line = max(end_line, self._get_end_line(node.block))

            # catch 절 확인
            for catch in node.catches or []:
                end_line = max(end_line, self._get_end_line(catch))

            # finally 블록 확인
            if node.finally_block:
                end_line = max(end_line, self._get_end_line(node.finally_block))

        # 일반적인 자식 노드 처리
        for attr_name in dir(node):
            attr = getattr(node, attr_name)
            if isinstance(attr, list):
                for item in attr:
                    if isinstance(item, javalang.tree.Node):
                        end_line = max(end_line, self._get_end_line(item))
            elif isinstance(attr, javalang.tree.Node):
                end_line = max(end_line, self._get_end_line(attr))

        return end_line



    def _get_cut_tree(self, m_name):
        global _current_node

        for (class_name, method_name), method_nodes in self.__methods.items():
            if method_name == m_name:
                for file_path, method_node in method_nodes:
                    for path, node in method_node:
                        if isinstance(node, javalang.tree.MethodDeclaration) and node.name == method_name:
                            _current_node = node
                            self._file_path=file_path

                            # 시작 줄
                            start_line = node.position.line

                            # 끝 줄을 재귀적으로 계산합니다.
                            end_line = self._get_end_line(node)

                            # Store start and end positions in a single variable
                            self._get_position=f"{start_line}-{end_line}"
                            print(self._get_position)
                            # Return or use node_positions as needed
                            return self._method_declaration_to_string(node)


    def _method_declaration_to_string(self, method_node):
        """
        MethodDeclaration 객체를 전체적으로 문자열로 변환합니다.
        """
        # 메소드 이름과 매개변수를 포함한 서명
        params = ', '.join([f"{param.type.name} {param.name}" for param in method_node.parameters])
        method_signature = f"Method: {method_node.name}({params})"

        # 메소드의 본문을 문자열로 변환
        method_body = self._node_to_string(method_node.body)

        return f"{method_signature}\nBody:\n{method_body}"


    def _node_to_string(self, nodes):
        """
        노드의 리스트를 재귀적으로 문자열로 변환합니다.
        """
        if nodes is None:
            return "None"

        result = []
        for node in nodes:
            if isinstance(node, javalang.tree.Statement):
                result.append(str(node))
            elif isinstance(node, javalang.tree.BlockStatement):
                result.append(self._node_to_string(node.statements))
            else:
                result.append(str(node))

        return '\n'.join(result)


    def _extract_method_source_code(self):
        start_line_str, end_line_str = self._get_position.split('-')


        # 파일 경로에 해당하는 소스 코드를 가져옵니다.
        if self._file_path not in self.source_codes:
            raise ValueError(f"파일 경로 '{self._file_path}'가 source_codes에 존재하지 않습니다.")

        source_code = self.source_codes[self._file_path]

        # 시작 줄과 끝 줄을 분리하여 정수로 변환합니다.
        start_line_str, end_line_str = self._get_position.split('-')
        start_line = int(start_line_str)
        end_line = int(end_line_str)

        # 소스 코드에서 해당 범위를 추출합니다.
        lines = source_code.splitlines()

        # 시작 줄과 끝 줄을 기준으로 코드 추출
        if start_line < 1 or end_line > len(lines):
            raise ValueError(f"잘못된 줄 번호 범위: 시작 줄 {start_line}, 끝 줄 {end_line}")

        extracted_lines = lines[start_line - 1:end_line]

        return '\n'.join(extracted_lines)


    def __track_variable_flow(self, class_method, var_name, count=0): #변수 흐름 추적. (계속 추가 가능)
        parts = class_method.split('.')

        class_name = parts[0]

        if parts[1] is None:
            parts[1] = " "

        method_name = parts[1]
        self.__flow.append(class_method) # 흐름 추가
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
        parts = class_method.split('.')
        class_name = parts[0]
        method_name = parts[1]

        if count>current_count:
            return

        if node.member in S.sink_functions.keys() and node.arguments:
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
                self.__flow.append(f".{method_name}.{node.member}")
                self.sink_check.append(node.member)
                # 새로운 키를 생성하고, 기존 키가 존재하면 새 키를 사용
                existing_key = (class_method, var_name)
                new_key = self.__numbering(self.flows, existing_key,node)
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

    # 로그 파일 설정
    logging.basicConfig(filename='error_log.txt', level=logging.ERROR,
                        format='- %(message)s',
                        encoding='utf-8')


    def __if_variable_assignment(self, node, class_method, var_name, count, current_count):
        try:
            if isinstance(node.value, javalang.tree.MethodInvocation):  # 2-2
                if node.value.arguments:
                    for arg_index, arg in enumerate(node.value.arguments):
                        if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name and (count < current_count):
                            # self.__flow.append([node.value.member,var_name])
                            self.__track_variable_flow(class_method, node.expressionl.member, current_count)  # 같은 메서드에서 추적

            if isinstance(node.value, javalang.tree.MethodInvocation) and (node.value.qualifier == var_name) and (count < current_count):
                # self.__flow.append([node.value.member,var_name])
                self.__track_variable_flow(class_method, node.expressionl.member, current_count)  # 같은 메서드에서 추적

            if isinstance(node.expressionl, javalang.tree.MemberReference) and node.value.member == var_name and (count < current_count):  # 1-1
                self.__track_variable_flow(class_method, node.expressionl.member, current_count)

            if isinstance(node.expressionl, javalang.tree.MemberReference) and node.expressionl.member == var_name and (count < current_count):  # 1-2
                # 초기화 값이 Source 함수일 경우 추가 필요
                if count < current_count:
                    return

        except Exception as e:
            error_message = f"오류 발생 in __if_variable_assignment: {str(e)}"
            logging.error(error_message)  # 오류 메시지를 파일에 기록
            pass  # 오류 발생 시 무시하고 계속 진행


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
                    #self.__flow.append([var_decl.initializer.member,var_name])
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