import javalang
import logging
from collections import defaultdict
from sensitivityDB import SensitivityDB as S


MAX_RECURSION_DEPTH = 20

# 우리가 실제로 추적에 관심을 두는 javalang 노드 타입. 사전에 필터링해
# 메서드 본문을 매번 다시 재귀 순회할 필요가 없도록 한다.
_RELEVANT_TYPES = (
    javalang.tree.MethodInvocation,
    javalang.tree.Assignment,
    javalang.tree.LocalVariableDeclaration,
    javalang.tree.ForStatement,
    javalang.tree.TryResource,
    javalang.tree.TernaryExpression,
)


def _extract_var_name(expr):
    """할당 LHS / 참조 노드에서 대상 변수명을 보수적으로 끌어낸다.

    MemberReference -> 변수명
    This.x         -> "this.x"   (cross-method 동일 클래스 추적용)
    이 외에는 None.
    """
    if expr is None:
        return None
    if isinstance(expr, javalang.tree.MemberReference):
        return expr.member
    if isinstance(expr, javalang.tree.This):
        # This.selectors[0] 이 MemberReference 인 케이스만 다룬다.
        selectors = getattr(expr, 'selectors', None) or ()
        for sel in selectors:
            if isinstance(sel, javalang.tree.MemberReference):
                return f"this.{sel.member}"
            break
    return None


def _arg_taints_var(arg, var_name):
    """인자(arg) 가 var_name 을 직간접적으로 사용하는지 판정.

    MemberReference 직접 참조, BinaryOperation (재귀), MethodInvocation 의 인자/qualifier
    까지 살펴본다. 깊이는 BinaryOperation 한정 재귀이므로 자연스럽게 제한된다.
    """
    if arg is None:
        return False

    if isinstance(arg, javalang.tree.MemberReference):
        return arg.member == var_name

    if isinstance(arg, javalang.tree.BinaryOperation):
        return _arg_taints_var(arg.operandl, var_name) or _arg_taints_var(arg.operandr, var_name)

    if isinstance(arg, javalang.tree.MethodInvocation):
        if getattr(arg, 'qualifier', None) == var_name:
            return True
        for inner in (arg.arguments or ()):
            if _arg_taints_var(inner, var_name):
                return True
        return False

    if isinstance(arg, javalang.tree.Cast):
        return _arg_taints_var(getattr(arg, 'expression', None), var_name)

    # ClassCreator: 생성자 인자 중 하나라도 var_name 을 사용하면 taint.
    # 예) new BufferedReader(new InputStreamReader(tainted)) — 중첩 생성자까지 재귀.
    if isinstance(arg, javalang.tree.ClassCreator):
        for inner in (arg.arguments or ()):
            if _arg_taints_var(inner, var_name):
                return True
        return False

    # TernaryExpression: 분기 중 하나라도 var_name 을 사용하면 taint.
    if isinstance(arg, javalang.tree.TernaryExpression):
        return (_arg_taints_var(getattr(arg, 'if_true', None), var_name)
                or _arg_taints_var(getattr(arg, 'if_false', None), var_name))

    return False


def _initializer_is_sanitized(rhs, var_name):
    """RHS 가 SANITIZER_FUNCTIONS 에 등록된 메서드 호출이고, 그 인자에 var_name 이
    들어 있으면 True. 이 경우 호출자는 taint 전파를 멈춰야 한다."""
    if not isinstance(rhs, javalang.tree.MethodInvocation):
        return False
    if rhs.member not in S.sanitizer_functions:
        return False
    for arg in (rhs.arguments or ()):
        if _arg_taints_var(arg, var_name):
            return True
    return False


class FlowTracker:
    """변수 흐름을 추적하는 클래스"""

    def __init__(self, methods, source_codes):
        self.methods = methods
        self.source_codes = source_codes
        self.flows = defaultdict(list)
        self.flow = []
        self.sink_check = []
        # priority_flow 캐시 (main.py 가 두 번 호출하므로 메모이즈)
        self._priority_flow_cache = None

        # 메서드 이름 -> [(class_name, file_path, method_node), ...] 인덱스.
        # _call2method 가 모든 메서드를 선형 탐색하던 것을 O(1) 사전 조회로 대체한다.
        self._methods_by_name = defaultdict(list)
        for (class_name, method_name), nodes in methods.items():
            for file_path, method_node in nodes:
                self._methods_by_name[method_name].append((class_name, file_path, method_node))

        # (class, method) -> [(path, node), ...]  — 관심 있는 노드 타입만 미리 평탄화해 둔다.
        # 동일 메서드를 여러 번 재진입해도 AST 전체를 다시 재귀 순회하지 않는다.
        self._nodes_cache = {}

        # 자주 쓰이는 source/sink dict 를 set 으로 캐싱
        self._source_keys = set(S.source_functions.keys())
        self._sink_keys = set(S.sink_functions.keys())

        # 한 번의 top-level 추적 세션 동안 같은 (class, method, var) 를 다시 들어가지 않도록.
        # _track_variable_flow 시작 시 set 이고, track_all_flows 가 매 변수마다 비운다.
        self._visited = set()

    def _flatten(self, class_name, method_name):
        """관심 노드 타입만 (visit_index, node) 쌍으로 캐싱.

        visit_index 는 VariableExtractor 의 count 와 동일한 의미 — 메서드 본문 전체를
        재귀 순회했을 때의 1-based 방문 순번. 이렇게 해 둬야 source 가 자기 자신보다
        이전에 나온 노드를 다시 sink 로 처리하지 않는다는 기존 의미가 그대로 유지된다.
        """
        key = (class_name, method_name)
        cached = self._nodes_cache.get(key)
        if cached is not None:
            return cached

        relevant = []
        for _file_path, method_node in self.methods.get(key, ()):
            visit_index = 0
            for _path, node in method_node:
                visit_index += 1
                if isinstance(node, _RELEVANT_TYPES):
                    relevant.append((visit_index, node))
        self._nodes_cache[key] = relevant
        return relevant

    def track_all_flows(self, tainted_variables):
        """모든 taint된 변수의 흐름을 추적"""
        for class_method, var, count in tainted_variables:
            self.flow.clear()
            self._visited.clear()
            self._track_variable_flow(class_method, var, count, depth=0)
        # 새 흐름이 추가되었을 수 있으므로 priority 캐시 무효화
        self._priority_flow_cache = None

    def _track_variable_flow(self, class_method, var_name, count=0, depth=0):
        """변수 흐름 추적. depth 는 호출자가 명시적으로 전달."""
        if depth >= MAX_RECURSION_DEPTH:
            return

        # class_method 는 "Class.method[.suffix...]" 형식. 한 번만 분리.
        dot = class_method.find('.')
        if dot == -1:
            class_name, method_name = class_method, ""
        else:
            class_name = class_method[:dot]
            rest = class_method[dot + 1:]
            second_dot = rest.find('.')
            method_name = rest if second_dot == -1 else rest[:second_dot]

        # 같은 (class, method, var) 조합을 같은 세션 내에서 다시 추적하지 않는다.
        # 순환 호출/상호 재귀에서의 폭발을 막는 핵심 가드.
        visit_key = (class_name, method_name, var_name)
        if visit_key in self._visited:
            return
        self._visited.add(visit_key)

        self.flow.append(class_method)

        # 자주 쓰이는 노드 타입을 지역 변수로 캐싱
        MI = javalang.tree.MethodInvocation
        AS = javalang.tree.Assignment
        LV = javalang.tree.LocalVariableDeclaration
        FS = javalang.tree.ForStatement
        TR = javalang.tree.TryResource
        TE = javalang.tree.TernaryExpression

        for current_count, node in self._flatten(class_name, method_name):
            if current_count <= count:
                continue

            node_type = type(node)

            if node_type is MI:
                self._if_find_sink(node, class_method, class_name, method_name, var_name)
                self._if_call_method(node, var_name, count, current_count, depth)
            elif node_type is AS:
                self._if_variable_assignment(node, class_method, var_name, count, current_count, depth)
            elif node_type is LV:
                self._if_local_variable_declaration(node, class_method, var_name, count, current_count, depth)
            elif node_type is FS:
                self._if_for_statement(node, class_method, var_name, count, current_count, depth)
            elif node_type is TR:
                self._if_try(node, class_method, var_name, count, current_count, depth)
            elif node_type is TE:
                self._if_ternary(node, class_method, var_name, count, current_count, depth)

        if self.flow:
            self.flow.pop()

    def _if_find_sink(self, node, class_method, class_name, method_name, var_name):
        if not node.arguments or node.member not in self._sink_keys:
            return

        for arg in node.arguments:
            if _arg_taints_var(arg, var_name):
                break
        else:
            return

        self.flow.append(f"{class_name}.{method_name}.{node.member}")
        logging.info(f".{method_name}.{getattr(node, 'qualifier', None)}.{node.member}")
        self.sink_check.append(node.member)
        existing_key = (class_method, var_name)
        new_key = self._numbering(self.flows, existing_key, node)
        self.flows[new_key].append(self.flow[:])
        self.flow.pop()

    def _if_variable_assignment(self, node, class_method, var_name, count, current_count, depth):
        if count >= current_count:
            return

        value = getattr(node, 'value', None)
        lhs = getattr(node, 'expressionl', None)
        lhs_name = _extract_var_name(lhs)

        # 1) RHS 가 sanitizer 호출이라면 더 이상 전파하지 않는다.
        if _initializer_is_sanitized(value, var_name):
            return

        # 2) RHS 가 MethodInvocation 이고 인자 / qualifier 가 var_name 을 사용 →
        #    LHS 가 taint 된다.
        if isinstance(value, javalang.tree.MethodInvocation):
            propagate = False
            if getattr(value, 'qualifier', None) == var_name:
                propagate = True
            else:
                for arg in (value.arguments or ()):
                    if _arg_taints_var(arg, var_name):
                        propagate = True
                        break
            if propagate and lhs_name:
                self._track_variable_flow(class_method, lhs_name, current_count, depth + 1)
                return

        # 3) RHS 가 MemberReference == var_name → LHS taint
        if isinstance(value, javalang.tree.MemberReference) and value.member == var_name and lhs_name:
            self._track_variable_flow(class_method, lhs_name, current_count, depth + 1)
            return

        # 4) RHS 가 BinaryOperation 인데 어느 한 쪽이 var_name 을 사용한다면 LHS taint
        if isinstance(value, javalang.tree.BinaryOperation) and _arg_taints_var(value, var_name) and lhs_name:
            self._track_variable_flow(class_method, lhs_name, current_count, depth + 1)
            return

    def _if_local_variable_declaration(self, node, class_method, var_name, count, current_count, depth):
        if count >= current_count:
            return

        for var_decl in (node.declarators or ()):
            init = getattr(var_decl, 'initializer', None)
            if init is None:
                continue

            # sanitizer 가 감싸면 전파 차단
            if _initializer_is_sanitized(init, var_name):
                continue

            propagate = False

            if isinstance(init, javalang.tree.MethodInvocation):
                if getattr(init, 'qualifier', None) == var_name:
                    propagate = True
                else:
                    for arg in (init.arguments or ()):
                        if _arg_taints_var(arg, var_name):
                            propagate = True
                            break
            elif isinstance(init, javalang.tree.MemberReference) and init.member == var_name:
                propagate = True
            elif isinstance(init, javalang.tree.BinaryOperation) and _arg_taints_var(init, var_name):
                propagate = True
            elif isinstance(init, javalang.tree.Cast) and _arg_taints_var(init, var_name):
                propagate = True

            if propagate:
                self._track_variable_flow(class_method, var_decl.name, current_count, depth + 1)

    def _if_call_method(self, node, var_name, count, current_count, depth):
        if not node.arguments or count >= current_count:
            return

        for arg_index, arg in enumerate(node.arguments):
            if isinstance(arg, javalang.tree.MemberReference):
                if arg.member == var_name:
                    class_method_2, var_name_2 = self._call2method(node, arg_index)
                    if var_name_2 is None:
                        var_name_2 = var_name
                    self._track_variable_flow(class_method_2, var_name_2, 0, depth + 1)

            elif isinstance(arg, javalang.tree.BinaryOperation):
                if _arg_taints_var(arg, var_name):
                    class_method_2, var_name_2 = self._call2method(node, arg_index)
                    if var_name_2 is None:
                        var_name_2 = var_name
                    self._track_variable_flow(class_method_2, var_name_2, 0, depth + 1)

    def _call2method(self, node, arg_index):
        invoked_method = node.member
        # _methods_by_name 인덱스로 O(1) 조회
        for target_class_name, _file_path, target_method_node in self._methods_by_name.get(invoked_method, ()):
            if len(target_method_node.parameters) > arg_index:
                return f"{target_class_name}.{invoked_method}", target_method_node.parameters[arg_index].name
        return "UnknownClass." + invoked_method, None

    def _if_for_statement(self, node, class_method, var_name, count, current_count, depth):
        if count >= current_count:
            return
        control = getattr(node, 'control', None)
        if not isinstance(control, javalang.tree.EnhancedForControl):
            return
        iterable = getattr(control, 'iterable', None)
        if not isinstance(iterable, javalang.tree.MemberReference) or iterable.member != var_name:
            return
        var_decls = getattr(getattr(control, 'var', None), 'declarators', None) or ()
        for var_decl in var_decls:
            if isinstance(var_decl, javalang.tree.VariableDeclarator):
                self._track_variable_flow(class_method, var_decl.name, current_count, depth + 1)

    def _if_try(self, node, class_method, var_name, count, current_count, depth):
        # try-with-resources 초기화식이 이미 taint 된 var_name 을 사용하면,
        # 리소스 변수(node.name)가 새로 taint 된다.
        #
        # 기존 구현은 `inner_arg.member == var_name` 으로 "메서드 이름"과 "변수 이름"을
        # 비교해 사실상 절대 매치되지 않았다(try-with-resources 추적이 죽어 있었음).
        # 이제 _arg_taints_var 로 초기화식 안에서 var_name 사용 여부를 보수적으로 판정한다.
        if count >= current_count:
            return
        value = getattr(node, 'value', None)
        if value is None:
            return
        resource_name = getattr(node, 'name', None)
        if not resource_name:
            return
        if _arg_taints_var(value, var_name):
            self._track_variable_flow(class_method, resource_name, current_count, depth + 1)

    def _if_ternary(self, node, class_method, var_name, count, current_count, depth):
        if count >= current_count:
            return
        for sub in (getattr(node, 'condition', None),
                    getattr(node, 'if_true', None),
                    getattr(node, 'if_false', None)):
            if isinstance(sub, javalang.tree.MemberReference) and sub.member == var_name:
                self._track_variable_flow(class_method, sub.member, current_count, depth + 1)
                return

    def _numbering(self, d, key_tuple, node):
        if key_tuple not in d:
            return key_tuple
        base_key1, base_key2 = key_tuple
        i = 1
        new_key = (base_key1, f"{base_key2}_{i}")
        while new_key in d:
            i += 1
            new_key = (base_key1, f"{base_key2}_{i}")
        return new_key

    def priority_flow(self):
        """민감도에 따른 우선순위 흐름 계산. 결과 캐싱."""
        if self._priority_flow_cache is not None:
            return self._priority_flow_cache

        prioritized_flows = []
        src_funcs = S.source_functions
        sink_funcs = S.sink_functions

        for value in self.flows.values():
            for flow in value:
                source = flow[0].rsplit('.', 1)[-1]
                sink = flow[-1].rsplit('.', 1)[-1]
                total_sensitivity = max(src_funcs.get(source, 0), sink_funcs.get(sink, 0))
                prioritized_flows.append([int(round(total_sensitivity))] + flow)

        self._priority_flow_cache = prioritized_flows
        return prioritized_flows
