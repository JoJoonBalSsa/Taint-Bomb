import javalang
from methodFinder import MethodEndLineFinder


class MethodAnalyzer:
    """메소드 분석 관련 유틸리티 클래스"""

    def __init__(self, methods, source_codes):
        self.methods = methods
        self.source_codes = source_codes
        self._get_position = ""
        self._current_node = None
        self._file_path = ""
        # 파일별로 source_lines 분할과 MethodEndLineFinder 인스턴스를 캐싱.
        # get_cut_tree 가 메서드마다 source 를 다시 splitlines 하던 비용을 제거.
        self._finder_cache = {}
        # 메서드 이름 -> [(class, file_path, MethodDeclaration node), ...] 인덱스
        self._decls_by_name = self._build_decl_index(methods)

    @staticmethod
    def _build_decl_index(methods):
        index = {}
        for (class_name, method_name), method_nodes in methods.items():
            bucket = index.setdefault(method_name, [])
            for file_path, method_node in method_nodes:
                for _path, node in method_node:
                    if isinstance(node, javalang.tree.MethodDeclaration) and node.name == method_name:
                        bucket.append((class_name, file_path, node))
                        break
        return index

    def _get_finder(self, file_path):
        finder = self._finder_cache.get(file_path)
        if finder is None:
            finder = MethodEndLineFinder(self.source_codes[file_path])
            self._finder_cache[file_path] = finder
        return finder

    def get_cut_tree(self, m_name):
        """메소드 이름으로 해당 메소드의 트리 정보를 반환"""
        for class_name, file_path, node in self._decls_by_name.get(m_name, ()):
            self._current_node = node
            self._file_path = file_path
            start_line = node.position.line
            end_line = self._get_finder(file_path).find_method_end_line(start_line)
            self._get_position = f"{start_line}-{end_line}"
            return self._method_declaration_to_string(node)

    def _method_declaration_to_string(self, method_node):
        """MethodDeclaration 객체를 전체적으로 문자열로 변환"""
        # 메소드 이름과 매개변수를 포함한 서명
        params = ', '.join([f"{param.type.name} {param.name}" for param in method_node.parameters])
        method_signature = f"Method: {method_node.name}({params})"

        # 메소드의 본문을 문자열로 변환
        method_body = self._node_to_string(method_node.body)

        return f"{method_signature}\nBody:\n{method_body}"

    def _node_to_string(self, nodes):
        """노드의 리스트를 재귀적으로 문자열로 변환"""
        if nodes is None:
            return "None"

        result = []
        for node in nodes:
            if isinstance(node, javalang.tree.Statement):
                result.append(str(node))
            elif isinstance(node, javalang.tree.BlockStatement):
                result.append(self._node_to_string(node.statements))
            else:
                result.append(str(node))

        return '\n'.join(result)

    def extract_method_source_code(self):
        """메소드의 소스 코드를 추출"""
        if self._file_path not in self.source_codes:
            raise ValueError(f"파일 경로 '{self._file_path}'가 source_codes에 존재하지 않습니다.")

        start_str, end_str = self._get_position.split('-', 1)
        start_line = int(start_str)
        end_line = int(end_str)

        # MethodEndLineFinder 가 이미 split 한 결과를 재사용 (재분할 비용 제거)
        lines = self._get_finder(self._file_path).source_lines

        if start_line < 1 or end_line > len(lines):
            raise ValueError(f"잘못된 줄 번호 범위: 시작 줄 {start_line}, 끝 줄 {end_line}")

        # 원본의 ''.join 은 줄바꿈을 잃어 한 줄로 합쳐졌었음. '\n'.join 으로 보존.
        return '\n'.join(lines[start_line - 1:end_line])