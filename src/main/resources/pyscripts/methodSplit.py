import re
import secrets
import string


class MethodSplit:
    def __init__(self, method):
        self.method = method

        access_modifier, return_type, method_name, method_param, body, is_static = self.__extract_java_method_info(
            self.method)
        if is_static:
            self.new_method = None
            return
        else :
            new_func, new_func_name = self.__generate_java_function(body, return_type, method_param)
            modified_body = self.__replace_method_body(self.method, method_name, new_func_name, return_type, method_param)
            self.new_method = self.__add_new_method(modified_body, new_func)

    def get_new_method(self):
        return self.new_method

    def __extract_java_method_info(self, method_code):
        method_pattern = re.compile(r'\b(public|protected|private)\s+(static\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{')
        match = method_pattern.search(method_code)

        if match:
            access_modifier = match.group(1)
            is_static = bool(match.group(2))  # static 키워드가 있으면 True, 없으면 False

            return_type = match.group(3)
            method_name = match.group(4)
            parameters = match.group(5).strip()

            # 매개변수를 리스트로 변환
            param_list = [param.strip() for param in parameters.split(',')] if parameters else []

            start_index = match.end()
            body = ""
            brace_count = 1
            for i, char in enumerate(method_code[start_index:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        body = method_code[start_index:start_index + i].strip()
                        break

            return access_modifier, return_type, method_name, param_list, body, is_static

        else:
            return None  # 메소드 패턴이 일치하지 않을 경우

    def __extract_try_block_content(self, java_code):
        pattern = r'(public|private)\s+(\w+)\s+\w+\s*\([^)]*\)\s*\{.*?try\s*\{([\s\S]*?)\s*return\s+(.*?);'
        match = re.search(pattern, java_code, re.DOTALL)
        if match:
            return_type = match.group(2)
            content = match.group(3).strip()
            return_value = match.group(4).strip()
            return content, return_value, return_type
        return None, None, None

    def __has_try_in_body(self, method_body):
        return 'try' in method_body

    def __generate_random_string(self, length=8):
        if length < 1:
            return None
        letters = string.ascii_lowercase
        letters_and_digits = string.ascii_lowercase + string.digits
        first_char = secrets.choice(letters)
        rest_chars = "".join(secrets.choice(letters_and_digits) for _ in range(length - 1))
        return first_char + rest_chars

    def __generate_java_function(self, method_body, return_type, method_param):
        function_name = self.__generate_random_string()

        params = ""
        if method_param:
            for para in method_param:
                if params == "":
                    params += para
                else:
                    params += ', ' + para

        java_function_code = f"""
        public {return_type} {function_name}({params}) {{
            {method_body}
        }}
        """
        return java_function_code, function_name

    def __replace_method_body(self, java_content, method_name, function_name, return_type, method_param):
        method_pattern = re.compile(rf"(\b{return_type}\s+{method_name}\s*\([^)]*\)\s*{{)")
        match = method_pattern.search(java_content)
        start_index = match.end()

        open_braces = 1
        end_index = start_index
        while open_braces > 0 and end_index < len(java_content):
            if java_content[end_index] == '{':
                open_braces += 1
            elif java_content[end_index] == '}':
                open_braces -= 1
            end_index += 1

        if method_param != []:
            params = ""
            for para in method_param:
                para = para.split()[-1]

                if params == "":
                    params += para
                else:
                    params += ', ' + para

            if return_type == 'void' or return_type == '':
                modified_body = f"\n        {function_name}({params});\n"
            else:
                modified_body = f"\n        return {function_name}({params});\n"

        else:
            if return_type == 'void':
                modified_body = f"\n        {function_name}();\n"
            else:
                modified_body = f"\n        return {function_name}();\n"

        modified_content = (
                java_content[:start_index] + modified_body + java_content[end_index - 1:]
        )

        return modified_content

    def __add_new_method(self, java_method, new_func):
        #     if self.__has_try_in_body(new_func):
        #         try_content, return_value, return_type = self.__extract_try_block_content(new_func)
        #         if try_content and return_value and return_type:
        #             new_func_name = self.__generate_random_string()
        #
        #             new_try_func = f"""
        #     public {return_type} {new_func_name}({new_func.split('(')[1].split(')')[0]}) {{
        #         {try_content}
        #         return {return_value};
        #     }}
        # """
        #             modified_new_func = f"""
        #     public {new_func.split()[1]} {new_func.split()[2].split('(')[0]}({new_func.split('(')[1].split(')')[0]}) {{
        #         try {{
        #             return {new_func_name}({new_func.split('(')[1].split(')')[0].split()[-1]});
        #         }} catch (IllegalArgumentException e) {{
        #             return {return_value};
        #         }}
        #     }}
        # """
        #             new_method_content = f"\n{modified_new_func}\n{new_try_func}\n"
        #         else:
        #             new_method_content = f"\n{new_func}\n"
        #     else:
        #        new_method_content = f"\n{new_func}\n"

        new_method_content = f"\n{new_func}\n"

        return java_method + "\n" + new_method_content
