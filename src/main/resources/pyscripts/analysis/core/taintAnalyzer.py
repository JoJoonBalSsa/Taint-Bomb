import logging
from astParser import ASTParser
from variableExtractor import VariableExtractor
from flowTracker import FlowTracker
from methodAnalyzer import MethodAnalyzer


class TaintAnalysis:
    """Taint 분석을 조정하는 메인 클래스"""

    def __init__(self, java_folder_path):
        # 로그 설정 - 분석 대상 폴더에 로그 파일 생성
        import os
        log_file_path = os.path.join(java_folder_path, 'taint_analysis.log')
        logging.basicConfig(filename=log_file_path, level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        # Step 1: Parse all Java files
        self.parser = ASTParser()
        trees, self.source_codes = self.parser.parse_java_files(java_folder_path)

        # Step 2: Extract methods and find tainted variables
        self.extractor = VariableExtractor()
        self.__tainted_variables, self.__methods = self.extractor.extract_tainted_variables(trees)

        # Step 3: Track variable flows
        self.flow_tracker = FlowTracker(self.__methods, self.source_codes)
        self.flow_tracker.track_all_flows(self.__tainted_variables)

        # Step 4: Initialize method analyzer for detailed analysis
        self.method_analyzer = MethodAnalyzer(self.__methods, self.source_codes)

        # 호환성을 위해 기존 속성들을 유지
        self.flows = self.flow_tracker.flows
        self.method_check = self.extractor.method_check
        self.sink_check = self.flow_tracker.sink_check

    def _priority_flow(self):
        """민감도에 따른 우선순위 흐름 반환"""
        return self.flow_tracker.priority_flow()

    def _get_cut_tree(self, m_name):
        """메소드 이름으로 해당 메소드의 트리 정보를 반환"""
        return self.method_analyzer.get_cut_tree(m_name)

    def _extract_method_source_code(self):
        """메소드의 소스 코드를 추출"""
        return self.method_analyzer.extract_method_source_code()

    @property
    def _get_position(self):
        """현재 분석 중인 메소드의 위치 정보"""
        return getattr(self.method_analyzer, '_get_position', "")

    @property
    def _file_path(self):
        """현재 분석 중인 파일 경로"""
        return getattr(self.method_analyzer, '_file_path', "")