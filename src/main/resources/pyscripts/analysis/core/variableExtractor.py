import javalang
from collections import defaultdict
from sensitivityDB import SensitivityDB as S


def _annotation_name(ann):
    """javalang 의 Annotation 노드에서 단순 이름을 얻는다.
    예) @org.springframework.web.bind.annotation.RequestParam -> 'RequestParam'.
    """
    name = getattr(ann, 'name', '') or ''
    return name.rsplit('.', 1)[-1]


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
            for _path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    current_class = node.name
                elif isinstance(node, (javalang.tree.MethodDeclaration,
                                       javalang.tree.ConstructorDeclaration)):
                    self._extract_methods(node, current_class, file_path)

        return self.tainted_variables, self.methods

    def _extract_methods(self, node, current_class, file_path):
        """메소드 단위로 AST 노드를 저장하고 taint 변수를 탐색"""
        method_name = node.name
        self.methods[(current_class, method_name)].append((file_path, node))

        # (A) Spring / JAX-RS 어노테이션이 붙은 파라미터는 그 자체가 source.
        # count=0 으로 등록해 메서드 본문 전체에서 추적 가능하게 한다.
        for param in getattr(node, 'parameters', []) or []:
            for ann in (getattr(param, 'annotations', None) or ()):
                if _annotation_name(ann) in S.parameter_source_annotations:
                    self.tainted_variables.append(
                        (f"{current_class}.{method_name}.PARAM", param.name, 0)
                    )
                    self.method_check.append(method_name)
                    break

        # (B) 본문에서 source 호출로 만들어지는 taint 변수 탐색
        count = 0
        for _sub_path, sub_node in node:
            count += 1
            self._extract_variables(sub_node, current_class, method_name, count)

    def _extract_variables(self, sub_node, current_class, method_name, count):
        """AST 노드에서 taint된 변수를 추출"""
        # 변수 선언 및 정의일 때
        if isinstance(sub_node, javalang.tree.VariableDeclarator):
            self._handle_var_declarator(sub_node, current_class, method_name, count)
            return

        # 변수 할당일 때
        if isinstance(sub_node, javalang.tree.Assignment):
            self._handle_assignment(sub_node, current_class, method_name, count)
            return

        # try-with-resources
        if isinstance(sub_node, javalang.tree.TryResource):
            self._handle_try_resource(sub_node, current_class, method_name, count)
            return

    def _handle_var_declarator(self, sub_node, current_class, method_name, count):
        init = getattr(sub_node, 'initializer', None)
        if init is None:
            return

        # source 함수가 직접 RHS 인 케이스
        if isinstance(init, javalang.tree.MethodInvocation):
            if init.member in S.source_functions:
                self.tainted_variables.append(
                    (f"{current_class}.{method_name}.{init.member}", sub_node.name, count)
                )
                self.method_check.append(method_name)
                return
            # 인자나 qualifier 에 source 가 중첩된 경우
            nested = self._find_nested_source(init)
            if nested:
                self.tainted_variables.append(
                    (f"{current_class}.{method_name}.{nested}", sub_node.name, count)
                )
                self.method_check.append(method_name)
                return

        # try-with-resources 비슷한 ClassCreator 패턴
        if isinstance(init, javalang.tree.ClassCreator):
            nested = self._find_nested_source_in_creator(init)
            if nested:
                self.tainted_variables.append(
                    (f"{current_class}.{method_name}.{nested}", sub_node.name, count)
                )
                self.method_check.append(method_name)

    def _handle_assignment(self, sub_node, current_class, method_name, count):
        value = getattr(sub_node, 'value', None)
        lhs = getattr(sub_node, 'expressionl', None)
        if value is None:
            return

        # 어떤 source 함수가 관여하는지 식별
        source_name = None
        if isinstance(value, javalang.tree.MethodInvocation):
            if value.member in S.source_functions:
                source_name = value.member
            else:
                source_name = self._find_nested_source(value)
        elif isinstance(value, javalang.tree.ClassCreator):
            source_name = self._find_nested_source_in_creator(value)

        if source_name is None:
            return

        for var_name in self._lhs_var_names(lhs):
            self.tainted_variables.append(
                (f"{current_class}.{method_name}.{source_name}", var_name, count)
            )
            self.method_check.append(method_name)

    def _handle_try_resource(self, sub_node, current_class, method_name, count):
        value = getattr(sub_node, 'value', None)
        if not isinstance(value, javalang.tree.ClassCreator):
            return
        nested = self._find_nested_source_in_creator(value)
        if nested:
            self.tainted_variables.append(
                (f"{current_class}.{method_name}.{nested}", sub_node.name, count)
            )
            self.method_check.append(method_name)

    @staticmethod
    def _lhs_var_names(lhs):
        """할당 LHS 에서 추적 대상 변수명을 모두 뽑는다.
        MemberReference -> 변수명
        This + selectors -> 'this.x'
        """
        if isinstance(lhs, javalang.tree.MemberReference):
            return [lhs.member]
        if isinstance(lhs, javalang.tree.This):
            for sel in (getattr(lhs, 'selectors', None) or ()):
                if isinstance(sel, javalang.tree.MemberReference):
                    return [f"this.{sel.member}"]
        return []

    @staticmethod
    def _find_nested_source(call):
        """MethodInvocation 의 인자 / qualifier 에 source 호출이 중첩됐는지 찾는다.

        단, 바깥 호출 자체가 sanitizer 면(예: escapeHtml(getParameter("x"))) 내부
        source 는 정화된 것으로 보고 taint 로 등록하지 않는다(거짓 양성 방지).
        """
        if not isinstance(call, javalang.tree.MethodInvocation):
            return None
        if call.member in S.sanitizer_functions:
            return None
        for arg in (call.arguments or ()):
            if isinstance(arg, javalang.tree.MethodInvocation) and arg.member in S.source_functions:
                return arg.member
        return None

    @staticmethod
    def _find_nested_source_in_creator(creator):
        """ClassCreator 의 인자에 ClassCreator / MethodInvocation 형태로 source 호출이
        중첩되어 있는 케이스 (e.g., new BufferedReader(new InputStreamReader(socket.getInputStream())))."""
        for arg in (creator.arguments or ()):
            if isinstance(arg, javalang.tree.MethodInvocation) and arg.member in S.source_functions:
                return arg.member
            if isinstance(arg, javalang.tree.ClassCreator):
                for inner_arg in (arg.arguments or ()):
                    if isinstance(inner_arg, javalang.tree.MethodInvocation) and inner_arg.member in S.source_functions:
                        return inner_arg.member
        return None
