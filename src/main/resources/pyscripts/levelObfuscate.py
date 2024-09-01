from operationObfuscate import ObfuscateOperations
from applyObfuscated import ApplyObfuscated
from dumbDB import DumbDB
from dummyInsert import InsertDummyCode

import json


class LevelObfuscation:
    def __init__(self, output_folder):
        tainted_json = self.parse_json(output_folder + '/analysis_result.json')

        self.check_level(tainted_json)

    def parse_json(self, json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as file:
            ob_json = json.load(file)
        return ob_json

    def check_level(self, json):
        for item in json:
            print("sensitivity", item["sensitivity"])

            if item["sensitivity"] == 1:
                continue

            if item["sensitivity"] == 3:
                ddb = DumbDB()
                for tainted in item["tainted"]:
                    # 연산자 난독화
                    print("연산자")
                    O = ObfuscateOperations(tainted)
                    obfuscated_code = O.return_obfuscated_code()

                    # 더미 코드 추가
                    rand = ddb.get_unique_random_number()
                    if rand is not None:
                        print("더미코드")
                        dummy_code = ddb.get_dumb(rand)
                        idc = InsertDummyCode(obfuscated_code, dummy_code, rand)
                        if idc.get_obfuscated_code() is not None:
                            obfuscated_code = idc.get_obfuscated_code()

                    else:
                        continue

                    print(obfuscated_code)
                    ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)

            if item["sensitivity"] == 2:
                for tainted in item["tainted"]:
                    O = ObfuscateOperations(tainted)
                    obfuscated_code = O.return_obfuscated_code()
                    ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)
