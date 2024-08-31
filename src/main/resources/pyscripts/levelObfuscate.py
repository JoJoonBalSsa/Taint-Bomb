from operationExtract import ExtractOperations
from operationObfuscate import ObfuscateOperations
from applyObfuscated import ApplyObfuscated

import json


class LevelObfuscation:
    def __init__(self, output_folder):
        tainted_json = self.parse_json(output_folder + '/analysis_result_copy.json')

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
                continue
                # for tainted in item["tatinted"]:
                #     print("  File Path:", tainted["file_path"])
                #     print("  Method Name:", tainted["method_name"])
                #     print("  Tree Position:", tainted["tree_position"])
                #     print("  Source Code:", tainted["source_code"])
                #     print("  -" * 50)

            if item["sensitivity"] == 2:
                for tainted in item["tainted"]:
                    O = ObfuscateOperations(tainted)
                    obfuscated_code = O.return_obfuscated_code()
                    ApplyObfuscated(tainted["file_path"], tainted["source_code"], obfuscated_code)
