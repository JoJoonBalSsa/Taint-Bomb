import javalang

from obfuscateTool import obfuscateTool
from collections import defaultdict


class StringSearch:
    def __init__(self, java_folder_path): 
        self.class_names = []
        
        print("parsing strings...")
        trees = obfuscateTool.parse_java_files(java_folder_path)
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

                if isinstance(node, javalang.tree.ClassDeclaration): # 근데 클래스 밖에있는 문자열, 다른클래스에서 특정 클래스의 문자열을 불러온다면?
                    literal = self.__extract_strings(node, package_name)
                    literal.append(file_path)
                    literals.append(literal)

        path_to_literals = defaultdict(list)

        for literal in literals:
            path_to_literals[literal[3]].append(literal)
        unique_literals_by_path = [self.remove_duplicate_positions(literal_group[0]) for literal_group in path_to_literals.values() for literal_group in [literal_group]] #중복 문자열 제거

        return unique_literals_by_path


    def remove_duplicate_positions(self,literals):
        package, class_name, literals_list, path = literals
        seen_positions = set()
        unique_literals_list = []
        for value, pos in literals_list:
            if pos not in seen_positions:
                seen_positions.add(pos)
                unique_literals_list.append((value, pos))
        return [package, class_name, unique_literals_list, path]

    # 클래스 별로 문자열 추출
    def __extract_strings(self, node, package_name) :
        string_literals = []
        class_name = node.name
        self.class_names.append([package_name, class_name])

        for sub_path, sub_node in node:
            if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                if not any(pos == sub_node.position for _, pos in string_literals):
                    string_literals.append((sub_node.value, sub_node.position))
                
        Literal = [package_name, class_name, string_literals]
        return Literal
