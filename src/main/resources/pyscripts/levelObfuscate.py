from operationObfuscate import ObfuscateOperations
from applyObfuscated import ApplyObfuscated
from dumbDB import DumbDB
from dummyInsert import InsertDummyCode
from methodSplit import MethodSplit

import json


class LevelObfuscation:
    def __init__(self, output_folder):
        tainted_json = self.parse_json(output_folder + '/analysis_result.json')
        if tainted_json is None:
            return

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
                ddb = DumbDB()
                for tainted in item["tainted"]:
                    # 연산자 난독화
                    print("operation obfuscation started...")
                    O = ObfuscateOperations(tainted)
                    obfuscated_code = O.return_obfuscated_code()

                    print("function spliting... ", )
                    if obfuscated_code is None:
                        obfuscated_code = tainted["source_code"]

                    # 메소드 분할
                    O = MethodSplit(obfuscated_code)
                    temp_ob = O.get_new_method()

                    if temp_ob is not None:
                        obfuscated_code = temp_ob
                    # 더미 코드 추가
                    rand = ddb.get_unique_random_number()

                    if rand is not None:
                        if obfuscated_code is None:
                            obfuscated_code = tainted["source_code"]

                            print("dummy code insertion started...")
                            dummy_code = ddb.get_dumb(rand)
                            idc = InsertDummyCode(obfuscated_code, dummy_code, rand)
                            obfuscated_code = idc.get_obfuscated_code()

                        else:
                            print("dummy code insertion started...")
                            dummy_code = ddb.get_dumb(rand)
                            idc = InsertDummyCode(obfuscated_code, dummy_code, rand)
                            temp_ob = idc.get_obfuscated_code()
                            if temp_ob is not None:
                                obfuscated_code = temp_ob

                    else:
                        continue

                    if obfuscated_code is not None:
                        ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)

            if item["sensitivity"] == 2:
                for tainted in item["tainted"]:
                    #print(f"\n{tainted["method_name"]} level obfuscation")
                    print("operation obfuscation started...")
                    O = ObfuscateOperations(tainted)

                    obfuscated_code = O.return_obfuscated_code()

                    if obfuscated_code is not None:
                        ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)


if __name__ == '__main__':
    import sys

    LevelObfuscation(sys.argv[1])