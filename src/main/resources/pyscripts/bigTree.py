import javalang
import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from keyObfuscate import KeyObfuscate


from obfuscateTool import obfuscateTool
from removeComments import RemoveComments

class BigTree:
    def __init__(self, folder_path) :
        self.trees = obfuscateTool.parse_java_files(folder_path)

        self.class_names = []
        self.Literals = []

        for file_path, tree, source_code in self.trees:
            self.lines = source_code.split('\n')
            for path, node in tree:
                if isinstance(node, javalang.tree.PackageDeclaration):
                    self.package_name = node.name
                    
                if isinstance(node, javalang.tree.ClassDeclaration):
                    self.class_name = node.name
                    for sub_path, sub_node in node:
                        if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                            Literal = self.extract_strings(self, node)
                            self.encrypt_strings(Literal)
                            random_classes = obfuscateTool.random_class(self.class_names, 2)

                    replaced_code = self.replace_strings(Literal)
                    obfuscateTool.overwrite_file(path, replaced_code)

                            

    def extract_strings(self, node) :
        string_literals = []
        self.class_names.append([self.package_name, self.class_name])

        for sub_path, sub_node in node:
            if isinstance(sub_node, javalang.tree.Literal) and isinstance(sub_node.value, str) and sub_node.value.startswith('"') and sub_node.value.endswith('"'):
                string_literals.append((sub_node.value, sub_node.position))
        Literal = [self.package_name, self.class_name, string_literals]
        return Literal
    

    def encrypt_strings(self, literals):
        for p, c, strings in literals:
            aes_key = os.urandom(16)
            enc_aes_key = os.urandom(8)

            ko = KeyObfuscate(aes_key, enc_aes_key)
            encrypted_aes_key = ko.enc_aes_key

            enc_aes_key = base64.b64encode(enc_aes_key).decode('utf-8').replace("=","")
            encrypted_aes_key = base64.b64encode(encrypted_aes_key).decode('utf-8').replace("=","")

            return ([p, c, encrypted_aes_key, enc_aes_key,[(self.__encrypt_string(literal, aes_key), _) for literal, _ in strings]])

    
    def __encrypt_string(self, plain_text, key):
        cipher = AES.new(key, AES.MODE_ECB)
        padded_text = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted_text = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted_text).decode('utf-8')
    

    def replace_strings(self, literals):
        for p, c, strings in literals:
                if p == self.package_name and c == self.class_name:
                    literals_sorted = sorted(literals, key=lambda x: (x[1][0], -x[1][1]))  # 라인 오른쪽부터 문자열 변환
                    for index, (literal, position) in enumerate(literals_sorted):
                        line_index = position[0] - 1
                        column_index = position[1] - 1
                        line = self.lines[line_index]
                        end_column_index = column_index + len(literal)
                        new_line = line[:column_index] + f'STRING_LITERALS[{index}]' + line[end_column_index:]
                        self.lines[line_index] = new_line
        code = '\n'.join(self.lines)

        return code