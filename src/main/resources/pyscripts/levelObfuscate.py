from operationObfuscate import ObfuscateOperations
from applyObfuscated import ApplyObfuscated
from dumbDB import DumbDB
from dummyInsert import InsertDummyCode
from methodSplit import MethodSplit

import json


class LevelObfuscation:
    def __init__(self, output_folder, operator_obf="True", method_obf="True", dummy_obf="True"):
        tainted_json = self.parse_json(output_folder + '/analysis_result.json')
        if tainted_json is None:
            return

        # 문자열을 boolean으로 변환
        self.operator_obf = operator_obf.lower() == "true"
        self.method_obf = method_obf.lower() == "true"
        self.dummy_obf = dummy_obf.lower() == "true"

        self.check_level(tainted_json)

    def parse_json(self, json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                ob_json = json.load(file)
            return ob_json
        except FileNotFoundError:
            print("No analysis result found.")
            return None

    def check_level(self, json):
        for item in json:
            print("\nsensitivity", item["sensitivity"])

            if item["sensitivity"] == 1:
                continue

            if item["sensitivity"] == 3:
                self._process_level3_obfuscation(item)
            elif item["sensitivity"] == 2:
                self._process_level2_obfuscation(item)

    def _process_level3_obfuscation(self, item):
        """Level 3: 연산자 난독화, 메소드 분할, 더미 코드 삽입"""
        ddb = DumbDB() if self.dummy_obf else None

        for tainted in item["tainted"]:
            obfuscated_code = tainted["source_code"]

            # 연산자 난독화
            if self.operator_obf:
                print("operation obfuscation started...")
                obfuscated_code = self._apply_operator_obfuscation(obfuscated_code, tainted)

            # 메소드 분할
            if self.method_obf:
                print("function spliting...")
                obfuscated_code = self._apply_method_split(obfuscated_code)

            # 더미 코드 추가
            if self.dummy_obf:
                obfuscated_code = self._apply_dummy_code(obfuscated_code, ddb)

            # 난독화가 실제로 적용된 경우에만 파일 업데이트
            if obfuscated_code != tainted["source_code"]:
                ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)

    def _process_level2_obfuscation(self, item):
        """Level 2: 연산자 난독화만 수행"""
        if not self.operator_obf:
            return

        for tainted in item["tainted"]:
            print("operation obfuscation started...")
            obfuscated_code = self._apply_operator_obfuscation(
                tainted["source_code"],
                tainted
            )

            if obfuscated_code is not None:
                ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)

    def _apply_operator_obfuscation(self, source_code, tainted):
        """연산자 난독화 적용"""
        O = ObfuscateOperations(tainted)
        obfuscated_code = O.return_obfuscated_code()
        return obfuscated_code if obfuscated_code is not None else source_code

    def _apply_method_split(self, code):
        """메소드 분할 적용"""
        O = MethodSplit(code)
        temp_ob = O.get_new_method()
        return temp_ob if temp_ob is not None else code

    def _apply_dummy_code(self, code, ddb):
        """더미 코드 삽입 적용"""
        if ddb is None:
            return code

        rand = ddb.get_unique_random_number()
        if rand is None:
            return code

        print("dummy code insertion started...")
        dummy_code = ddb.get_dumb(rand)
        idc = InsertDummyCode(code, dummy_code, rand)
        temp_ob = idc.get_obfuscated_code()
        return temp_ob if temp_ob is not None else code


if __name__ == '__main__':
    import sys

    LevelObfuscation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])