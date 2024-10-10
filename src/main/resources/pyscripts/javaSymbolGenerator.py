import javalang
from collections import defaultdict
import json
import javalang.tree

class PseudoReflection:
    def __init__(self):
        # 표준 라이브러리 클래스와 메서드 정보를 저장
        self.classes = {
            "java.lang.String": ["length", "charAt", "substring", "toLowerCase", "toUpperCase", "trim", "equals", "compareTo", "replace", "split", "concat", "matches", "contains", "startsWith", "endsWith"],
            "java.util.ArrayList": ["add", "remove", "get", "set", "size", "clear", "isEmpty", "contains", "indexOf", "toArray", "sort", "subList"],
            "java.util.HashMap": ["put", "get", "remove", "containsKey", "containsValue", "size", "clear", "isEmpty", "keySet", "values", "entrySet"],
            "java.util.List": ["add", "remove", "get", "set", "size", "clear", "isEmpty", "contains", "indexOf", "toArray"],
            "java.util.Map": ["put", "get", "remove", "containsKey", "containsValue", "size", "clear", "isEmpty", "keySet", "values", "entrySet"],
            "java.util.Set": ["add", "remove", "contains", "size", "clear", "isEmpty", "toArray"],
            "java.io.File": ["exists", "getName", "getPath", "isDirectory", "isFile", "length", "createNewFile", "delete", "list", "mkdir", "renameTo"],
            "java.io.FileInputStream": ["read", "close", "skip", "available", "mark", "reset"],
            "java.io.FileOutputStream": ["write", "close", "flush"],
            "java.util.Scanner": ["next", "nextLine", "nextInt", "nextDouble", "hasNext", "hasNextLine", "close"],
            "java.lang.Math": ["abs", "max", "min", "pow", "sqrt", "random", "round", "floor", "ceil"],
            "java.time.LocalDate": ["now", "of", "parse", "plusDays", "minusDays", "isAfter", "isBefore", "getYear", "getMonth", "getDayOfMonth"],
            "java.time.LocalTime": ["now", "of", "parse", "plusHours", "minusHours", "getHour", "getMinute", "getSecond"],
            "java.util.Arrays": ["sort", "binarySearch", "fill", "copyOf", "equals", "asList", "toString"],
            "java.util.Collections": ["sort", "reverse", "shuffle", "max", "min", "binarySearch", "frequency", "swap"],
            "java.util.concurrent.ConcurrentHashMap": ["put", "get", "remove", "putIfAbsent", "replace", "containsKey", "containsValue", "clear", "size"]
        }

        self.java_lang_methods = [
            "println", "print", "printf",
            "parseInt", "parseDouble", "parseLong", "parseFloat",
            "valueOf",
            "toString",
            "equals",
            "hashCode",
            "getClass",
            "clone",
            "compareTo",
            "wait", "notify", "notifyAll",
            "instanceof",
            "synchronized",
            "try", "catch", "finally", "throw", "throws",
            "getAnnotation"
        ]

    def is_standard_library_method(self, class_name, method_name):
        return (class_name in self.classes and method_name in self.classes[class_name]) or \
            (class_name == "java.lang" and method_name in self.java_lang_methods)

class JavaSymbolGenerator:
    def __init__(self):
        self.reset()

    def reset(self):
        # 다양한 심볼 정보를 저장할 딕셔너리들 초기화
        self.symbols = defaultdict(list)  # 모든 심볼 정보 저장
        self.imports = {}  # 임포트 정보 저장
        self.current_package = ""  # 현재 패키지 이름
        self.type_mapping = {}  # 타입 이름과 전체 경로 매핑
        self.method_signatures = {}  # 메서드 시그니처 저장
        self.field_types = {}  # 필드 타입 정보 저장
        self.local_var_types = {}  # 지역 변수 타입 정보 저장
        self.reflection = PseudoReflection()  # 표준 라이브러리 정보 관리
        self.current_class = None  # 현재 분석 중인 클래스를 추적하기 위해 추가
        self.file_path = ""

    def collect_symbols(self, tree):
        # AST를 순회하며 다양한 심볼 정보 수집
        self._collect_imports(tree)
        self._collect_type_declarations(tree)
        self._collect_field_types(tree)
        self._collect_method_declarations(tree)
        self._collect_method_calls(tree)

    def _collect_imports(self, tree):
        # 임포트 문 정보 수집
        for path, node in tree.filter(javalang.tree.Import):
            if node.wildcard:
                self.imports[node.path + ".*"] = node.path
            else:
                class_name = node.path.split('.')[-1]
                self.imports[class_name] = node.path

    def _collect_type_declarations(self, tree):
        # 클래스, 인터페이스 등의 타입 선언 정보 수집
        for path, node in tree.filter(javalang.tree.TypeDeclaration):
            full_name = f"{self.current_package}.{node.name}" if self.current_package else node.name
            self.symbols['TypeDeclaration'].append(full_name)
            self.type_mapping[node.name] = full_name
            self.current_class = full_name

    def _collect_field_types(self, tree):
        # 필드 선언의 타입 정보 수집
        for path, node in tree.filter(javalang.tree.FieldDeclaration):
            field_type = self._get_type_name(node.type)
            for declarator in node.declarators:
                for _, imp in self.imports.items():
                    imp_last = imp.split('.')[-1]
                    if imp_last == field_type:
                        self.field_types[declarator.name] = imp

    def _collect_method_declarations(self, tree):
        # 메서드 선언 정보 수집
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            # if not isinstance(path[-2], javalang.tree.EnumBody) and not isinstance(path[-2], javalang.tree.ClassDeclaration):
            #     print(path[-2]) # 인터페이스의 경우에는 확인을 안했음
            #     break
            if isinstance(path[-2], javalang.tree.EnumBody):
                class_name = self.type_mapping[path[-3].name]
            elif isinstance(path[-2], javalang.tree.ClassCreator):
                for i in range(-1, -len(path) -1, -1):
                    if isinstance(path[i], javalang.tree.ClassDeclaration):
                        class_name = self.type_mapping[path[i].name]
            else:
                class_name = self.type_mapping[path[-2].name]
            method_signature = self._get_method_signature(class_name, node)
            self.symbols['MethodDeclaration'].append(method_signature)
            if method_signature == "EvCacheProvider.get(String, Map)":
                print(f"{class_name}.{node.name}", method_signature)
                print(node.name)
            self.method_signatures[f"{class_name}.{node.name}"] = method_signature

    def _collect_method_calls(self, tree):
        # 메서드 호출 분석
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            self._analyze_method_call(node, path)

    def _get_method_signature(self, class_name, method):
        # 메서드 시그니처 생성
        params = ", ".join([self._get_type_name(param.type) for param in method.parameters])
        return f"{class_name}.{method.name}({params})"

    def _get_type_name(self, type_node):
        # 타입 노드에서 타입 이름 추출
        if isinstance(type_node, javalang.tree.ReferenceType):
            return type_node.name
        return str(type_node)

    def _analyze_method_call(self, node, path):
        # 개별 메서드 호출 분
        if node.qualifier:
            target_class = self._infer_type(node, path)
            if target_class:
                self._categorize_method_call(target_class, node.member)
            else:
                # print(f"Could not infer type for: {node.qualifier}")
                pass
        else:
            self._analyze_no_qualifier_method_call(node, path)

    def _analyze_no_qualifier_method_call(self, node, path):
        user_define = []
        method_name = node.member
        # print("no : ", self.current_class)
        for md in self.symbols.get('MethodDeclaration', []):
            user_define.append(md.split('.')[1].split('(')[0])

        if self.current_class:
            full_method_name = f"{self.current_class}.{method_name}"
            if full_method_name in self.method_signatures:
                self.symbols['UserDefinedMethodCall'].append(full_method_name)
                return

        for import_name, import_path in self.imports.items():
            if import_name.endswith(method_name):
                self.symbols['UserDefinedMethodCall'].append(f"{import_path}")
                return

        if self.reflection.is_standard_library_method("java.lang", method_name):
            self.symbols['ResolvedMethodCall'].append(f"java.lang.{method_name}")
            return
        elif method_name in user_define:
            self.symbols['ResolvedMethodCall'].append(method_name) # 수정 필요(클래스가 없음)
        else:
            self.symbols['UnresolvedMethodCall'].append(method_name)

    def _categorize_method_call(self, target_class, method_name):
        user_define = []
        full_method_name = f"{target_class}.{method_name}"
        imports_values = self.imports.values()
        for md in self.symbols.get('MethodDeclaration', []):
            user_define.append(md.split('.')[1].split('(')[0])
        if self.reflection.is_standard_library_method(target_class, method_name) or target_class in imports_values or \
                method_name in user_define:
            self.symbols['ResolvedMethodCall'].append(full_method_name)
        elif full_method_name in self.method_signatures:
            self.symbols['UserDefinedMethodCall'].append(self.method_signatures[full_method_name])
        else:
            self.symbols['UnresolvedMethodCall'].append(full_method_name)

    def _infer_type(self, node, path):
        # 노드의 타입 추론
        arg = node.qualifier
        if arg:
            # 필드인 경우
            if arg in self.field_types:
                return self.field_types[arg]
            return self.type_mapping.get(node.member) or self.imports.get(node.member)
        elif isinstance(node, javalang.tree.ClassReference):
            return self.imports.get(arg.name, f"{self.current_package}.{arg.name}")
        elif isinstance(arg, str):
            return self.type_mapping.get(arg) or self.imports.get(arg)
        print(f"Unknown node type in _infer_type: {type(arg)}")
        return None

    def _get_local_variable_type(self, var_name, path):
        # 지역 변수의 타입 추론
        for node in reversed(path):
            if isinstance(node, javalang.tree.MethodDeclaration):
                for param in node.parameters:
                    if param.name == var_name:
                        return self._get_type_name(param.type)
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                for declarator in node.declarators:
                    if declarator.name == var_name:
                        return self._get_type_name(node.type)
        return None

    def generate_symbols(self, tree, file_path):
        self.reset()
        self.file_path = file_path  # 파일 경로 저장
        self.collect_symbols(tree)
        return self.create_json_output()

    def create_json_output(self):
        output = {
            self.file_path: {
                "TypeDeclarations": self.symbols.get('TypeDeclaration', []),
                "MethodDeclarations": self.symbols.get('MethodDeclaration', []),
                "MethodCalls": {
                    "Resolved": self.symbols.get('ResolvedMethodCall', []),
                    "UserDefined": self.symbols.get('UserDefinedMethodCall', []),
                    "Unresolved": self.symbols.get('UnresolvedMethodCall', [])
                },
                "Imports": self.imports,
                "FieldTypes": self.field_types
            }
        }
        return output

    def save_to_json(self, data, output_file):
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)