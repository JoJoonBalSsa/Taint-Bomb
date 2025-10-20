import javalang
import logging
import inspect
from collections import defaultdict
from sensitivityDB import SensitivityDB as S


class FlowTracker:
    """변수 흐름을 추적하는 클래스"""

    def __init__(self, methods, source_codes):
        self.methods = methods
        self.source_codes = source_codes
        self.flows = defaultdict(list)
        self.flow = []
        self.sink_check = []

    def track_all_flows(self, tainted_variables):
        """모든 taint된 변수의 흐름을 추적"""
        for class_method, var, count in tainted_variables:
            self.flow.clear()
            self._track_variable_flow(class_method, var, count)

    def _track_variable_flow(self, class_method, var_name, count=0):
        """변수 흐름 추적 (계속 추가 가능)"""
        MAX_RECURSION_DEPTH = 20  # 재귀 호출 최대 깊이 설정

        # 현재 재귀 깊이를 가져옴
        current_recursion_depth = len(inspect.stack())

        # 재귀 깊이가 MAX_RECURSION_DEPTH 이상이면 종료
        if current_recursion_depth >= MAX_RECURSION_DEPTH:
            return

        parts = class_method.split('.')
        class_name = parts[0]

        if parts[1] is None:
            parts[1] = " "

        method_name = parts[1]
        self.flow.append(class_method)  # 흐름 추가
        method_nodes = self.methods.get((class_name, method_name), [])  # 메서드 단위로 저장해둔 노드로 바로 접근 가능

        current_count = 0
        for file_path, method_node in method_nodes:
            for path, node in method_node:  # 노드 내부 탐색
                current_count += 1

                if current_count <= count:
                    continue

                # sink 탐색
                if isinstance(node, javalang.tree.MethodInvocation):
                    self._if_find_sink(node, class_method, var_name, count, current_count)

                # 변수 할당일 때
                if isinstance(node, javalang.tree.Assignment):
                    self._if_variable_assignment(node, class_method, var_name, count, current_count)

                # 지역변수 선언일 때
                elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                    self._if_local_variable_declaration(node, class_method, var_name, count, current_count)

                # 메서드 호출일 때
                elif isinstance(node, javalang.tree.MethodInvocation):
                    self._if_call_method(node, var_name, count, current_count)

                # for 문일 때
                elif isinstance(node, javalang.tree.ForStatement):
                    self._if_for_statement(node, class_method, var_name, count, current_count)

                # try 문일 때
                elif isinstance(node, javalang.tree.TryResource):
                    self._if_try(node, class_method, var_name, count, current_count)

                # 삼항연산자 일 때
                elif isinstance(node, javalang.tree.TernaryExpression):
                    self._if_ternary(node, class_method, var_name, count, current_count)

        if self.flow:
            self.flow.pop()

    def _if_find_sink(self, node, class_method, var_name, count, current_count):
        parts = class_method.split('.')
        class_name = parts[0]
        method_name = parts[1]

        if current_count <= count:
            return

        if node.member in S.sink_functions.keys() and node.arguments:
            flow_added = False

            for arg in node.arguments:
                # 인자가 하나일 때
                if isinstance(arg, javalang.tree.MemberReference):
                    if arg.member == var_name:
                        flow_added = True
                        break
                # 인자가 피연산자 중 하나일 때
                else:
                    flow_added = self._judge_binary_operation(arg, flow_added, var_name)
                    if flow_added == True:
                        break

            if flow_added:
                self.flow.append(f"{class_name}.{method_name}.{node.member}")
                log_message = f".{method_name}.{node.qualifier}.{node.member}"
                logging.info(log_message)
                self.sink_check.append(node.member)
                # 새로운 키를 생성하고, 기존 키가 존재하면 새 키를 사용
                existing_key = (class_method, var_name)
                new_key = self._numbering(self.flows, existing_key, node)
                if new_key not in self.flows:
                    self.flows[new_key] = []
                # flows에 flow 복사
                self.flows[new_key].append(self.flow[:])
                self.flow.pop()

    def _judge_binary_operation(self, arg, flow_added, var_name):
        try:
            if isinstance(arg, javalang.tree.BinaryOperation):
                try:
                    if isinstance(arg.operandl, javalang.tree.MemberReference):
                        if arg.operandl.member == var_name:
                            flow_added = True
                            return flow_added  # 하나의 인자만 확인하면 충분
                except Exception:
                    pass

                try:
                    if isinstance(arg.operandr, javalang.tree.MemberReference):
                        if arg.operandr.member == var_name:
                            flow_added = True
                            return flow_added  # 하나의 인자만 확인하면 충분
                except Exception:
                    pass

                try:
                    if isinstance(arg.operandl, javalang.tree.BinaryOperation):
                        flow_added = self._judge_binary_operation(arg.operandl, flow_added, var_name)
                        return flow_added
                except Exception:
                    pass

                try:
                    if isinstance(arg.operandr, javalang.tree.BinaryOperation):
                        flow_added = self._judge_binary_operation(arg.operandr, flow_added, var_name)
                        return flow_added
                except Exception:
                    pass

        except Exception:
            pass  # 전체적으로 발생할 수 있는 예외를 처리

    def _if_variable_assignment(self, node, class_method, var_name, count, current_count):
        try:
            # MethodInvocation 처리
            if isinstance(node.value, javalang.tree.MethodInvocation):  # 2-2
                if node.value.arguments:
                    for arg_index, arg in enumerate(node.value.arguments):
                        if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name and (count < current_count):
                            expression_member = getattr(node, 'expressionl', None)
                            if expression_member and hasattr(expression_member, 'member'):
                                self._track_variable_flow(class_method, expression_member.member, current_count)  # 같은 메서드에서 추적

            if isinstance(node.value, javalang.tree.MethodInvocation) and (getattr(node.value, 'qualifier', None) == var_name) and (count < current_count):
                self._track_variable_flow(class_method, getattr(node, 'expressionl', None).member, current_count)  # 같은 메서드에서 추적

            # MemberReference 처리
            if isinstance(node.expressionl, javalang.tree.MemberReference) and (getattr(node.value, 'member', None) == var_name) and (count < current_count):  # 1-1
                self._track_variable_flow(class_method, getattr(node, 'expressionl', None).member, current_count)

            if isinstance(node.expressionl, javalang.tree.MemberReference) and (getattr(node.expressionl, 'member', None) == var_name) and (count < current_count):  # 1-2
                if count < current_count:
                    return

        except AttributeError as e:
            print(f"AttributeError encountered: {e}")
            print(f"Offending node: {node}")
            print(f"Current method: {class_method}, variable: {var_name}")
        except Exception as e:
            # 다른 모든 예외 처리
            print(f"Exception encountered: {e}")
            print(f"Offending node: {node}")
            print(f"Current method: {class_method}, variable: {var_name}")

    def _if_local_variable_declaration(self, node, class_method, var_name, count, current_count):
        try:
            for var_decl in node.declarators:
                try:
                    if isinstance(var_decl.initializer, javalang.tree.MethodInvocation):  # 2-2
                        if var_decl.initializer.arguments:
                            for arg in var_decl.initializer.arguments:
                                if isinstance(arg, javalang.tree.MemberReference) and arg.member == var_name and count < current_count:
                                    self._track_variable_flow(class_method, var_decl.name, current_count)  # 같은 메서드에서 추적
                except Exception:  # MethodInvocation 내부 예외 처리
                    pass

                try:
                    if isinstance(var_decl.initializer, javalang.tree.MethodInvocation):
                        if var_decl.initializer.qualifier == var_name and count < current_count:  # 2-1
                            self._track_variable_flow(class_method, var_decl.name, current_count)  # 같은 메서드에서 추적
                except Exception:  # MethodInvocation 예외 처리
                    pass

                try:
                    if isinstance(var_decl.initializer, javalang.tree.MemberReference) and var_decl.initializer.member == var_name and count < current_count:  # 1-1
                        self._track_variable_flow(class_method, var_decl.name, current_count)
                except Exception:  # MemberReference 예외 처리
                    pass
        except Exception:  # node.declarators 처리에서 발생하는 예외를 전체적으로 잡음
            pass

    def _if_call_method(self, node, var_name, count, current_count):
        if node.arguments:
            for arg_index, arg in enumerate(node.arguments):
                if isinstance(arg, javalang.tree.MemberReference):
                    if arg.member == var_name and (count < current_count):  # 4-1
                        class_method_2, var_name_2 = self._call2method(node, arg_index)
                        var_name_2 = var_name if var_name_2 == None else var_name_2  # 소스코드에 없는 메서드 호출시 var_name_2 가 None 이 되는경우 방지
                        self._track_variable_flow(class_method_2, var_name_2)

                elif isinstance(arg, javalang.tree.BinaryOperation):
                    self._process_binary_operation(arg, node, var_name, count, current_count)

    def _process_binary_operation(self, binary_op, node, var_name, count, current_count):
        # 재귀적으로 BinaryOperation을 탐색하여 모든 오퍼랜드를 처리
        if isinstance(binary_op.operandl, javalang.tree.BinaryOperation):
            self._process_binary_operation(binary_op.operandl, node, var_name, count, current_count)
        elif isinstance(binary_op.operandl, javalang.tree.MemberReference):
            if binary_op.operandl.member == var_name:
                self._track_variable_flow(f"{type(node).__name__}.{node.member}", binary_op.operandl.member)

        if isinstance(binary_op.operandr, javalang.tree.BinaryOperation):
            self._process_binary_operation(binary_op.operandr, node, var_name, count, current_count)

        elif isinstance(binary_op.operandr, javalang.tree.MemberReference):
            if binary_op.operandr.member == var_name:
                self._track_variable_flow(f"{type(node).__name__}.{node.member}", binary_op.operandr.member)

    def _call2method(self, node, arg_index):
        invoked_method = node.member
        for target_class_method, target_method_nodes in self.methods.items():
            target_class_name, target_method_name = target_class_method
            if target_method_name == invoked_method:  # 문제: 메서드 이름은 같은데 클래스가 다르다면?
                for target_file_path, target_method_node in target_method_nodes:
                    if len(target_method_node.parameters) > arg_index:
                        new_var_name = target_method_node.parameters[arg_index].name
                        return f"{target_class_name}.{invoked_method}", new_var_name
        return "UnknownClass." + invoked_method, None  # 만약 소스코드에 정의되지 않은 함수라면

    def _if_for_statement(self, node, class_method, var_name, count, current_count):
        if isinstance(node.control, javalang.tree.EnhancedForControl):
            EFC = node.control
            if EFC.iterable.member == var_name:
                for var_decl in EFC.var.declarators:
                    if isinstance(var_decl, javalang.tree.VariableDeclarator) and (count < current_count):
                        var_name_2 = var_decl.name
                        self._track_variable_flow(class_method, var_name_2, current_count)  # for 문 끝날때 까지만 추적하도록 수정 필요

    def _if_try(self, node, class_method, var_name, count, current_count):
        try:
            if isinstance(node.value, javalang.tree.ClassCreator):
                for arg in node.value.arguments:
                    if isinstance(arg, javalang.tree.ClassCreator):
                        for inner_arg in arg.arguments:
                            if isinstance(inner_arg, javalang.tree.MethodInvocation):
                                if inner_arg.member == var_name and count < current_count:
                                    self._track_variable_flow(class_method, inner_arg.member, current_count)
        except Exception:
            pass  # node.value가 없을 때 예외 처리

    def _if_ternary(self, node, class_method, var_name, count, current_count):
        try:
            # TernaryExpression에서 직접 condition, if_true, if_false에 접근
            condition = node.condition
            true_expr = node.if_true
            false_expr = node.if_false

            # 조건, 참/거짓 식에서 taint 여부를 추적
            try:
                if isinstance(condition, javalang.tree.MemberReference) and condition.member == var_name:
                    self._track_variable_flow(class_method, condition.member, current_count)
            except Exception:
                pass

            try:
                if isinstance(true_expr, javalang.tree.MemberReference) and true_expr.member == var_name:
                    self._track_variable_flow(class_method, true_expr.member, current_count)
            except Exception:
                pass

            try:
                if isinstance(false_expr, javalang.tree.MemberReference) and false_expr.member == var_name:
                    self._track_variable_flow(class_method, false_expr.member, current_count)
            except Exception:
                pass

        except Exception:
            pass

    def _numbering(self, d, key_tuple, node):
        if key_tuple in d:
            base_key1, base_key2 = key_tuple
            i = 1
            new_key = (base_key1, f"{base_key2}_{i}")
            while new_key in d:
                i += 1
                new_key = (base_key1, f"{base_key2}_{i}")
            return new_key
        else:
            return key_tuple

    def priority_flow(self):
        """민감도에 따른 우선순위 흐름 계산"""
        prioritized_flows = []

        for (class_method, var), value in self.flows.items():
            for flow in self.flows[(class_method, var)]:
                # 흐름에서 첫 번째 항목 (source)와 마지막 항목 (sink)을 가져옴
                source_full = flow[0]  # 첫 번째 항목의 첫 번째 요소 추출
                sink_full = flow[-1]  # 마지막 항목의 첫 번째 요소 추출

                # 'a.b.c'에서 'c' 부분 추출
                source = source_full.split('.')[-1]
                sink = sink_full.split('.')[-1]

                # source와 sink의 민감도 값을 가져옴
                source_sensitivity = S.source_functions.get(source, 0)  # 기본값 0
                sink_sensitivity = S.sink_functions.get(sink, 0)        # 기본값 0

                # source와 sink 민감도 중 더 큰 값을 사용 (max)
                total_sensitivity = max(source_sensitivity, sink_sensitivity)

                # 민감도를 흐름 앞에 삽입
                prioritized_flow = [int(round(total_sensitivity))] + flow
                prioritized_flows.append(prioritized_flow)

        return prioritized_flows