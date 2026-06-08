import re
import secrets
import string


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

            # static 메소드인지 확인. static 이면 더미 호출을 인스턴스 컨텍스트에
            # 넣을 수 없으므로 건너뛰고 "다음" 비-static 메서드를 찾는다.
            # (기존엔 첫 매치가 static 이면 곧장 None 을 반환해, 뒤에 비-static
            #  메서드가 있어도 더미 삽입이 조용히 무산됐다.)
            is_static = 'static' in method_declaration

            if not is_static:
                return self.__insert_dummy_code(self.java_code[method_start:])
            # static → 다음 매치로 계속
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
        # 불투명-거짓 술어로 가드된 dummy 호출.
        #
        # 기존 구현은 `new Random()` 을 썼는데, 대상 클래스가 java.util.Random 을
        # import 하지 않으면 컴파일이 깨졌다. 이제는 import 가 전혀 필요 없는
        # 정수 비트 연산 불투명 술어를 사용한다.
        #   ((v * v) & 3) == 3 은 임의 정수 제곱이 (mod 4) 0/1 이므로 항상 거짓.
        # 따라서 unusedFunction 호출은 절대 실행되지 않지만 컴파일은 유지된다.
        v = self.__rand_name()
        seed = secrets.randbelow(2_000_000_000) + 1
        return f"""
        int {v} = {seed};
        if ((({v} * {v}) & 3) == 3) {{
            unusedFunction{self.rand}();
        }}
"""

    @staticmethod
    def __rand_name(length=8):
        first = secrets.choice(string.ascii_lowercase)
        rest = "".join(secrets.choice(string.ascii_lowercase + string.digits)
                       for _ in range(length - 1))
        return first + rest


    def get_obfuscated_code(self):
        return self.obfuscated_code