import json


class AnalysisResultManager:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.results = {}

    def append(self, sensitivity, file_path, method_name, tree_position, cut_tree, source_code):
        sensitivity = int(sensitivity)
        new_entry = {
            "file_path": file_path,
            "method_name": method_name,
            "tree_position": tree_position,
            "cut_tree": cut_tree,
            "source_code": source_code
        }

        if sensitivity not in self.results:
            self.results[sensitivity] = {"sensitivity": sensitivity, "tainted": []}

        # 기존 항목 중 file_path와 tree_position이 같은 항목 찾기
        existing_entry = next((item for item in self.results[sensitivity]["tainted"]
                               if item["file_path"] == file_path and item["tree_position"] == tree_position), None)

        if existing_entry:
            # 기존 항목이 있으면 교체
            self.results[sensitivity]["tainted"].remove(existing_entry)

        # 새 항목 추가
        self.results[sensitivity]["tainted"].append(new_entry)

    def save_to_json(self):
        try:
            # sensitivity를 기준으로 내림차순 정렬
            sorted_results = sorted(self.results.values(), key=lambda x: x["sensitivity"], reverse=True)

            with open(self.json_file_path, 'w') as f:
                json.dump(sorted_results, f, indent=4)
        except IOError as e:
            print(f"파일 쓰기 오류: {e}")