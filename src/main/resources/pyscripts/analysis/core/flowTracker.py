import javalang
import logging
from collections import defaultdict
from sensitivityDB import SensitivityDB as S


MAX_RECURSION_DEPTH = 20


class FlowTracker:
    """변수 흐름을 추적하는 클래스"""

    def __init__(self, methods, source_codes):
        self.methods = methods
        self.source_codes = source_codes
        self.flows = defaultdict(list)
        self.flow = []
        self.sink_check = []
        self._recursion_depth = 0

        # 메서드 이름 -> [(class_name, file_path, method_node), ...] 인덱스.
        # _call2method 가 모든 메서드를 선형 탐색하던 것을 O(1) 사전 조회로 대체한다.
        self._methods_by_name = defaultdict(list)
        for (class_name, method_name), nodes in methods.items():
            for file_path, method_node in nodes:
                self._methods_by_name[method_name].append((class_name, file_path, method_node))

        # 자주 쓰이는 source/sink dict 를 set 으로 캐싱 (멤버십 검사를 빠르게)
        self._source_keys = set(S.source_functions.keys())
        self._sink_keys = set(S.sink_functions.keys())

    def track_all_flows(self, tainted_variables):
        """모든 taint된 변수의 흐름을 추적"""
        for class_method, var, count in tainted_variables:
            self.flow.clear()
            self._recursion_depth = 0
            self._track_variable_flow(class_method, var, count)

    def _track_variable_flow(self, class_method, var_name, count=0):
        """변수 흐름 추적 (계속 추가 가능)"""
        if self._recursion_depth >= MAX_RECURSION_DEPTH:
            return
        self._recursion_depth += 1
        try:
            self.__track_variable_flow_impl(class_method, var_name, count)
        finally:
            self._recursion_depth -= 1

    def __track_variable_flow_impl(self, class_method, var_name, count):
        # class_method 는 항상 "Class.method[.suffix...]" 형태이므로 한 번만 분리한다.
        dot = class_method.find('.')
        if dot == -1:
            class_name, method_name = class_method, ""
        else:
            class_name = class_method[:dot]
            rest = class_method[dot + 1:]
            second_dot = rest.find('.')
            method_name = rest if second_dot == -1 else rest[:second_dot]

        self.flow.append(class_method)
        method_nodes = self.methods.get((class_name, method_name), ())

        # 자주 쓰이는 노드 타입을 지역 변수로 캐싱하여 attribute lookup 비용을 줄임
        MI = javalang.tree.MethodInvocation
        AS = javalang.tree.Assignment
        LV = javalang.tree.LocalVariableDeclaration
        FS = javalang.tree.ForStatement
        TR = javalang.tree.TryResource
        TE = javalang.tree.TernaryExpression

        current_count = 0
        for _file_path, method_node in method_nodes:
            for _path, node in method_node:
                current_count += 1
                if current_count <= count:
                    continue

                node_type = type(node)

                # MethodInvocation 은 sink 탐색과 호출-연쇄 추적 양쪽 모두에 해당
                if node_type is MI:
                    self._if_find_sink(node, class_method, class_name, method_name, var_name)
                    self._if_call_method(node, var_name, count, current_count)
                elif node_type is AS:
                    self._if_variable_assignment(node, class_method, var_name, count, current_count)
                elif node_type is LV:
                    self._if_local_variable_declaration(node, class_method, var_name, count, current_count)
                elif node_type is FS:
                    self._if_for_statement(node, class_method, var_name, count, current_count)
                elif node_type is TR:
                    self._if_try(node, class_method, var_name, count, current_count)
                elif node_type is TE:
                    self._if_ternary(node, class_method, var_name, count, current_count)

        if self.flow:
            self.flow.pop()

    def _if_find_sink(self, node, class_method, class_name, method_name, var_name):
        # node 는 호출자에서 이미 MethodInvocation 으로 확정.
        # current_count > count 도 호출자에서 필터링됨.
        if not node.arguments or node.member not in self._sink_keys:
            return

        flow_added = False
        for arg in node.arguments:
            if isinstance(arg, javalang.tree.MemberReference):
                if arg.member == var_name:
                    flow_added = True
                    break
            elif self._judge_binary_operation(arg, False, var_name):
                flow_added = True
                break

        if not flow_added:
            return

        self.flow.append(f"{class_name}.{method_name}.{node.member}")
        logging.info(f".{method_name}.{node.qualifier}.{node.member}")
        self.sink_check.append(node.member)
        existing_key = (class_method, var_name)
        new_key = self._numbering(self.flows, existing_key, node)
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
        # _methods_by_name 인덱스로 O(1) 조회 (이전: 모든 (class, method) 선형 탐색)
        for target_class_name, _file_path, target_method_node in self._methods_by_name.get(invoked_method, ()):
            if len(target_method_node.parameters) > arg_index:
                return f"{target_class_name}.{invoked_method}", target_method_node.parameters[arg_index].name
        return "UnknownClass." + invoked_method, None

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
        src_funcs = S.source_functions
        sink_funcs = S.sink_functions

        for value in self.flows.values():
            for flow in value:
                source = flow[0].rsplit('.', 1)[-1]
                sink = flow[-1].rsplit('.', 1)[-1]
                total_sensitivity = max(src_funcs.get(source, 0), sink_funcs.get(sink, 0))
                prioritized_flows.append([int(round(total_sensitivity))] + flow)

        return prioritized_flows