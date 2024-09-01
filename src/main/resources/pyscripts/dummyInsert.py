import re
import random


class InsertDummyCode:
    def __init__(self, java_code, dummy, rand):
        self.java_code = java_code
        self.dummy = dummy
        self.rand = rand
        self.obfuscated_code = self.__obfuscate()

    def __obfuscate(self):
        # 정규식을 사용해 메소드를 찾습니다.
        pattern = re.compile(r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\([^)]*\)\s*{')

        for match in pattern.finditer(self.java_code):
            method_start = match.start()
            method_declaration = match.group()

            # static 메소드인지 확인
            is_static = 'static' in method_declaration

            if not is_static:
                return self.__insert_dummy_code(self.java_code[method_start:])
            else:
                return None


    def __insert_dummy_code(self, method_body):
        pattern = re.compile(r'if\s*\((.*?)\)\s*{')

        obfuscated_code, count = pattern.subn(self.__replace_condition, self.java_code)

        # if 문을 찾지 못했을 경우의 처리
        if count == 0:
            return None
        else:
            obfuscated_code += self.dummy
            return obfuscated_code



    def __replace_condition(self, match):
        condition = match.group(1)
        obfuscated_condition = self.__obfuscate_condition(condition)
        dummy_condition = self.__generate_dummy_condition()
        return self.__obfuscate_condition_with_dummy_if(obfuscated_condition, dummy_condition)

    def __obfuscate_condition_with_dummy_if(self, condition, dummy_condition):
        # 의미 없는 중첩 if 문을 추가합니다.
        return f"""if ({condition}) {{
        if ({dummy_condition}) 
            unusedFunction{self.rand}();
        
"""

    def __obfuscate_condition(self, condition):
        # 기존 조건에 의미 없는 조건을 추가합니다.
        return f"(({condition}) && (1 == 1)) || (false && {condition})"

    def __generate_dummy_condition(self):
        # 간단한 더미 조건을 생성합니다.
        return f"{random.randint(1, 100)} == {random.randint(103, 300)}"

    def get_obfuscated_code(self):
        return self.obfuscated_code
