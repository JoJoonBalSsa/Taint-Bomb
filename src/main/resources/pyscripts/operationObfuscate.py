import re

from operationExtract import ExtractOperations
from operationDB import OperationDB


class ObfuscateOperations:
    def __init__(self, tainted):
        # 연산자 우선순위 리스트 (우선순위 높은 것부터 나열)
        self.operator_priority = [
            r'\*\*',  # 거듭제곱 연산자 (Python 스타일)
            r'\*', r'/', r'%',  # 곱셈, 나눗셈, 나머지
            r'\+', r'-',  # 덧셈, 뺄셈
            r'<<', r'>>', r'>>>',  # 시프트 연산자
            r'<', r'<=', r'>', r'>=', r'instanceof',  # 비교 연산자
            r'==', r'!=',  # 동등 비교 연산자
            r'&',  # 비트 AND
            r'\^',  # 비트 XOR
            r'\|',  # 비트 OR
            r'&&',  # 논리 AND
            r'\|\|',  # 논리 OR
            r'\?', r'\:',  # 삼항 연산자
            r'=', r'\+=', r'-=', r'\*=', r'/=', r'%=', r'<<=', r'>>=', r'>>>=', r'&=', r'\^=', r'\|=',  # 대입 연산자
        ]

        self.file_path = tainted["file_path"]
        self.method_name = tainted["method_name"]
        self.tree_position = tainted["tree_position"]
        self.source_code = tainted["source_code"]

        O = OperationDB()
        self.op_json = O.op_db()

        self.obfuscated = None
        temp_result = ''

        self.obfuscation_map = {}  # 난독화된 부분을 임시 저장할 맵
        self.counter = 0  # 난독화 넘버링에 사용

        e = ExtractOperations(self.source_code)

        expressions = e.expressions

        if expressions is not None:
            for expression_list in expressions:
                if len(expression_list) > 0:
                    obfuscate_list = self.obfuscate_expression(expression_list)

                    # 변환된 표현식으로 소스 코드를 교체
                    self.obfuscated = self.replace_expression(self.source_code, expression_list, obfuscate_list)



    def return_obfuscated_code(self):
        return self.obfuscated

    def obfuscate_expression(self, expression_list):
        # 괄호 안의 내용을 먼저 처리
        result_list=[]
        for expression in expression_list:
            expression = self.apply_operator_priority(expression)
            # 임시 기호를 원래의 난독화된 표현으로 대체
            for key, value in sorted(self.obfuscation_map.items(), reverse=True):
                expression = expression.replace(key, f"{value}")  # 괄호를 추가하지 않고 원래 표현으로
            result_list.append(expression)

        return result_list


    def apply_operator_priority(self, expression):
        # 함수 호출과 일반 괄호를 구분하기 위한 패턴
        function_call_pattern = re.compile(r'\b[\w\.]+\s*\([^()]*\)')

        # 함수 호출의 괄호는 건드리지 않도록 미리 찾아둠
        def preserve_function_calls(match):
            inner = match.group(0)
            temp_key = f"__FUNC_CALL_{self.counter}__"
            self.obfuscation_map[temp_key] = inner  # 함수 호출 저장
            self.counter += 1
            return temp_key

        # 모든 함수 호출을 임시 키로 치환
        expression = function_call_pattern.sub(preserve_function_calls, expression)

        # 괄호 내부를 재귀적으로 처리 (단, 함수 호출은 제외)
        while '(' in expression:
            expression = re.sub(
                r'\(([^()]+)\)',
                lambda x: self.apply_operator_priority(x.group(1)),
                expression
            )

        # 연산자 우선순위에 따라 처리
        for operator_pattern in self.op_json.keys():
            # 단항 연산자까지 포함한 정규식
            pattern = re.compile(
                rf'(\([^()]+\)|\b-?\w+\b|-?\d+|[!~]\s*\([^()]+\)|[!~]\s*\b-?\w+\b|-?\d+)\s*'
                rf'({re.escape(operator_pattern)})\s*'
                rf'(\([^()]+\)|\b-?\w+\b|-?\d+|[!~]\s*\([^()]+\)|[!~]\s*\b-?\w+\b|-?\d+)'
            )

            expression = ''.join(expression)
            match = pattern.search(expression)
            while match:
                operand1 = match.group(1)
                operator = match.group(2)
                operand2 = match.group(3)

                # 디버깅용 출력
                print(f"Identified operator: {operator} between '{operand1}' and '{operand2}'")

                # 난독화된 표현으로 변경
                obfuscated = self.op_json[operator].format(a=operand1, b=operand2)
                temp_key = f"__OBFUSCATED_{self.counter}__"
                self.obfuscation_map[temp_key] = f"{obfuscated}"
                expression = (
                        expression[:match.start()]
                        + temp_key
                        + expression[match.end():]
                )
                self.counter += 1

                # 다음 연산자 처리
                match = pattern.search(expression)

        # 임시로 치환한 함수 호출을 원래대로 복원
        for key, value in self.obfuscation_map.items():
            if key.startswith("__FUNC_CALL_"):
                expression = expression.replace(key, value)

        return expression



    def replace_expression(self, source_code, original_list,obfuscate_list):
        result = source_code

        for original, obfuscated in zip(original_list, obfuscate_list):
            print("오리지널:",original)
            print("난독화: ",obfuscated)
            # 임시 변수 초기화
            temp_result = ""
            index = 0

            while index < len(result):
                # 원본 표현식 찾기
                found_index = result.find(original, index)
                if found_index == -1:
                    # 더 이상 찾을 수 없으면 남은 부분을 결과에 추가하고 종료
                    temp_result += result[index:]
                    break
                # 찾은 위치 이전까지의 코드를 임시 결과에 추가
                temp_result += result[index:found_index]
                # 원본 표현식을 난독화된 표현식으로 대체
                temp_result += obfuscated
                # 다음 검색 위치 갱신
                index = found_index + len(original)

            # 현재 단계의 난독화된 결과로 업데이트
            result = temp_result

        return result
