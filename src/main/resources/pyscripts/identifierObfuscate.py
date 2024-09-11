import javalang
import random
import os
import glob
import re

class ob_identifier:
    def __init__(self, folder_path, output_directory):
        self.folder_path = folder_path
        self.output_directory = output_directory
        self.class_mapping = {}  # 클래스 난독화 매핑
        self.method_mapping = {}  # 메서드(함수) 난독화 매핑
        self.variable_mapping = {}  # 변수 난독화 매핑
        self.external_imports = set()  # 외부에서 import된 클래스
        self.user_defined_classes = set()  # 사용자 정의 클래스

        self.ran = random.choice([1, 2, 3])
        self.__process_java_files_in_folder__()

    def __generate_obfuscated_name__(self, length=8):
        """난독화된 이름을 생성합니다."""
        ran = self.ran
        if ran == 1:
            return ''.join(random.choices(["l", "I"], k=1)) + ''.join(random.choices(['l', '1', 'I'], k=length))
        elif ran == 2:
            return ''.join(random.choices(['l', 'I', 'α', 'β', 'γ', 'δ', 'π'], k=1)) + ''.join(random.choices(['l', '1', 'I', 'α', 'β', 'γ', 'δ', 'π'], k=length))
        elif ran == 3:
            return ''.join(random.choices(['O', 'o'], k=1)) + ''.join(random.choices(['0', 'O', 'o', 'Ο', 'о'], k=length))

    def __log_obfuscation_mapping__(self):
        """난독화 매핑을 로깅"""
        with open('obfuscation_log.txt', 'a') as log_file:
            log_file.write("Class Mapping:\n")
            for original, obfuscated in self.class_mapping.items():
                log_file.write(f'{original} -> {obfuscated}\n')

            log_file.write("\nMethod Mapping:\n")
            for original, obfuscated in self.method_mapping.items():
                log_file.write(f'{original} -> {obfuscated}\n')

            log_file.write("\nVariable Mapping:\n")
            for original, obfuscated in self.variable_mapping.items():
                log_file.write(f'{original} -> {obfuscated}\n')

    def __extract_imported_classes__(self, java_code):
        """import된 외부 라이브러리 클래스들을 식별하여 반환"""
        external_imports = set()
        # 코드에서 import 구문을 찾고 클래스 이름을 추출
        lines = java_code.splitlines()
        for line in lines:
            if line.strip().startswith("import"):
                import_class_match = re.search(r'import\s+([\w\.]+);', line)
                if import_class_match:
                    imported_class = import_class_match.group(1).split('.')[-1]
                    external_imports.add(imported_class)
        return external_imports

    def __extract_user_defined_identifiers__(self, java_code):
        """사용자 정의된 클래스, 메서드, 변수 추출"""
        user_defined_classes = set()
        user_defined_methods = set()
        user_defined_variables = set()

        try:
            tokens = list(javalang.tokenizer.tokenize(java_code))
            parser = javalang.parser.Parser(tokens)
            tree = parser.parse()  # 전체 파싱 시도

            # 트리를 순회하면서 클래스, 메서드, 변수 식별
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    user_defined_classes.add(node.name)  # 클래스 이름 추가
                    for body_item in node.body:
                        if isinstance(body_item, javalang.tree.MethodDeclaration):
                            user_defined_methods.add(body_item.name)  # 메서드 이름 추가
                            for param in body_item.parameters:
                                user_defined_variables.add(param.name)  # 매개변수 이름 추가
                            if body_item.body is not None:
                                for statement in body_item.body:
                                    if isinstance(statement, javalang.tree.VariableDeclarator):
                                        user_defined_variables.add(statement.name)  # 변수 이름 추가
                elif isinstance(node, javalang.tree.MethodDeclaration):
                    user_defined_methods.add(node.name)
                    for param in node.parameters:
                        user_defined_variables.add(param.name)
                    if node.body is not None:
                        for statement in node.body:
                            if isinstance(statement, javalang.tree.VariableDeclarator):
                                user_defined_variables.add(statement.name)
                elif isinstance(node, javalang.tree.VariableDeclarator):
                    user_defined_variables.add(node.name)
                elif isinstance(node, javalang.tree.TryStatement):
                    # TryStatement에서 괄호 안에 선언된 자원(resource) 추출
                    if node.resources:
                        for resource in node.resources:
                            if isinstance(resource, javalang.tree.FormalParameter):
                                if isinstance(resource.declarator, javalang.tree.VariableDeclarator):
                                    user_defined_variables.add(resource.declarator.name)

        except javalang.parser.JavaSyntaxError as e:
            print(f"Java syntax error in file: {e}")
            return user_defined_classes, user_defined_methods, user_defined_variables

        return user_defined_classes, user_defined_methods, user_defined_variables

    def __create_identifier_mapping__(self, user_defined_classes, user_defined_methods, user_defined_variables):
        """식별자를 난독화된 이름으로 매핑"""
        # 클래스 이름 난독화
        for class_name in user_defined_classes:
            if class_name not in self.class_mapping:
                obfuscated_class_name = self.__generate_obfuscated_name__()
                while obfuscated_class_name in self.class_mapping.values():
                    obfuscated_class_name = self.__generate_obfuscated_name__()
                self.class_mapping[class_name] = obfuscated_class_name

        # 함수 이름 난독화
        for method_name in user_defined_methods:
            if method_name not in self.method_mapping:
                obfuscated_method_name = self.__generate_obfuscated_name__()
                while obfuscated_method_name in self.method_mapping.values():
                    obfuscated_method_name = self.__generate_obfuscated_name__()
                self.method_mapping[method_name] = obfuscated_method_name

        # 변수 이름 난독화
        for variable_name in user_defined_variables:
            if variable_name not in self.variable_mapping:
                obfuscated_variable_name = self.__generate_obfuscated_name__()
                while obfuscated_variable_name in self.variable_mapping.values():
                    obfuscated_variable_name = self.__generate_obfuscated_name__()
                self.variable_mapping[variable_name] = obfuscated_variable_name

        # 난독화 매핑을 로그에 기록
        self.__log_obfuscation_mapping__()

    def __obfuscate_code_with_mapping__(self, java_code):
        """난독화 매핑을 사용하여 클래스, 함수, 변수, 매개변수 등 각 식별자를 구분하여 변환"""
        obfuscated_code = java_code
        object_types = {}  # 객체의 타입을 추적하기 위한 딕셔너리

        # 코드 라인을 하나씩 처리
        lines = obfuscated_code.splitlines()
        for i, line in enumerate(lines):
            # import 문은 난독화하지 않음
            if line.strip().startswith("import"):
                continue

            # Class.forName("클래스명") 패턴 찾기
            class_for_name_matches = re.finditer(r'Class\.forName\("([\w.]+)"\)', line)
            for match in class_for_name_matches:
                class_name_literal = match.group(1).split('.')[-1]
                if class_name_literal in self.class_mapping:
                    obfuscated_class_name = self.class_mapping.get(class_name_literal, class_name_literal)
                    line = line.replace(class_name_literal, obfuscated_class_name)

            # getMethod("메서드명") 패턴 찾기
            get_method_matches = re.finditer(r'getMethod\("([A-Za-z_]\w*)"', line)
            for match in get_method_matches:
                method_name_literal = match.group(1)
                if method_name_literal in self.method_mapping:
                    obfuscated_method_name = self.method_mapping.get(method_name_literal, method_name_literal)
                    line = line.replace(method_name_literal, obfuscated_method_name)

            # 리터럴 문자열을 처리하기 위해 문자열 리터럴 분리
            parts = re.split(r'(".*?")', line)  # 문자열 리터럴("...")을 분리

            new_line = ""
            for part in parts:
                # 리터럴 문자열은 그대로 유지
                if part.startswith('"') and part.endswith('"'):
                    new_line += part
                    continue

                # 클래스 선언 시 클래스 이름과 부모 클래스(extends) 이름 난독화
                class_declaration_match = re.search(r'\bclass\s+([A-Za-z_]\w*)\s*(extends\s+([A-Za-z_]\w*))?\s*\{?', part)
                if class_declaration_match:
                    class_name = class_declaration_match.group(1)  # 클래스 이름
                    parent_class_name = class_declaration_match.group(3)  # 부모 클래스 이름

                    # 클래스 이름 난독화
                    if class_name in self.class_mapping:
                        obfuscated_class_name = self.class_mapping.get(class_name, class_name)
                        part = re.sub(r'\b' + re.escape(class_name) + r'\b', obfuscated_class_name, part)

                    # 부모 클래스 이름 난독화 (extends)
                    if parent_class_name and parent_class_name in self.class_mapping:
                        obfuscated_parent_class_name = self.class_mapping.get(parent_class_name, parent_class_name)
                        part = re.sub(r'\b' + re.escape(parent_class_name) + r'\b', obfuscated_parent_class_name, part)

                # 클래스타입 객체 선언 난독화
                class_type_declaration_match = re.search(r'\b([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*;', part)
                if class_type_declaration_match:
                    class_name = class_type_declaration_match.group(1)  # 클래스 이름 (타입)
                    var_name = class_type_declaration_match.group(2)  # 변수 이름
                    if class_name in self.class_mapping:
                        obfuscated_class_name = self.class_mapping.get(class_name, class_name)
                        part = re.sub(r'\b' + re.escape(class_name) + r'\b', obfuscated_class_name, part)

                # 클래스 생성자(Constructor) 난독화 (생성자는 클래스 이름과 동일)
                constructor_match = re.search(r'\b([A-Za-z_]\w*)\s*\(', part)
                if constructor_match:
                    constructor_name = constructor_match.group(1)
                    if constructor_name in self.class_mapping:
                        obfuscated_constructor_name = self.class_mapping.get(constructor_name, constructor_name)
                        part = re.sub(r'\b' + re.escape(constructor_name) + r'\b', obfuscated_constructor_name, part)

                # 객체 생성 시 클래스 이름을 난독화 (new ClassName()) - 외부 라이브러리는 제외
                class_instantiation_match = re.search(r'\bnew\s+([A-Za-z_]\w*)\s*\(', part)
                if class_instantiation_match:
                    class_name = class_instantiation_match.group(1)
                    if class_name not in self.external_imports and class_name in self.class_mapping:
                        obfuscated_class_name = self.class_mapping.get(class_name, class_name)
                        part = re.sub(r'\b' + re.escape(class_name) + r'\b', obfuscated_class_name, part)

                    # 객체가 생성될 때 변수에 클래스 정보를 저장
                    obj_name_match = re.search(r'\b([A-Za-z_]\w*)\s*=\s*new\s+([A-Za-z_]\w*)', part)
                    if obj_name_match:
                        obj_name, class_name = obj_name_match.groups()
                        #object_types[obj_name] = class_name  # 변수와 클래스의 관계를 저장 => 언젠가 쓰일듯

                # 클래스에서 메서드를 호출할 때 클래스와 메서드 이름을 모두 난독화
                class_method_call_match = re.finditer(r'\b([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)\s*\(', part)
                for match in class_method_call_match:
                    class_name, method_name = match.groups()

                    # 클래스 이름 난독화 (클래스 앞에 점(.)이 없을 때)
                    if class_name in self.class_mapping and not re.search(r'\.', part.split(class_name)[0][-1]):
                        obfuscated_class_name = self.class_mapping.get(class_name, class_name)
                        part = re.sub(r'\b' + re.escape(class_name) + r'\b', obfuscated_class_name, part)

                    # 메서드 이름 난독화 (외부 라이브러리가 아닌 경우만)
                    if method_name in self.method_mapping and class_name not in self.external_imports:
                        obfuscated_method_name = self.method_mapping.get(method_name, method_name)
                        part = re.sub(r'\b' + re.escape(method_name) + r'\b(?=\()', obfuscated_method_name, part)

                # 함수 호출 시 함수 이름을 난독화
                method_call_matches = re.finditer(r'\b([A-Za-z_]\w*)\s*\(', part)
                for method_call_match in method_call_matches:
                    method_name = method_call_match.group(1)

                    # 메서드 이름 난독화 (외부 라이브러리랑 main은 제외)
                    if method_name in self.method_mapping and method_name not in self.external_imports:
                        if method_name == 'main':
                            part = re.sub(r'\b' + re.escape(method_name) + r'\b', 'main', part)
                        else:
                            obfuscated_method_name = self.method_mapping.get(method_name, method_name)
                            part = re.sub(r'\b' + re.escape(method_name) + r'\b(?=\()', obfuscated_method_name, part)

                # 변수 식별자만 난독화 (정확한 변수만 치환)
                for var_name, obfuscated_var_name in self.variable_mapping.items():
                    # 메서드 호출이 아닌 부분에서만 변수 이름을 난독화
                    part = re.sub(r'\b' + re.escape(var_name) + r'\b(?!\s*\()', obfuscated_var_name, part)

                # 난독화된 부분을 다시 조합
                new_line += part

            # 난독화된 라인을 다시 저장
            lines[i] = new_line

        obfuscated_code = "\n".join(lines)
        return obfuscated_code






    def __process_java_files_in_folder__(self):
        """자바 파일을 찾아서 난독화하고, 결과를 출력 디렉토리에 저장"""
        java_files = glob.glob(os.path.join(self.folder_path, '**', '*.java'), recursive=True)

        # 모든 파일에서 식별자 추출 (전역 매핑을 위해)
        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                java_code = file.read()

                # 외부에서 import된 클래스 식별
                external_imports = self.__extract_imported_classes__(java_code)
                self.external_imports.update(external_imports)

                # 사용자 정의 클래스, 메서드, 변수 추출
                user_defined_classes, user_defined_methods, user_defined_variables = self.__extract_user_defined_identifiers__(java_code)
                self.user_defined_classes.update(user_defined_classes)

                # 전역 난독화 매핑에 추가
                self.__create_identifier_mapping__(user_defined_classes, user_defined_methods, user_defined_variables)

        # 모든 파일에 동일한 난독화 매핑을 적용하여 코드 변환
        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                java_code = file.read()

            os.remove(file_path)
            # 난독화된 코드 생성
            obfuscated_code = self.__obfuscate_code_with_mapping__(java_code)
            # 기존 파일 경로와 패키지 유지
            relative_path = os.path.relpath(file_path, self.folder_path)
            base_dir, original_filename = os.path.split(relative_path)
            original_class_name = original_filename.split('.')[0]
            # 난독화된 클래스 이름 생성
            new_class_name = self.class_mapping.get(original_class_name, original_class_name)
            new_filename = new_class_name + '.java'
            output_path = os.path.join(self.output_directory, base_dir, new_filename)
            # 출력 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # 난독화된 파일 저장
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(obfuscated_code)

        # build.gradle 파일 수정
        build_gradle_path = os.path.join(self.folder_path, 'build.gradle')
        if os.path.exists(build_gradle_path):
            with open(build_gradle_path, 'r', encoding='utf-8') as file:
                build_gradle_content = file.read()

            # 'Main-Class': 'christmas.?????' 패턴을 찾아서 대체
            def replace_main_class(match):
                original_fully_qualified_class_name = match.group(2)
                package_name = '.'.join(original_fully_qualified_class_name.split('.')[:-1])
                original_class_name = original_fully_qualified_class_name.split('.')[-1]
                new_class_name = self.class_mapping.get(original_class_name, original_class_name)
                return f"{match.group(1)}{package_name}.{new_class_name}{match.group(3)}"

            build_gradle_content = re.sub(
                r"('Main-Class'\s*:\s*')([\w.]+)(')",
                replace_main_class,
                build_gradle_content
            )

            # 수정된 내용을 다시 build.gradle에 씀
            with open(build_gradle_path, 'w', encoding='utf-8') as file:
                file.write(build_gradle_content)

        print("난독화 완료!")
