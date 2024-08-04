import javalang

from obfuscateTool import obfuscateTool

class stringSearch:
    def __init__(self, java_folder_path): 
        self.class_names = []
        self.trees = obfuscateTool.parse_java_files(java_folder_path)
        self.Literals = self.__extract_string_literals(self.trees)  # [package,class,[Literals,,]] 이렇게 넣을 예정


    # trees 에서 각 tree 의 문자열들을 추출하고 Literals 에 package_class 와 함께 저장 
    def __extract_string_literals(self, trees):       
        Literals = []
        string_literals = []
        package_name = None
        class_name = None
        for file_path, tree, source_code in trees:
            for path, node in tree:
                if isinstance(node, javalang.tree.PackageDeclaration):
                    package_name = node.name
                    
                if isinstance(node, javalang.tree.ClassDeclaration): # 근데 클래스 밖에있는 문자열, 다른클래스에서 특정 클래스의 문자열을 불러온다면?
                    string_literals = []
                    class_name = node.name
                    self.class_names.append([package_name,class_name])
                    for sub_path,sub_node in node:
                        if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                            #literal = sub_node.value[1:-1]
                            string_literals.append((sub_node.value, sub_node.position))
                    Literals.append([package_name,class_name,string_literals]) # 클래스 별로 문자열 추출
        return Literals