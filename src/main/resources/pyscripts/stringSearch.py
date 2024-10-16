import javalang

from obfuscateTool import ObfuscateTool
from collections import defaultdict,namedtuple

Position = namedtuple("Position", ["line", "column"]) # Postion 정의

class StringSearch:
    def __init__(self, java_folder_path):
        self.class_names = []
        self.ban_list = []
        self.value_map = {}

        print("converting unicode...")
        ObfuscateTool.convert_unicode_literals(java_folder_path)
        print("parsing strings...")
        trees = ObfuscateTool.parse_java_files(java_folder_path)
        print("extracting strings...")
        self.Literals = self.__extract_string_literals(trees)  # [package,class,[Literals,,]] 이렇게 넣을 예정


    # trees 에서 각 tree 의 문자열들을 추출하고 Literals 에 package_class 와 함께 저장
    def __extract_string_literals(self, trees):
        literals = []
        package_name = None
        for file_path, tree, source_code in trees:
            for path, node in tree:
                if isinstance(node, javalang.tree.PackageDeclaration):
                    package_name = node.name

                if isinstance(node, javalang.tree.ClassDeclaration):
                    class_name = node.name
                    if 'public' in node.modifiers:
                        self.class_names.append([package_name, class_name]) # static 있는 클래스만 기록
                    literal = self.__extract_strings(node, package_name)
                    literal.append(file_path)
                    literals.append(literal)

        path_to_literals = defaultdict(list)

        for literal in literals:
            path_to_literals[literal[3]].append(literal)

        unique_literals_by_path = [self.remove_duplicate_positions(literal_group[0]) for literal_group in path_to_literals.values() for literal_group in [literal_group]]  # 중복 문자열 제거

        return unique_literals_by_path

    # Switch-case 구문에서 case에 있는 문자열 리터럴을 ban_list에 추가하는 함수
    def __check_and_remove_switch_case_literals(self, node):
        # SwitchStatement를 탐색하고 그 안의 각 SwitchStatementCase를 확인
        if isinstance(node, javalang.tree.SwitchStatement):
            for case in node.cases:
                if isinstance(case, javalang.tree.SwitchStatementCase):
                    for case_value in case.case:
                        if isinstance(case_value, javalang.tree.Literal) and isinstance(case_value.value, str):
                            # case 구문에서 문자열 리터럴을 발견한 경우 ban_list에 추가
                            if case_value.value.startswith('"') and case_value.value.endswith('"'):
                                self.ban_list.append(case_value.value)

    # 기존 문자열 추출 함수에 switch-case 처리 추가
    def __extract_strings(self, node, package_name):
        string_literals = []
        self.ban_list = []
        class_name = node.name
        is_next = False
        next = 0
        before_line = 0

        for sub_path, sub_node in node:
            self.__check_and_remove_annotation_literals(sub_node)
            self.__track_variable_declarations(sub_node)  # 변수 선언도 확인
            self.__check_and_remove_switch_case_literals(sub_node)  # switch-case 처리 추가

            if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                if not any(pos == sub_node.position for _, pos in string_literals):
                    pos = sub_node.position
                    if is_next and pos.line == before_line:
                        pos = Position(pos.line, pos.column + next)
                    string_literals.append((sub_node.value, pos))
                    is_next = False
                    next = 0
                    for char in sub_node.value:
                        if ord(char) > 127:  # 유니코드 처리
                            next += 5
                            before_line = pos.line
                            is_next = True

        # ban_list에 있는 문자열 제거
        string_literals = [(value, pos) for value, pos in string_literals if value not in self.ban_list]

        Literal = [package_name, class_name, string_literals]
        return Literal

    def remove_duplicate_positions(self, literals):
        package, class_name, literals_list, path = literals
        seen_positions = set()
        unique_literals_list = []
        for value, pos in literals_list:
            if pos not in seen_positions:
                seen_positions.add(pos)
                unique_literals_list.append((value, pos))
        return [package, class_name, unique_literals_list, path]

    def __check_and_remove_annotation_literals(self, node):

        if isinstance(node, javalang.tree.Annotation):

            if isinstance(node.element, javalang.tree.Literal):
                if node.element.value.startswith('"') and node.element.value.endswith('"'):
                    self.ban_list.append(node.element.value)

            elif isinstance(node.element, javalang.tree.ElementArrayValue):
                for element in node.element.values:
                    self.__process_annotation_element(element)

            elif isinstance(node.element, list):
                for element in node.element:
                    self.__process_annotation_element(element)

            elif isinstance(node.element, javalang.tree.ElementValuePair):
                self.__process_annotation_element(node.element)

    def __process_annotation_element(self, element):
        if isinstance(element, javalang.tree.ElementValuePair):
            value = element.value
            if isinstance(value, javalang.tree.ElementArrayValue):
                for literal in value.values:
                    if isinstance(literal, javalang.tree.Literal) and isinstance(literal.value, str):
                        if literal.value.startswith('"') and literal.value.endswith('"'):
                            self.ban_list.append(literal.value)

            elif isinstance(value, javalang.tree.Literal) and isinstance(value.value, str):
                if value.value.startswith('"') and value.value.endswith('"'):
                    self.ban_list.append(value.value)
            # 변수 할당 처리
            elif isinstance(value, javalang.tree.MemberReference):
                variable_name = value.member
                if variable_name in self.value_map and self.value_map[variable_name]:
                    self.ban_list.append(self.value_map[variable_name])
        elif isinstance(element, javalang.tree.Literal):
            if element.value.startswith('"') and element.value.endswith('"'):
                self.ban_list.append(element.value)

    def __track_variable_declarations(self, node):
        if isinstance(node, javalang.tree.VariableDeclarator) and isinstance(node.initializer, javalang.tree.Literal):
            if node.initializer.value.startswith('"') and node.initializer.value.endswith('"'):
                self.value_map[node.name] = node.initializer.value
