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

    def get_cut_tree(self, m_name):
        """메소드 이름으로 해당 메소드의 트리 정보를 반환"""
        for (class_name, method_name), method_nodes in self.methods.items():
            if method_name == m_name:
                for file_path, method_node in method_nodes:
                    for path, node in method_node:
                        if isinstance(node, javalang.tree.MethodDeclaration) and node.name == method_name:
                            self._current_node = node
                            self._file_path = file_path

                            # 시작 줄
                            start_line = node.position.line

                            # 끝 줄을 재귀적으로 계산합니다.
                            finder = MethodEndLineFinder(self.source_codes[file_path])
                            end_line = finder.find_method_end_line(start_line)

                            # Store start and end positions in a single variable
                            self._get_position = f"{start_line}-{end_line}"
                            # Return or use node_positions as needed
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
        start_line_str, end_line_str = self._get_position.split('-')

        # 파일 경로에 해당하는 소스 코드를 가져옵니다.
        if self._file_path not in self.source_codes:
            raise ValueError(f"파일 경로 '{self._file_path}'가 source_codes에 존재하지 않습니다.")

        source_code = self.source_codes[self._file_path]

        # 시작 줄과 끝 줄을 분리하여 정수로 변환합니다.
        start_line_str, end_line_str = self._get_position.split('-')
        start_line = int(start_line_str)
        end_line = int(end_line_str)

        # 소스 코드에서 해당 범위를 추출합니다.
        lines = source_code.splitlines()

        # 시작 줄과 끝 줄을 기준으로 코드 추출
        if start_line < 1 or end_line > len(lines):
            raise ValueError(f"잘못된 줄 번호 범위: 시작 줄 {start_line}, 끝 줄 {end_line}")

        extracted_lines = lines[start_line - 1:end_line]

        return ''.join(extracted_lines)