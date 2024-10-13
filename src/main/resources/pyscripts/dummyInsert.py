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
                print()
                return self.__insert_dummy_code(self.java_code[method_start:])
            else:
                return None


    # def __insert_dummy_code(self, method_body):
    #
    #     # 자바 메서드의 본문 시작을 찾는 패턴: { 뒤에 공백 또는 줄바꿈이 가능
    #     pattern = re.compile(r'({\s*)')
    #
    #     # 자바 메서드에서 본문을 찾고 그 위치에 더미 코드를 삽입
    #     obfuscated_code, count = pattern.subn(r'\1' + self.__add_dummy_if() + '\n', method_body)
    #
    #     # 자바 본문을 찾지 못한 경우
    #     if count == 0:
    #         return None
    #     else:
    #         obfuscated_code += self.dummy
    #         print("dummy code inserted : ")
    #         print(obfuscated_code)
    #
    #         return obfuscated_code
    def __insert_dummy_code(self, method_body):
        # 자바 메서드의 시작 부분을 찾는 패턴: 메서드 선언부 끝에 있는 { 를 찾습니다.
        pattern = re.compile(r'(.*?{)(\s*)', re.DOTALL)

        # 메서드 선언부와 본문 시작 부분을 찾아 더미 코드를 삽입합니다.
        match = pattern.match(method_body)
        if match:
            method_start = match.group(1)
            whitespace = match.group(2)
            method_body_rest = method_body[match.end():]

            obfuscated_code = method_start + whitespace + self.__add_dummy_if() + '\n' + method_body_rest

            obfuscated_code += self.dummy
            print("dummy code inserted : ", obfuscated_code)
            return obfuscated_code
        else:
            return None



    def __add_dummy_if(self):
        # 의미 없는 중첩 if 문을 추가합니다.
        return f"""
        Random random = new Random();
        int randomValue = random.nextInt();
        int randomValue2 = random.nextInt(101) + 101;
        if (randomValue == randomValue2) 
            unusedFunction{self.rand}();
"""


    def get_obfuscated_code(self):
        return self.obfuscated_code
