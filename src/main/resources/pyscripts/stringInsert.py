import javalang

from obfuscateTool import ObfuscateTool
import re

class StringInsert:
    def __init__(self, Literals, enc_Literals, class_names, foler_path, keyDecryptJava, stringDecryptJava):
        self.Literals = Literals
        self.enc_Literals = enc_Literals
        self.classes = class_names
        self.foler_path = foler_path

        self.str_decrypt = self.classes[0]
        self.key_decrypt = self.classes[1]

        print("replacing strings...")
        self.__replace_strings()

        print("inserting strings...")
        self.__insert_string()

        print("inserting decrypt functions...")
        self.__insert_str_decrypt(stringDecryptJava) # 복호화 함수 넣기
        self.__insert_key_decrypt(keyDecryptJava)
        print("to : ", self.str_decrypt)
        print("to : ", self.key_decrypt)


    def __insert_key_decrypt(self, key_decryptor_code):
        java_files = ObfuscateTool.parse_java_files(self.foler_path) # insert 할때마다 position이 달라져서 여러번 하는중
        for path,tree,source_code in java_files:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.insert_key_decrypt(source_code, key_decryptor_code))


    def insert_key_decrypt(self, code, key_decryptor_code):
        tree = javalang.parse.parse(code)
        lines = code.split('\n')
        package_name = None

        for path, node in tree:

            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name

            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
                pos = node.position.line

                if (self.key_decrypt[0] is None or self.key_decrypt[0] == package_name) and self.key_decrypt[1] == class_name:
                    key_decryptor_code = key_decryptor_code.split('\n')
                    key_decryptor_code = [line for line in key_decryptor_code if not line.startswith('import')]
                    key_decryptor_code = '\n'.join(key_decryptor_code)


                    lines.insert(pos,key_decryptor_code)


                    import_statements = [
                        "import java.security.MessageDigest;",
                        "import java.security.NoSuchAlgorithmException;",
                        "import java.util.ArrayList;",
                        "import java.util.Arrays;",
                        "import java.util.Base64;",
                        "import java.util.List;"
                    ]

                    for import_statement in import_statements:
                        if import_statement not in lines:
                            lines.insert(1, import_statement)

        code = '\n'.join(lines)

        return code


    def __insert_str_decrypt(self, key_decryptor_code): # 복호화 함수 넣기
        java_files = ObfuscateTool.parse_java_files(self.foler_path) # insert 할때마다 position이 달라져서 여러번 하는중
        for path,tree,source_code in java_files:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.insert_str_decrypt(source_code, key_decryptor_code))


    def insert_str_decrypt(self, code, key_decryptor_code):
        tree = javalang.parse.parse(code)
        lines = code.split('\n')
        package_name = None
        pos = None
        for path, node in tree:

            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name

            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
                pos = node.position.line
                if (self.str_decrypt[0] is None or self.str_decrypt[0] == package_name) and self.str_decrypt[1] == class_name:

                    key_decryptor_code = key_decryptor_code.split('\n')
                    key_decryptor_code = [line for line in key_decryptor_code if not line.startswith('import')]
                    key_decryptor_code = '\n'.join(key_decryptor_code)


                    lines.insert(pos,key_decryptor_code)


                    import_statements = [
                        "import javax.crypto.Cipher;",
                        "import javax.crypto.SecretKey;",
                        "import javax.crypto.spec.SecretKeySpec;",
                        "import java.util.Base64;",
                        "import java.lang.reflect.Method;"
                    ]

                    for import_statement in import_statements:
                        if import_statement not in lines:
                            lines.insert(1, import_statement)


        code = '\n'.join(lines)
        return code


    def __replace_strings(self):
        java_files = ObfuscateTool.parse_java_files(self.foler_path)
        for path,tree,source_code in java_files:
            replaced_code = self.replace_string_literals(source_code,path)
            ObfuscateTool.overwrite_file(path, replaced_code)


    def replace_string_literals(self, code,file_path):
        tree = javalang.parse.parse(code)
        lines = code.split('\n')
        for path, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name
            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
                for p, c, literals,_ in self.Literals:
                    if  c == class_name and file_path == _:
                        literals_sorted = sorted(literals, key=lambda x: (x[1][0], -x[1][1]))  # 라인 오른쪽부터 문자열 변환
                        for index, (literal, position) in enumerate(literals_sorted):
                            line_index = position[0] - 1
                            column_index = position[1] - 1

                            line = lines[line_index]
                            l_len = 0
                            for char in literal:
                                if ord(char) > 127: #유니코드일 경우
                                    l_len+=6
                                else:
                                    l_len+=1

                            end_column_index = column_index + l_len
                            new_line = line[:column_index] + f'STRING_LITERALS[{index}]' + line[end_column_index:]
                            lines[line_index] = new_line
        code = '\n'.join(lines)

        return code


    # 여기서 반복문으로 소스코드 돌리면서 암호화 문자열 삽입
    def __insert_string(self):
        java_files = ObfuscateTool.parse_java_files(self.foler_path)
        for path, tree, source_code in java_files:
            inserted_code = self.insert_encrypted_string_array(source_code,path)
            ObfuscateTool.overwrite_file(path, inserted_code)


    def insert_encrypted_string_array(self, code,file_path):
        tree = javalang.parse.parse(code)
        package_name = None

        array_declaration = []

        classes_pos = []

        key_declaration = None
        key_declaration_list = []

        for path, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name
            if isinstance(node, javalang.tree.ClassDeclaration): # 근데 클래스 밖에있는 문자열, 다른클래스에서 특정 클래스의 문자열을 불러온다면?
                class_name = node.name
                for p,c,encrypted_aes_key,enc_aes_key,literals,_ in self.enc_Literals:
                    if  c == class_name and _ == file_path: # 클래스 별 암호화된 문자열 삽입
                        classes_pos.append(node.position[0])
                        literals_sorted = sorted(literals, key=lambda x: (x[1][0], -x[1][1]))  # 라인 오른쪽부터 문자열 변환

                        array_declaration.append(f'public static final String[] STRING_LITERALS = {{' + ','.join(f'"{literal}"' for literal,_ in literals_sorted) + '\n};\n')
                        key_declaration = f'private static final String ENC_ENCRYPTION_KEY = "{encrypted_aes_key}";\n'
                        key_declaration += f'private static final String ENCRYPTION_KEY = "{enc_aes_key}";\n'
                        key_declaration_list.append(key_declaration)


        lines = code.split('\n')
        classes_pos = sorted(classes_pos, key=lambda x: (x, -x))  # 아래 클래스부터 추가

        array_declaration = list(reversed(array_declaration)) if len(array_declaration) > 1 else array_declaration
        key_declaration_list = list(reversed(key_declaration_list))if len(key_declaration_list) > 1 else key_declaration_list

        key_decrypt_class = f"{self.key_decrypt[0]}.{self.key_decrypt[1]}" if self.key_decrypt[0] else f"{self.key_decrypt[1]}"
        str_decrypt_class = f"{self.str_decrypt[0]}.{self.str_decrypt[1]}" if self.str_decrypt[0] else f"{self.str_decrypt[1]}"

        decrypt_code = f"""        
             static{{try {{Class<?> decryptorClass1 = Class.forName("{key_decrypt_class}");
             Method decryptMethod1 = decryptorClass1.getMethod("keyDecrypt", String.class, String.class);
             Class<?> decryptorClass2 = Class.forName("{str_decrypt_class}");
             Method decryptMethod2 = decryptorClass2.getMethod("stringDecrypt", String.class, byte[].class);
             for (int i = 0; i < STRING_LITERALS.length; i++) 
            {{STRING_LITERALS[i] = (String) decryptMethod2.invoke(null, STRING_LITERALS[i], (byte[]) decryptMethod1.invoke(null,ENC_ENCRYPTION_KEY,ENCRYPTION_KEY)); 
             }}}} catch (Exception e) {{}}}}
         """

        for i,pos in enumerate(classes_pos):
            # print("pos : ", pos)
            # print("array_declaration : ", array_declaration[i])
            lines.insert(pos,array_declaration[i])
            lines.insert(pos+1,key_declaration_list[i])
            lines.insert(pos+2,decrypt_code)

        reflection = 'import java.lang.reflect.Method;'
        if reflection not in lines:
            lines.insert(1, reflection)

        code = '\n'.join(lines)

        return code