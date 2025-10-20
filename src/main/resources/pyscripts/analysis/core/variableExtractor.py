import javalang
from collections import defaultdict
from sensitivityDB import SensitivityDB as S


class VariableExtractor:
    """Taint 변수를 추출하는 클래스"""

    def __init__(self):
        self.methods = defaultdict(list)
        self.tainted_variables = []
        self.method_check = []

    def extract_tainted_variables(self, trees):
        """AST에서 taint된 변수들을 추출"""
        for file_path, tree in trees:
            current_class = "UnknownClass"
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    current_class = node.name

                elif isinstance(node, javalang.tree.MethodDeclaration):
                    self._extract_methods(node, current_class, file_path)

                elif isinstance(node, javalang.tree.ConstructorDeclaration):
                    self._extract_methods(node, current_class, file_path)

        return self.tainted_variables, self.methods

    def _extract_methods(self, node, current_class, file_path):
        """메소드 단위로 AST 노드를 저장하고 taint 변수를 탐색"""
        method_name = node.name
        self.methods[(current_class, method_name)].append((file_path, node))

        count = 0
        for sub_path, sub_node in node:
            count += 1  # 각각의 taint 변수가 생겨난 지점 식별
            self._extract_variables(sub_node, current_class, method_name, count)

    def _extract_variables(self, sub_node, current_class, method_name, count):
        """AST 노드에서 taint된 변수를 추출"""
        try:
            # 변수 선언 및 정의일 때
            if isinstance(sub_node, javalang.tree.VariableDeclarator):
                if isinstance(sub_node.initializer, javalang.tree.MethodInvocation):
                    try:
                        if sub_node.initializer.member in S.source_functions.keys():
                            self.tainted_variables.append((f"{current_class}.{method_name}.{sub_node.initializer.member}", sub_node.name, count))
                            self.method_check.append(method_name)
                    except Exception:
                        pass

                elif isinstance(sub_node.initializer, javalang.tree.ClassCreator):
                    try:
                        for arg in sub_node.initializer.arguments:
                            if isinstance(arg, javalang.tree.ClassCreator):
                                for inner_arg in arg.arguments:
                                    if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                        if inner_arg.member in S.source_functions:
                                            self.tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", sub_node.name, count))
                                            self.method_check.append(method_name)
                    except Exception:
                        pass

            # 변수 할당일 때
            elif isinstance(sub_node, javalang.tree.Assignment):
                try:
                    if isinstance(sub_node.value, javalang.tree.MethodInvocation):
                        # 직접 MethodInvocation의 member가 source_functions에 있는지 확인
                        if sub_node.value.member in S.source_functions:
                            try:
                                # sub_node.expressionl이 MemberReference인지 확인
                                if isinstance(sub_node.expressionl, javalang.tree.MemberReference):
                                    self.tainted_variables.append((f"{current_class}.{method_name}.{sub_node.value.member}", sub_node.expressionl.member, count))

                                # sub_node.expressionl이 This 객체인 경우
                                elif isinstance(sub_node.expressionl, javalang.tree.This):
                                    for selector in sub_node.expressionl.selectors:
                                        if isinstance(selector, javalang.tree.MemberReference):
                                            self.tainted_variables.append((f"{current_class}.{method_name}.{sub_node.value.member}", selector.member, count))
                            except Exception:
                                pass

                        # MethodInvocation의 인자(arguments)에서 중첩된 MethodInvocation 확인
                        for inner_arg in sub_node.value.arguments:
                            try:
                                if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                    # 인자의 member가 source_functions에 있는지 확인
                                    if inner_arg.member in S.source_functions:
                                        if isinstance(sub_node.expressionl, javalang.tree.MemberReference):
                                            self.tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", sub_node.expressionl.member, count))
                                        elif isinstance(sub_node.expressionl, javalang.tree.This):
                                            for selector in sub_node.expressionl.selectors:
                                                if isinstance(selector, javalang.tree.MemberReference):
                                                    self.tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", selector.member, count))
                            except Exception:
                                pass
                except Exception:
                    pass

            # TRY문
            elif isinstance(sub_node, javalang.tree.TryResource):
                try:
                    if isinstance(sub_node.value, javalang.tree.ClassCreator):
                        for arg in sub_node.value.arguments:
                            if isinstance(arg, javalang.tree.ClassCreator):
                                for inner_arg in arg.arguments:
                                    if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                        if inner_arg.member in S.source_functions:
                                            self.tainted_variables.append((f"{current_class}.{method_name}.{inner_arg.member}", sub_node.name, count))
                except Exception:
                    pass
        except Exception:
            pass