from operationObfuscate import ObfuscateOperations
from applyObfuscated import ApplyObfuscated
from dumbDB import DumbDB
from dummyInsert import InsertDummyCode
from methodSplit import MethodSplit
from opaquePredicate import OpaquePredicate
from stringSplit import StringArraySplit
from controlFlowFlatten import ControlFlowFlatten
from javaValidate import safe_transform

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

    # ------------------------------------------------------------------
    # 안전망: 각 변환은 직전의 유효한 코드 위에서 수행되고, 결과가 구문상 유효할
    # 때만 채택된다. 깨진 Java 를 만들면 그 단계는 통째로 버려지고 직전 코드가 유지된다.
    # 어떤 변환이 예외를 던져도 전체 난독화가 중단되지 않도록 보호한다.
    # ------------------------------------------------------------------
    @staticmethod
    def _safe(prev, transform_callable):
        try:
            candidate = transform_callable()
        except Exception as e:  # noqa: BLE001
            print(f"  transform skipped (raised): {e}")
            return prev
        return safe_transform(prev, candidate)

    def _process_level3_obfuscation(self, item):
        """Level 3 (높은 민감도): 가능한 모든 변환을 안전망으로 누적 적용.

        순서: 연산자 → 제어흐름 평탄화 → 메소드 분할 → 불투명 술어 → 문자열 분해 → 더미.
        각 단계는 검증을 통과해야만 반영된다.
        """
        ddb = DumbDB() if self.dummy_obf else None

        for tainted in item["tainted"]:
            original = tainted["source_code"]
            code = original

            if self.operator_obf:
                print("operation obfuscation...")
                code = self._safe(code, lambda c=code: self._operator(c, tainted))

            if self.method_obf:
                print("control-flow flattening...")
                code = self._safe(code, lambda c=code: ControlFlowFlatten(c).get_obfuscated_code())

                print("function splitting...")
                code = self._safe(code, lambda c=code: MethodSplit(c).get_new_method())

            print("opaque predicate insertion...")
            code = self._safe(code, lambda c=code: OpaquePredicate(c, count=2).get_obfuscated_code())

            print("string split encoding...")
            code = self._safe(code, lambda c=code: StringArraySplit(c).get_obfuscated_code())

            if self.dummy_obf:
                print("dummy code insertion...")
                code = self._safe(code, lambda c=code: self._dummy(c, ddb))

            if code != original:
                ApplyObfuscated(tainted["file_path"], original, code)

    def _process_level2_obfuscation(self, item):
        """Level 2 (중간 민감도): 가벼운 변환만 — 연산자 + 불투명 술어 + 문자열 분해."""
        for tainted in item["tainted"]:
            original = tainted["source_code"]
            code = original

            if self.operator_obf:
                print("operation obfuscation...")
                code = self._safe(code, lambda c=code: self._operator(c, tainted))

            print("opaque predicate insertion...")
            code = self._safe(code, lambda c=code: OpaquePredicate(c, count=1).get_obfuscated_code())

            print("string split encoding...")
            code = self._safe(code, lambda c=code: StringArraySplit(c).get_obfuscated_code())

            if code != original:
                ApplyObfuscated(tainted["file_path"], original, code)

    # ------------------------------------------------------------------
    # 개별 변환 래퍼 (현재 코드 위에서 동작하도록 source_code 를 교체해 전달)
    # ------------------------------------------------------------------
    @staticmethod
    def _operator(code, tainted):
        # ObfuscateOperations 는 tainted["source_code"] 를 읽으므로, 체이닝을 위해
        # 현재 단계의 코드로 교체한 사본을 넘긴다.
        t2 = dict(tainted)
        t2["source_code"] = code
        return ObfuscateOperations(t2).return_obfuscated_code()

    @staticmethod
    def _dummy(code, ddb):
        if ddb is None:
            return None
        rand = ddb.get_unique_random_number()
        if rand is None:
            return None
        dummy_code = ddb.get_dumb(rand)
        return InsertDummyCode(code, dummy_code, rand).get_obfuscated_code()


if __name__ == '__main__':
    import sys

    LevelObfuscation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
