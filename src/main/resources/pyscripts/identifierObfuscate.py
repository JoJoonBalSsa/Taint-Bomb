import os
import javalang
import secrets
import re

class ob_identifier:
    def __init__(self, folder_path, output_folder):
        self.folder_path = folder_path
        self.output_folder = output_folder
        self.identifier_map = {}  # 난독화 맵
        self.files = []  # 파일 경로 저장
        self.package_map = []  # 패키지 이름 저장 or set으로 해야할지도

        self.ran = secrets.choice([1, 2, 3])

        # 파일 수집 및 난독화 맵 구성
        self.collect_files()
        self.build_obfuscation_map()

        # 난독화 적용
        self.apply_obfuscation_to_files()
        print(self.identifier_map)

    def generate_obfuscated_name(self, name, length=8):
        """난독화된 이름을 생성합니다."""
        if name not in self.identifier_map and name != 'main':
            obfuscated_name = None
            ran = self.ran

            while True:
                if ran == 1:
                    obfuscated_name = ''.join([secrets.choice(["l", "I"])]) + ''.join([secrets.choice(['l', '1', 'I']) for _ in range(length)])
                elif ran == 2:
                    obfuscated_name = ''.join([secrets.choice(['l', 'I', 'α', 'β', 'γ', 'δ', 'π'])]) + ''.join([secrets.choice(['l', '1', 'I', 'α', 'β', 'γ', 'δ', 'π']) for _ in range(length)])
                elif ran == 3:
                    obfuscated_name = ''.join([secrets.choice(['O', 'o'])]) + ''.join([secrets.choice(['0', 'O', 'o', 'Ο', 'о']) for _ in range(length)])

                if obfuscated_name not in self.identifier_map.values():
                    self.identifier_map[name] = obfuscated_name                    
                    break

    def collect_files(self):
        """모든 자바 파일을 수집합니다."""
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    self.files.append(file_path)

    def build_obfuscation_map(self):
        """모든 파일을 처리하고 난독화할 식별자를 수집하여 맵을 구성합니다."""
        for file_path in self.files:
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()

            # 자바 소스코드를 파싱하여 AST 추출
            tree = javalang.parse.parse(source_code)

            # AST에서 식별자 수집 및 난독화 맵 구축
            self.collect_identifiers_from_ast(tree, file_path)

    def collect_identifiers_from_ast(self, tree, file_path):
        for path, node in tree:
            # 패키지 선언
            if isinstance(node, javalang.tree.PackageDeclaration):
                self.package_map.append(node.name)  # 패키지 이름 저장

            # 클래스나 Enum 선언
            elif isinstance(node, javalang.tree.ClassDeclaration) or isinstance(node, javalang.tree.EnumDeclaration):
                self.generate_obfuscated_name(node.name)

            # 메서드 선언
            elif isinstance(node, javalang.tree.MethodDeclaration):
                self.generate_obfuscated_name(node.name)

                # 메서드 매개변수 처리
                for param in node.parameters:
                    self.generate_obfuscated_name(param.name)

            # 변수 선언
            elif isinstance(node, javalang.tree.VariableDeclarator):
                self.generate_obfuscated_name(node.name)

            # 객체 생성 및 변수 선언
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                # 변수 선언에서 객체가 생성될 때의 변수 이름 처리
                for declarator in node.declarators:
                    self.generate_obfuscated_name(declarator.name)

            # Try 문과 그 안에 있는 리소스, 변수, 메서드 호출 처리
            elif isinstance(node, javalang.tree.TryStatement):
                # Try-with-resources: 리소스 변수 난독화 (리소스가 있는 경우만)
                if node.resources is not None:
                    for resource in node.resources:
                        self.generate_obfuscated_name(resource.name)

                # Try 블록 안의 명령문 처리
                for statement in node.block:
                    if isinstance(statement, javalang.tree.LocalVariableDeclaration):
                        for declarator in statement.declarators:
                            self.generate_obfuscated_name(declarator.name)
                    # elif isinstance(statement, javalang.tree.StatementExpression):
                    #     # MethodInvocation의 변수나 메서드 식별자 처리
                    #     if isinstance(statement.expression, javalang.tree.MethodInvocation):
                    #         if statement.expression.qualifier:
                    #             self.generate_obfuscated_name(statement.expression.qualifier)
                    #         self.generate_obfuscated_name(statement.expression.member)


    def apply_obfuscation_to_files(self):
        """난독화된 맵을 사용하여 각 파일을 다시 처리하고 난독화된 파일로 저장합니다."""
        for file_path in self.files:
            self.obfuscate_java_file(file_path, self.output_folder)

        self.replace_gradle()


    def replace_gradle(self):
        # build.gradle 파일 수정
        build_gradle_path = os.path.join(self.folder_path, 'build.gradle')
        if os.path.exists(build_gradle_path):
            with open(build_gradle_path, 'r', encoding='utf-8') as file:
                build_gradle_content = file.read()

            # 'Main-Class': 'pkg.?????' 패턴을 찾아서 대체
            def replace_main_class(match):
                original_fully_qualified_class_name = match.group(2)
                package_name = '.'.join(original_fully_qualified_class_name.split('.')[:-1])
                original_class_name = original_fully_qualified_class_name.split('.')[-1]
                new_class_name = self.identifier_map.get(original_class_name, original_class_name)
                return f"{match.group(1)}{package_name}.{new_class_name}{match.group(3)}"

            build_gradle_content = re.sub(
                r"('Main-Class'\s*:\s*')([\w.]+)(')",
                replace_main_class,
                build_gradle_content
            )

            # 수정된 내용을 다시 build.gradle에 씀
            with open(build_gradle_path, 'w', encoding='utf-8') as file:
                file.write(build_gradle_content)


    def obfuscate_java_file(self, file_path, output_folder):
        """난독화된 식별자를 실제로 파일에 적용하여 저장."""

        print("Processing file : ",file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()

        os.remove(file_path)
        # 난독화 맵을 사용하여 소스 코드에 난독화된 식별자 치환 적용
        obfuscated_code = self.replace_identifiers_in_code(source_code)


        relative_path = os.path.relpath(file_path, self.folder_path)
        base_dir, original_filename = os.path.split(relative_path)

        # 파일 이름을 난독화된 클래스 또는 Enum 이름으로 변경
        file_name = os.path.basename(file_path)
        class_or_enum_name = os.path.splitext(file_name)[0]

        # 난독화 맵에서 클래스 또는 Enum의 난독화된 이름을 가져옴
        class_or_enum_obfuscated = self.identifier_map.get(class_or_enum_name, class_or_enum_name)

        # 새 파일 이름으로 저장 (클래스나 Enum 이름에 맞춰 파일명 설정)
        new_file_name = f"{class_or_enum_obfuscated}.java"
        output_path = os.path.join(self.output_folder, base_dir, new_file_name)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as new_file:
            new_file.write(obfuscated_code)  # 난독화된 코드를 새 파일에 저장

    def replace_identifiers_in_code(self, source_code):
        """난독화된 식별자 맵을 사용하여 소스 코드 내의 모든 식별자를 정확하게 치환하되, 리터럴 문자열은 제외."""

        # 파일의 각 라인을 처리
        lines = source_code.splitlines()
        for i, line in enumerate(lines):
            # import로 시작하는 라인을 처리
            if line.strip().startswith('import'):
                package_name_match = re.match(r'import\s+([\w\.]+);', line)
                if package_name_match:
                    package_name = package_name_match.group(1)

                    # 패키지 맵에 있는 패키지이면 난독화 적용
                    if not any(package_name.startswith(pkg) for pkg in self.package_map):
                        continue


            # 복호화 코드 내 리터럴 문자 복호화

            # Class.forName("클래스명") 패턴 찾기
            class_for_name_matches = re.finditer(r'Class\.forName\("([\w.]+)"\)', line)
            for match in class_for_name_matches:
                class_name_literal = match.group(1).split('.')[-1]
                if class_name_literal in self.identifier_map:
                    obfuscated_class_name = self.identifier_map.get(class_name_literal, class_name_literal)
                    line = line.replace(class_name_literal, obfuscated_class_name)

            # getMethod("메서드명") 패턴 찾기
            get_method_matches = re.finditer(r'getMethod\("([A-Za-z_]\w*)"', line)
            for match in get_method_matches:
                method_name_literal = match.group(1)
                if method_name_literal in self.identifier_map:
                    obfuscated_method_name = self.identifier_map.get(method_name_literal, method_name_literal)
                    line = line.replace(method_name_literal, obfuscated_method_name)



            # 문자열 리터럴 ("...")을 분리하여 처리
            parts = re.split(r'(".*?")', line)  # 큰따옴표로 묶인 문자열은 분리
            for j, part in enumerate(parts):
                # 문자열 리터럴은 그대로 두고, 리터럴이 아닌 코드 부분만 난독화 처리
                if not part.startswith('"'):  # 큰따옴표로 시작하지 않으면 코드 부분
                    for original, obfuscated in self.identifier_map.items():
                        # 일반적인 식별자 패턴
                        pattern = r'\b' + re.escape(original) + r'\b'
                        part = re.sub(pattern, obfuscated, part)
                # parts 리스트에 다시 수정된 코드를 반영
                parts[j] = part

            # 수정된 라인을 결합
            lines[i] = ''.join(parts)

        # 난독화된 코드를 반환
        obfuscated_code = '\n'.join(lines)
        return obfuscated_code