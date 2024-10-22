import string
import secrets
import re

class MethodSplit:
    def __init__(self, method):
        self.method = method

        modified_method, functions = self.__dynamic_method_split(method)
        self.merged_code = self.__merge_methods_and_functions(modified_method, functions)
    
    def __extract_java_method_info(self, method_code):
        method_pattern = re.compile(r'(@\w+\s+)?(public|protected|private)?\s*(static\s+)?(\w+(\[\])?|List<\w+>|\w+)\s+(\w+)\s*\(([^)]*)\)\s*(throws\s+\w+)?\s*\{')
        match = method_pattern.search(method_code)

        if match:
            access_modifier = match.group(2) or "package-private"  # 접근 제한자가 없으면 패키지-프라이빗으로 처리
            is_static = bool(match.group(3))  # static 키워드가 있으면 True, 없으면 False
            return_type = match.group(4)
            method_name = match.group(6)
            
            # 매개변수 처리 (None이나 빈 문자열 처리)
            parameters = match.group(7)
            if parameters:
                parameters = parameters.strip()
            else:
                parameters = ""
    
            # throws 구문 처리
            throws_clause = match.group(8) 

            # 매개변수 리스트로 변환하고 변수와 자료형 추출
            param_list = []
            if parameters:
                for param in parameters.split(','):
                    param_type, param_name = param.strip().split()
                    param_list.append((param_type, param_name))

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
    
    def __dynamic_method_split(self, method_code):
        result = self.__extract_java_method_info(method_code)
        if not result:
            return None, None

        access_modifier, return_type, method_name, param_list, body, is_static = result

        # 새로운 함수들을 저장할 리스트
        extracted_functions = []
        modified_body = []
        
        # body를 ';'로 나누어 각 구문을 처리
        statements = body.split(';')
        var_pattern = re.compile(r'(\w+(?:\[\])?)\s+(\w+)\s*=')
        update_pattern = re.compile(r'(\w+)\s*=\s*(?![=!])(.+)')  # 변수 업데이트 패턴에서 == 또는 != 같은 비교 연산자 제외

        local_vars = {}  # 로컬 변수와 자료형 저장
        brace_count = 0  # 중괄호 카운트

        # 본문을 한 줄씩 처리하며 변수 선언 및 변수 업데이트를 함수로 분리
        for line in statements:
            line = line.strip()
            
            # 중괄호 처리 (블록 안쪽인 경우 처리하지 않음)
            if '{' in line:
                brace_count += 1
            if '}' in line:
                brace_count -= 1

            declare_match = var_pattern.search(line)  # 변수 선언
            update_match = update_pattern.search(line)  # 변수 업데이트

            if declare_match and brace_count == 0:  # 블록 밖에서만 처리
                # 변수 선언 처리
                var_type, var_name = declare_match.groups()
                expression = line.split('=')[1].strip(';').strip()

                # 선언된 로컬 변수와 자료형을 추적
                local_vars[var_name] = var_type

                # 표현식에서 사용된 변수를 추적 (파라미터로 넘길 변수들)
                used_vars = [var for var in local_vars if var in expression] + [pname for _, pname in param_list if pname in expression]

                # 중복된 매개변수를 제거
                used_vars = list(dict.fromkeys(used_vars))

                # 새로운 함수 이름 생성
                function_name = self.__generate_random_string()

                # 동적으로 추적한 변수의 자료형을 매개변수로 할당
                new_function = f"public {'static ' if is_static else ''}{var_type} {function_name}({', '.join([f'{local_vars[var]} {var}' for var in used_vars if var in local_vars] + [f'{ptype} {pname}' for ptype, pname in param_list if pname in used_vars])}) {{\n    {var_type} {var_name} = {expression};\n    return {var_name};\n}}\n"
                extracted_functions.append(new_function)

                # 기존 라인에서 변수 선언을 함수 호출로 변경 (자료형 포함)
                modified_line = f"{var_type} {var_name} = {function_name}({', '.join(used_vars)});"
                modified_body.append(modified_line)

            elif update_match:  # 블록 안에서도 변수 업데이트 처리
                # 변수 업데이트 처리
                var_name, expression = update_match.groups()

                # 표현식에서 사용된 변수를 추적 (파라미터로 넘길 변수들)
                used_vars = [var for var in local_vars if var in expression] + [pname for _, pname in param_list if pname in expression]
                used_vars.append(var_name)  # 업데이트 대상 변수도 포함

                # 중복된 매개변수를 제거
                used_vars = list(dict.fromkeys(used_vars))

                # 새로운 함수 이름 생성
                function_name = self.__generate_random_string()

                # 동적으로 추적한 변수의 자료형을 매개변수로 할당
                new_function = f"public {'static ' if is_static else ''}{local_vars[var_name]} {function_name}({', '.join([f'{local_vars[var]} {var}' for var in used_vars if var in local_vars] + [f'{ptype} {pname}' for ptype, pname in param_list if pname in used_vars])}) {{\n    {var_name} = {expression};\n    return {var_name};\n}}\n"
                extracted_functions.append(new_function)

                # 기존 라인에서 변수 업데이트를 함수 호출로 변경
                modified_line = f"{var_name} = {function_name}({', '.join(used_vars)});"
                modified_body.append(modified_line)

            else:
                # 기존의 세미콜론을 붙여주는 방식으로 처리
                modified_body.append(line + ';')

        # 기존 메서드에 수정된 본문 적용 (맨 마지막 중괄호는 지움)
        modified_method = f"public {'static ' if is_static else ''}{return_type} {method_name}({', '.join([f'{ptype} {pname}' for ptype, pname in param_list])}) {{\n    " + '\n    '.join(modified_body).rstrip(';')

        return modified_method, extracted_functions

    def __merge_methods_and_functions(self, modified_method, extracted_functions):
        try:
            # modified_method가 None인 경우 예외 발생
            if modified_method is None:
                raise ValueError("Modified method is None. The input method code might not match the expected Java method pattern.")
            
            # Modified Method 마지막 중괄호 제거
            if modified_method.endswith("}\n"):
                modified_method = modified_method[:-2]  # 마지막 중괄호 제거

            # Extracted Functions 추가
            merged_code = modified_method + '\n}\n\n' + '\n'.join(extracted_functions) + '\n'
            
            return merged_code

        except AttributeError as e:
            # AttributeError 발생 시 처리 (NoneType에서 .endswith() 호출하는 경우)
            print(f"An error occurred: {e}")
            return "// Error: Invalid method code."

        except ValueError as e:
            # ValueError 발생 시 처리 (None 값이 반환된 경우)
            print(f"An error occurred: {e}")
            return "// Error: Method pattern did not match the expected format."


    def __generate_random_string(self, length=8):
        if length < 1:
            return None
        letters = string.ascii_lowercase
        letters_and_digits = string.ascii_lowercase + string.digits
        first_char = secrets.choice(letters)
        rest_chars = "".join(secrets.choice(letters_and_digits) for _ in range(length - 1))
        return first_char + rest_chars

    def get_new_method(self):
        return self.merged_code