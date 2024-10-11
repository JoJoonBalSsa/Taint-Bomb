import os
import secrets

import javalang
import re

class ob_identifier:

    def __init__(self, folder_path, output_folder):
        self.folder_path = folder_path
        self.output_folder = output_folder

        self.main_class = None
        self.ann_list = []
        self.class_list = []

        self.not_ob_list = ['Class','get','main','accept','getName',
                            'Runnable','run','Callable','call','Comparable','compareTo','Cloneable','clone',#자바에서 자주 사용하는 인터페이스 및 메서드
                            'toObservable','map','toString'
                            ] #난독화 하면 안되는 식별자들
        self.identifier_map = {}  # 난독화 맵
        self.files = []  # 파일 경로 저장
        self.package_map = []  # 패키지 이름 저장 or set으로 해야할지도
        self.ran = secrets.choice(range(3))

        # 파일 수집 및 난독화 맵 구성
        self.collect_files()
        self.build_obfuscation_map()

        # 난독화 적용
        self.apply_obfuscation_to_files()
        print(self.identifier_map)
        print(self.package_map)


    def generate_obfuscated_name(self, name, length=8):
        """난독화된 이름을 생성합니다."""
        if name not in self.identifier_map and (name not in self.not_ob_list):
            obfuscated_name = None
            ran = self.ran

            while True:
                if ran == 0:
                    obfuscated_name = (''.join(secrets.choice(["l", "I"])) +
                                       ''.join(self.choose_chars(['l', '1', 'I'], length)))
                elif ran == 1:
                    obfuscated_name = (''.join(secrets.choice(['l', 'I', 'α', 'β', 'γ', 'δ', 'π'])) +
                                       ''.join(self.choose_chars(['l', '1', 'I', 'α', 'β', 'γ', 'δ', 'π'], length)))
                elif ran == 2:
                    obfuscated_name = (''.join(secrets.choice(['O', 'o'])) +
                                       ''.join(self.choose_chars(['0', 'O', 'o', 'Ο', 'о'], length)))

                if obfuscated_name not in self.identifier_map.values():
                    self.identifier_map[name] = obfuscated_name
                    break


    def choose_chars(self, random_list, k):
        return [secrets.choice(random_list) for _ in range(k)]


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

            try:
                # 자바 소스코드를 파싱하여 AST 추출
                tree = javalang.parse.parse(source_code)
            except SyntaxError as e:  # 문법 오류는 파이썬의 SyntaxError로 처리
                print(f"Syntax error in file {file_path}: {e}")
            except javalang.parser.JavaSyntaxError as e:
                print(f"Java syntax error in file {file_path}: {e}")

            # AST에서 식별자 수집 및 난독화 맵 구축
            self.collect_identifiers_from_ast(tree, file_path)


    def collect_identifiers_from_ast(self, tree, file_path):
        current_class = None
        for path, node in tree: # 패키지 선언
            if isinstance(node, javalang.tree.PackageDeclaration):
                self.package_map.append(node.name)  # 패키지 이름 저장


            # 클래스나 Enum 선언 (+ Interface)
            elif isinstance(node, javalang.tree.ClassDeclaration) or isinstance(node, javalang.tree.EnumDeclaration) or isinstance(node, javalang.tree.InterfaceDeclaration):
                current_class = node.name
                self.class_list.append(node.name)
                self.generate_obfuscated_name(node.name)

            elif isinstance(node, javalang.tree.AnnotationDeclaration): # 여기서 어노테이션들 이름 기록해 놔야함 (어노테이션 난독화)
                self.ann_list.append(node.name)
                self.generate_obfuscated_name(node.name)

            # 메서드 선언
            elif isinstance(node, javalang.tree.MethodDeclaration):
                if node.name == 'main':
                    self.main_class = current_class

                if any(ann.name == "Override" for ann in node.annotations):

                    self.not_ob_list.append(node.name)
                    self.identifier_map.pop(node.name, None)

                self.generate_obfuscated_name(node.name)

                # 메서드 매개변수 처리
                for param in node.parameters:
                    self.generate_obfuscated_name(param.name)

            # 변수 선언
            elif isinstance(node, javalang.tree.VariableDeclarator):
                self.generate_obfuscated_name(node.name)

            # 객체 생성 및 변수 선언
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):

                for declarator in node.declarators: # 변수 이름

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
            print(f"Identifier Obfuscating.. {file_path}")
            self.obfuscate_java_file(file_path, self.output_folder)

        self.replace_gradle()


    def replace_gradle(self):
        # build.gradle 파일 수정
        build_gradle_path = os.path.join(self.folder_path, 'build.gradle')
        if os.path.exists(build_gradle_path):
            with open(build_gradle_path, 'r', encoding='utf-8') as file:
                build_gradle_content = file.read()

            lines = build_gradle_content.split("\n")
            for i,line in enumerate(lines):
                if "Main-Class" in line:
                    print(line)
                    line = line.replace(self.main_class,self.identifier_map.get(self.main_class,self.main_class))
                    lines[i] = line
            build_gradle_content = '\n'.join(lines)

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
        obfuscated_code = self.replace_identifiers_in_code(source_code,file_path)

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


    def analyze_class_declaration(self,line): # 클래스 식별
        pattern = r'''
            ^\s*                    # 라인 시작과 앞쪽 공백
            (public|private|protected)?\s* # 접근 제어자 (선택적)
            (abstract|final)?\s*    # abstract 또는 final 키워드 (선택적)
            class\s+                # class 키워드
            (\w+)                   # 클래스 이름
            (\s+extends\s+\w+)?     # 상속 (선택적)
            (\s+implements\s+\w+(\s*,\s*\w+)*)?  # 인터페이스 구현 (선택적)
            \s*(\{|$)               # 중괄호 시작 또는 라인 끝
        '''
        match = re.match(pattern, line, re.VERBOSE)

        if match:
            class_name = match.group(3)  # 클래스 이름은 세 번째 그룹
            return True, class_name
        else:
            return False, None


    def extract_annotation_identifier(self,line): # 어노테이션 식별
        pattern = r'@\s*(\w+)'
        match = re.match(pattern, line.strip())
        if match:
            return match.group(1)
        else:
            return None


    def find_variable_declarations(self, code):  # 변수 선언 식별
            # 모든 변수 선언을 찾는 패턴
        pattern = re.compile(r'''
            # 접근 제어자 및 기타 제어자 (optional, 무시)
            (?:\b(?:public|protected|private|static|final|abstract|synchronized|volatile)\b\s+)*
    
            # 타입 (제네릭이나 배열 포함)
            (\w+(?:<[^>]+>)?(?:\[\])*)\s+
    
            # 변수명
            (\w+)
    
            # 첫 번째 매개변수 또는 끝에 , 세미콜론, 괄호로 끝나는지 확인
            (?=\s*[,;)])
        ''', re.VERBOSE)
        return [(match.group(1), match.group(2))
                for match in pattern.finditer(code) if match.group(1) != 'return']


    def replace_identifiers_in_code(self, source_code,file_path):
        # 난독화된 식별자 맵을 사용하여 소스 코드 내의 모든 식별자를 정확하게 치환하되, 리터럴 문자열은 제외.

        start_package = True
        ann = None
        external_class = set()

        imp_var_list = list()

        # 파일의 각 라인을 처리
        lines = source_code.splitlines()
        curr_class =None
        for i, line in enumerate(lines):
            # import로 시작하는 라인을 처리
            if line.strip().startswith("package"):
                if start_package:
                    start_package = False
                    continue

            if line.strip().startswith("@"): # 어노테이션 식별(사용자 정의인지 확인후 아니라면 난독화 제약 걸기)
                ann = self.extract_annotation_identifier(line)
                if ann and ann not in self.ann_list:
                    line = line.replace("@"+ann,"@"+ann+"_DO_NOT_OBFUSCATE")
                    variable_pattern = re.compile(r'(\w+)\s*=\s*(\w+\.class)')
                    matches = variable_pattern.findall(line)

                    for match in matches:
                        variable_name = match[0]
                        line = line.replace(variable_name, variable_name + "_DO_NOT_OBFUSCATE")

            if line.strip().startswith('import'):
                package_name_match = re.match(r'import\s+(static\s+)?([\w\.]+);', line)
                if package_name_match:
                    package_name = package_name_match.group(2)

                    # 패키지 맵에 있는 패키지이면 난독화 적용
                    if any(package_name.startswith(pkg) for pkg in self.package_map):
                        for pkg in list(reversed(self.package_map)): #왜 reversed를 했느냐 그건 조준형에게 물어보면 된다
                            if package_name.startswith(pkg):
                                pkg = pkg+"." # 패키지 끝 . 추가
                                ob_pkg = pkg.replace(".","_DO_NOT_OBFUSCATE.")
                                ob_pkg_line = package_name.replace(pkg,ob_pkg) # ㅎㅎ;
                                line = line.replace(package_name,ob_pkg_line)

                    else:
                        external_class.add(package_name.split('.')[-1])
                        continue

            """ 현재 클래스 식별 """
            is_class, class_name = self.analyze_class_declaration(line)
            if is_class:
                curr_class = class_name
                imp_var_list = []

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
                    
            match = self.find_variable_declarations(line)
            if match:
                for var_type, var_name in match:
                    if (var_type in external_class) or ("<" in var_type) or (var_type not in self.class_list):
                        imp_var_list.append(var_name)

            # 함수 호출 패턴 (외부 함수 난독화에서 제외)
            if not line.startswith("import"): # import부분은 식별 X
                pattern = r'(?:(?:\((?:[a-zA-Z][\w.$]*(?:\[\])?)\))?\s*)?([a-zA-Z][\w.$]*?)\.([a-zA-Z]\w*)(?:\s*\((.*?)\))?'

                matches = re.findall(pattern, line)
                for ii in range(len(matches)):
                    var , fun , _=  matches[ii]
                    if (var in imp_var_list) or (var in external_class) or (var in self.not_ob_list) :
                        if _:
                            line = line.replace(var+"."+fun+"(",var+"."+fun+"_DO_NOT_OBFUSCATE(")
                        else :
                            line = line.replace(var+"."+fun,var+"."+fun+"_DO_NOT_OBFUSCATE")

            pattern = r'<(.*?)>'
            matches = re.findall(pattern, line)

            for ii in range(len(matches)):
                iden = matches[ii]

                if (iden in external_class):
                    line = line.replace(iden,iden+"_DO_NOT_OBFUSCATE")

            # 문자열 리터럴 ("...")을 분리하여 처리
            parts = re.split(r'(".*?")', line)  # 큰따옴표로 묶인 문자열은 분리
            for j, part in enumerate(parts):
                # 문자열 리터럴은 그대로 두고, 리터럴이 아닌 코드 부분만 난독화 처리
                if not part.startswith('"'):  # 큰따옴표로 시작하지 않으면 코드 부분
                    for original, obfuscated in self.identifier_map.items():

                        # 일반적인 식별자 패턴
                        pattern = r'\b' + re.escape(original) + r'\b'
                        part = re.sub(pattern, obfuscated, part)

                    part = part.replace("_DO_NOT_OBFUSCATE","")
                parts[j] = part

            lines[i] = ''.join(parts)
        # 난독화된 코드를 반환
        obfuscated_code = '\n'.join(lines)
        return obfuscated_code
