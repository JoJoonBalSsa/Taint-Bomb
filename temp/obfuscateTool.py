import random
import javalang
import os

class obfuscateTool :
    def random_class(class_list, random_count): 
            leng = len(class_list)
            random_indices = [random.randint(0, leng - 1) for _ in range(random_count)]
            random_class = [class_list[i] for i in random_indices]
            
            return random_class


    def overwrite_file(path, cleaned_code):
        with open(path, 'w', encoding='utf-8') as file:
                file.write(cleaned_code)


    def parse_java_files(folder_path):
        java_files = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.java'):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        source_code = file.read()

                    try:
                        tree = javalang.parse.parse(source_code)
                        java_files.append((file_path, tree, source_code))

                    except javalang.parser.JavaSyntaxError as e:
                        print(f"Syntax error in file {file_path}: {e}")
                    except Exception as e:
                        print(f"Error parsing file {file_path}: {e}")
        return java_files

