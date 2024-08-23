import json
import os

class analysisResultManager:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.results = []

    def append(self, sensitivity, file_path, method_name, tree_position, cut_tree, source_code):
        new_entry = {
            "sensitivity": sensitivity,
            "file_path": file_path,
            "method_name": method_name,
            "tree_position": tree_position,
            "cut_tree": cut_tree,
            "source_code": source_code
        }

        # 기존 항목 중 file_path와 tree_position이 같은 항목 찾기
        existing_entry = next((item for item in self.results
                               if item["file_path"] == file_path and item["tree_position"] == tree_position), None)

        if existing_entry:
            # 기존 항목이 있으면 sensitivity 비교
            if sensitivity > existing_entry["sensitivity"]:
                # 새 항목의 sensitivity가 더 높으면 기존 항목 교체
                self.results.remove(existing_entry)
                self.results.append(new_entry)
            # sensitivity가 같거나 낮으면 아무 것도 하지 않음 (기존 항목 유지)
        else:
            # 기존 항목이 없으면 새 항목 추가
            self.results.append(new_entry)

    def save_to_json(self):
        try:
            with open(self.json_file_path, 'w') as f:
                json.dump(self.results, f, indent=4)
        except IOError as e:
            print(f"파일 쓰기 오류: {e}")