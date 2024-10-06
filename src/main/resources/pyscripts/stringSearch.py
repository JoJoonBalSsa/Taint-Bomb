import javalang

from obfuscateTool import ObfuscateTool
from collections import defaultdict


class StringSearch:
    def __init__(self, java_folder_path):
        self.class_names = []
        self.ban_list = []
        self.value_map = {}

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
                    # 클래스 밖에 있는 문자열도 처리해야 함.
                    print(file_path)
                    literal = self.__extract_strings(node, package_name)
                    literal.append(file_path)
                    literals.append(literal)

        path_to_literals = defaultdict(list)

        for literal in literals:
            path_to_literals[literal[3]].append(literal)

        unique_literals_by_path = [self.remove_duplicate_positions(literal_group[0]) for literal_group in path_to_literals.values() for literal_group in [literal_group]]  # 중복 문자열 제거

        return unique_literals_by_path

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

            elif isinstance(node.element, list):
                for element in node.element:
                    self.__process_annotation_element(element)

            elif isinstance(node.element, javalang.tree.ElementValuePair):
                self.__process_annotation_element(node.element)

    def __process_annotation_element(self, element):
        if isinstance(element, javalang.tree.ElementValuePair):
            value = element.value
            if isinstance(value, javalang.tree.Literal) and isinstance(value.value, str):
                if value.value.startswith('"') and value.value.endswith('"'):
                    self.ban_list.append(value.value)
            # 변수 할당 처리
            elif isinstance(value, javalang.tree.MemberReference):
                variable_name = value.member
                if variable_name in self.value_map and self.value_map[variable_name]:
                    self.ban_list.append(self.value_map[variable_name])

    def __track_variable_declarations(self, node):
        if isinstance(node, javalang.tree.VariableDeclarator) and isinstance(node.initializer, javalang.tree.Literal):
            if node.initializer.value.startswith('"') and node.initializer.value.endswith('"'):
                self.value_map[node.name] = node.initializer.value

    # 클래스 별로 문자열 추출
    def __extract_strings(self, node, package_name):
        string_literals = []
        class_name = node.name
        self.class_names.append([package_name, class_name])
        self.ban_list = []

        for sub_path, sub_node in node:
            self.__check_and_remove_annotation_literals(sub_node)

            self.__track_variable_declarations(sub_node) # 동시에 변수선언도 확인

            if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                if not any(pos == sub_node.position for _, pos in string_literals):
                    string_literals.append((sub_node.value, sub_node.position))

        string_literals = [(value, pos) for value, pos in string_literals if value not in self.ban_list]

        Literal = [package_name, class_name, string_literals]
        return Literal
