import os
import secrets
import javalang
import re
import json
from typing import Dict, Set, Tuple, Optional


class SmartIdentifierObfuscator:
    """
    타입 기반 자동 분류를 사용하는 스마트 식별자 난독화기
    정의 기반 접근: 프로젝트 내 정의되지 않은 것은 모두 외부로 간주하여 자동 제외
    """

    # Java 기본 타입 및 내장 클래스
    JAVA_BUILTIN_TYPES = {
        # Primitive types
        'byte', 'short', 'int', 'long', 'float', 'double', 'boolean', 'char', 'void',
        # Wrapper classes
        'Byte', 'Short', 'Integer', 'Long', 'Float', 'Double', 'Boolean', 'Character',
        # Common classes
        'String', 'Object', 'Class', 'System', 'Math', 'StringBuilder', 'StringBuffer',
        # Collections
        'List', 'Set', 'Map', 'ArrayList', 'HashSet', 'HashMap', 'LinkedList',
        'Collection', 'Collections', 'Arrays',
        # Exceptions
        'Exception', 'RuntimeException', 'Throwable', 'Error',
        # I/O
        'File', 'InputStream', 'OutputStream', 'Reader', 'Writer',
        # Thread
        'Thread', 'Runnable',
    }

    # Java 표준 인터페이스 메서드
    JAVA_INTERFACE_METHODS = {
        'run', 'call', 'accept', 'apply', 'test',  # Functional interfaces
        'compareTo', 'compare',  # Comparable, Comparator
        'clone',  # Cloneable
        'equals', 'hashCode', 'toString',  # Object methods
        'iterator', 'hasNext', 'next',  # Iterator
        'size', 'isEmpty', 'contains', 'add', 'remove', 'clear', 'get',  # Collection
    }

    # 절대 난독화하면 안 되는 메서드
    PROTECTED_METHODS = {
        'main',  # Entry point
        'equals', 'hashCode', 'toString', 'clone',  # Object methods
        'finalize', 'notify', 'notifyAll', 'wait',  # Object native methods

        # Android 생명주기 메서드 (Activity)
        'onCreate', 'onStart', 'onResume', 'onPause', 'onStop', 'onDestroy',
        'onRestart', 'onNewIntent', 'onActivityResult', 'onSaveInstanceState',
        'onRestoreInstanceState', 'onPostCreate', 'onPostResume',

        # Android 생명주기 메서드 (Fragment)
        'onAttach', 'onCreateView', 'onViewCreated', 'onDestroyView', 'onDetach',

        # Android 생명주기 메서드 (Service)
        'onBind', 'onUnbind', 'onStartCommand', 'onRebind',

        # Android 생명주기 메서드 (BroadcastReceiver)
        'onReceive',

        # Android 생명주기 메서드 (Application)
        'onConfigurationChanged', 'onLowMemory', 'onTrimMemory',

        # Android View 콜백
        'onClick', 'onLongClick', 'onTouch', 'onFocusChange',
        'onCheckedChanged', 'onItemClick', 'onItemSelected',

        # Android Permission
        'onRequestPermissionsResult',

        # RecyclerView ViewHolder
        'onBindViewHolder', 'onCreateViewHolder', 'getItemCount',

        # Parcelable
        'writeToParcel', 'describeContents',
    }

    # 안드로이드 컴포넌트 클래스 서픽스 (매니페스트에 등록되므로 난독화 불가)
    ANDROID_COMPONENT_SUFFIXES = [
        'Activity',  # MainActivity, ChangePasswordActivity 등
        'Service',  # MyService 등
        'Receiver',  # MyReceiver, MyBroadcastReceiver 등
        'Provider',  # MyProvider, MyContentProvider 등
        'Application',  # MyApplication 등
        'Fragment',  # MyFragment 등
    ]

    # 절대 난독화하면 안 되는 클래스 (안드로이드 자동 생성 등)
    PROTECTED_CLASSES = {
        'R',  # Android 리소스 클래스 (자동 생성)
        'BuildConfig',  # Gradle 자동 생성 클래스
    }

    # R 클래스의 내부 클래스 (리소스 타입) - 난독화 금지
    R_INNER_CLASSES = {
        'id', 'layout', 'drawable', 'string', 'color', 'dimen',
        'style', 'menu', 'xml', 'anim', 'raw', 'mipmap',
        'animator', 'interpolator', 'transition', 'array',
        'bool', 'integer', 'attr', 'styleable', 'font', 'navigation'
    }

    # 외부 API의 흔한 멤버 이름 - 파라미터/변수로 사용되어도 난독화 금지
    # (프로젝트 내부에서 사용하더라도 외부 API와 충돌 방지)
    EXTERNAL_API_MEMBERS = {
        # Message 클래스 필드
        'replyTo', 'what', 'arg1', 'arg2', 'obj', 'sendingUid',
        # InputStream/OutputStream 메서드
        'read', 'write',
        # Builder 패턴 (Notification, Retrofit 등)
        'build', 'setContentText', 'setContentTitle', 'setSmallIcon',
        'setAutoCancel', 'setPriority', 'setContentIntent',
        'baseUrl', 'addConverterFactory', 'client',  # Retrofit
        # Notification
        'setDescription', 'setName', 'setImportance', 'setSound',
        'createNotificationChannel', 'notify',
        # ContactsContract 상수
        'NUMBER', 'DISPLAY_NAME', 'PHOTO_URI', 'LOOKUP_KEY',
        # 데이터베이스
        'query', 'insert', 'update', 'delete',
        # 흔한 메서드명
        'importDatabase', 'exportDatabase',
    }

    # 잘 알려진 외부 프레임워크 클래스 (멤버 접근 시 보호)
    KNOWN_EXTERNAL_CLASSES = {
        # Android framework
        'Log', 'Toast', 'Intent', 'Bundle', 'Context', 'Activity', 'Fragment',
        'View', 'TextView', 'Button', 'ImageView', 'EditText',
        'RecyclerView', 'Adapter', 'ViewHolder',
        'Handler', 'Message', 'Looper',
        'SharedPreferences', 'Editor',
        'Uri', 'Cursor', 'ContentValues',
        'Bitmap', 'Canvas', 'Paint',
        'MediaType', 'RequestBody', 'Response', 'Call', 'Callback',  # OkHttp
        'PendingIntent', 'Notification', 'NotificationManager', 'NotificationChannel',
        'BroadcastReceiver', 'Service', 'IntentFilter',
        'ContactsContract', 'CommonDataKinds', 'Phone',  # Contacts
        'Builder',  # 다양한 Builder 클래스
        # Java standard
        'System', 'Math', 'Arrays', 'Collections',
        'File', 'InputStream', 'OutputStream', 'Reader', 'Writer', 'BufferedReader',
        'Thread', 'Runnable',
        'Exception', 'IOException', 'RuntimeException',
    }

    def __init__(self, folder_path: str, output_folder: str):
        self.folder_path = folder_path
        self.output_folder = output_folder

        # 프로젝트 정의 정보
        self.project_definitions = {
            'packages': set(),  # 프로젝트 패키지명
            'classes': set(),  # 정의된 클래스명
            'methods': {},  # {class_name: set(method_names)}
            'fields': {},  # {class_name: set(field_names)}
            'all_methods': set(),  # 모든 메서드명 (빠른 검색용)
        }

        # 타입 추적 정보
        self.type_info = {
            'variables': {},  # {var_name: type_name} - 변수 타입
            'fields': {},  # {field_name: type_name} - 필드 타입
            'method_returns': {},  # {method_name: return_type} - 메서드 리턴 타입
            'method_params': {},  # {method_name: [(param_name, param_type), ...]}
        }

        # Import 정보
        self.imports_by_file = {}  # {file_path: {class_name: full_package}}
        self.external_classes = set()  # 외부 클래스 (import된 것 중 내부가 아닌 것)

        # 난독화 관련
        self.identifier_map = {}  # 난독화 맵
        self.files = []  # 파일 경로
        self.ran = secrets.choice(range(2))  # 난독화 모드
        self.file_mapping = {}  # 파일명 매핑: {원본경로: 난독화된경로}

        # 특수 처리
        self.main_class = None
        self.external_pkg = [
            'org.objectweb.asm',
            'android.',  # 안드로이드 프레임워크
            'androidx.',  # 안드로이드 지원 라이브러리
            'java.',  # Java 표준 라이브러리
            'javax.',  # Java 확장 라이브러리
            'kotlin.',  # Kotlin 표준 라이브러리
            'okhttp3.',  # OkHttp
            'com.google.',  # Google 라이브러리
        ]

        # 안드로이드 프로젝트 감지
        self.is_android_project = self._detect_android_project()

        # 실행
        print("=" * 60)
        print("Smart Identifier Obfuscator - Type-based Auto Classification")
        print("=" * 60)
        if self.is_android_project:
            print("[OK] Android project detected - Component classes will be protected")
        else:
            print("[OK] Standard Java project - All classes can be obfuscated")
        self.collect_files()
        self.process()

    def _detect_android_project(self) -> bool:
        """
        안드로이드 프로젝트인지 감지
        AndroidManifest.xml 또는 build.gradle 파일의 존재 여부로 판단
        """
        # folder_path의 상위 디렉토리들을 확인 (src/main/java 구조 고려)
        current_path = os.path.abspath(self.folder_path)

        # 최대 5단계 상위 디렉토리까지 확인
        for _ in range(5):
            # AndroidManifest.xml 확인
            manifest_path = os.path.join(current_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                return True

            # src/main/AndroidManifest.xml 확인
            manifest_path = os.path.join(current_path, 'src', 'main', 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                return True

            # app/src/main/AndroidManifest.xml 확인
            manifest_path = os.path.join(current_path, 'app', 'src', 'main', 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                return True

            # build.gradle에서 Android 플러그인 확인
            build_gradle = os.path.join(current_path, 'build.gradle')
            if os.path.exists(build_gradle):
                try:
                    with open(build_gradle, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'com.android.application' in content or 'com.android.library' in content:
                            return True
                except:
                    pass

            # 상위 디렉토리로 이동
            parent = os.path.dirname(current_path)
            if parent == current_path:  # 루트 디렉토리 도달
                break
            current_path = parent

        return False

    def collect_files(self):
        """모든 Java 파일 수집"""
        print("\n[Step 1] Collecting Java files...")
        excluded_files = {'R.java', 'BuildConfig.java'}
        excluded_count = 0

        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.java'):
                    # 자동 생성 파일 제외
                    if file in excluded_files:
                        excluded_count += 1
                        continue

                    file_path = os.path.join(root, file)
                    self.files.append(file_path)

        print(f"  Found {len(self.files)} Java files")
        if excluded_count > 0:
            print(f"  Excluded {excluded_count} auto-generated files (R.java, BuildConfig.java)")

    def process(self):
        """전체 난독화 프로세스"""
        # Phase 1: 모든 정의 수집
        print("\n[Step 2] Collecting all definitions...")
        self.collect_all_definitions()

        # Phase 2: 타입 정보 수집
        print("\n[Step 3] Collecting type information...")
        self.collect_type_information()

        # Phase 3: Import 분석
        print("\n[Step 4] Analyzing imports...")
        self.analyze_imports()

        # Phase 4: 난독화 맵 생성
        print("\n[Step 5] Building obfuscation map...")
        self.build_obfuscation_map()

        # Phase 5: 난독화 적용
        print("\n[Step 6] Applying obfuscation...")
        self.apply_obfuscation()

        print("\n" + "=" * 60)
        print(f"Obfuscation completed!")
        print(f"  Total identifiers obfuscated: {len(self.identifier_map)}")
        print(f"  External identifiers protected: {len(self.external_classes)}")
        print("=" * 60)

    # ========================================================================
    # Phase 1: 정의 수집
    # ========================================================================

    def collect_all_definitions(self):
        """프로젝트 내 모든 정의 수집"""
        for file_path in self.files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    source_code = file.read()

                tree = javalang.parse.parse(source_code)
                self._collect_definitions_from_tree(tree, file_path)

            except javalang.parser.JavaSyntaxError as e:
                print(f"  [WARN] Java syntax error in {file_path}: {e}")
            except Exception as e:
                print(f"  [WARN] Error parsing {file_path}: {e}")

        print(f"  Packages: {len(self.project_definitions['packages'])}")
        print(f"  Classes: {len(self.project_definitions['classes'])}")
        print(f"  Methods: {len(self.project_definitions['all_methods'])}")

    def _collect_definitions_from_tree(self, tree, file_path: str):
        """AST에서 정의 수집"""
        current_class = None

        for path, node in tree:
            # 패키지 선언
            if isinstance(node, javalang.tree.PackageDeclaration):
                self.project_definitions['packages'].add(node.name)

            # 클래스/인터페이스/Enum 선언
            elif isinstance(node, (javalang.tree.ClassDeclaration,
                                  javalang.tree.InterfaceDeclaration,
                                  javalang.tree.EnumDeclaration)):
                current_class = node.name
                self.project_definitions['classes'].add(node.name)

                # 메서드와 필드를 저장할 공간 초기화
                if current_class not in self.project_definitions['methods']:
                    self.project_definitions['methods'][current_class] = set()
                if current_class not in self.project_definitions['fields']:
                    self.project_definitions['fields'][current_class] = set()

            # 메서드 선언
            elif isinstance(node, javalang.tree.MethodDeclaration):
                if current_class:
                    self.project_definitions['methods'][current_class].add(node.name)
                    self.project_definitions['all_methods'].add(node.name)

                    # main 메서드 감지
                    if node.name == 'main':
                        self.main_class = current_class

                    # 리턴 타입 저장
                    if node.return_type:
                        return_type = self._get_type_name(node.return_type)
                        if return_type:
                            self.type_info['method_returns'][node.name] = return_type

            # 필드 선언
            elif isinstance(node, javalang.tree.FieldDeclaration):
                if current_class:
                    field_type = self._get_type_name(node.type)
                    for declarator in node.declarators:
                        self.project_definitions['fields'][current_class].add(declarator.name)
                        if field_type:
                            self.type_info['fields'][declarator.name] = field_type

    def _get_type_name(self, type_node) -> Optional[str]:
        """타입 노드에서 타입 이름 추출"""
        if type_node is None:
            return None

        if hasattr(type_node, 'name'):
            return type_node.name

        # ReferenceType의 경우
        if isinstance(type_node, javalang.tree.ReferenceType):
            return type_node.name

        # BasicType의 경우
        if isinstance(type_node, javalang.tree.BasicType):
            return type_node.name

        return None

    # ========================================================================
    # Phase 2: 타입 정보 수집
    # ========================================================================

    def collect_type_information(self):
        """변수 및 파라미터의 타입 정보 수집"""
        for file_path in self.files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    source_code = file.read()

                tree = javalang.parse.parse(source_code)
                self._collect_type_from_tree(tree)

            except Exception as e:
                pass  # 이미 1단계에서 에러 출력함

    def _collect_type_from_tree(self, tree):
        """AST에서 타입 정보 수집"""
        for path, node in tree:
            # 로컬 변수 선언
            if isinstance(node, javalang.tree.LocalVariableDeclaration):
                var_type = self._get_type_name(node.type)
                if var_type:
                    for declarator in node.declarators:
                        self.type_info['variables'][declarator.name] = var_type

            # 메서드 파라미터는 이미 1단계에서 처리 가능하지만
            # 더 상세한 정보가 필요하면 여기서 처리
            elif isinstance(node, javalang.tree.MethodDeclaration):
                if node.parameters:
                    param_list = []
                    for param in node.parameters:
                        param_type = self._get_type_name(param.type)
                        param_list.append((param.name, param_type))
                        if param_type:
                            self.type_info['variables'][param.name] = param_type
                    self.type_info['method_params'][node.name] = param_list

        print(f"  Variables tracked: {len(self.type_info['variables'])}")
        print(f"  Fields tracked: {len(self.type_info['fields'])}")

    # ========================================================================
    # Phase 3: Import 분석
    # ========================================================================

    def analyze_imports(self):
        """Import 문 분석하여 외부 클래스 식별"""
        for file_path in self.files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    source_code = file.read()

                imports = {}
                lines = source_code.splitlines()

                for line in lines:
                    if line.strip().startswith('import'):
                        match = re.match(r'import\s+(static\s+)?([\w\.]+(\*)?);', line)
                        if match:
                            full_package = match.group(2)
                            class_name = full_package.split('.')[-1]

                            # 프로젝트 내부 패키지인지 확인
                            is_internal = any(
                                full_package.startswith(pkg)
                                for pkg in self.project_definitions['packages']
                            )

                            # 명시적 외부 패키지인지 확인
                            is_explicit_external = any(
                                full_package.startswith(pkg)
                                for pkg in self.external_pkg
                            )

                            imports[class_name] = full_package

                            # 외부 클래스 등록
                            if not is_internal or is_explicit_external:
                                self.external_classes.add(class_name)

                self.imports_by_file[file_path] = imports

            except Exception as e:
                pass

        print(f"  External classes identified: {len(self.external_classes)}")

    # ========================================================================
    # Phase 4: 핵심 - 자동 분류 로직
    # ========================================================================

    def is_external_identifier(self, identifier: str, context_class: Optional[str] = None) -> bool:
        """
        식별자가 외부 것인지 자동으로 판단

        Returns:
            True: 외부 식별자 (난독화 제외)
            False: 내부 식별자 (난독화 OK)
        """
        # 1. Java 내장 타입/클래스
        if identifier in self.JAVA_BUILTIN_TYPES:
            return True

        # 2. Java 표준 인터페이스 메서드
        if identifier in self.JAVA_INTERFACE_METHODS:
            return True

        # 3. 보호 대상 메서드
        if identifier in self.PROTECTED_METHODS:
            return True

        # 4. 프로젝트 내 정의된 클래스
        if identifier in self.project_definitions['classes']:
            return False  # 내부 클래스 → 난독화 OK (주의: 클래스명은 일반적으로 난독화 안 함)

        # 5. 명시적으로 식별된 외부 클래스
        if identifier in self.external_classes:
            return True

        # 6. 컨텍스트 클래스의 메서드인지 확인
        if context_class and context_class in self.project_definitions['methods']:
            if identifier in self.project_definitions['methods'][context_class]:
                return False  # 현재 클래스의 메서드 → 난독화 OK

        # 7. 프로젝트 전체에서 정의된 메서드인지 확인
        if identifier in self.project_definitions['all_methods']:
            return False  # 내부 메서드 → 난독화 OK

        # 8. 모든 클래스의 필드 확인
        for class_fields in self.project_definitions['fields'].values():
            if identifier in class_fields:
                return False  # 내부 필드 → 난독화 OK

        # 9. 위 모든 경우가 아니면 → 외부로 간주
        return True

    def is_android_component_class(self, class_name: str) -> bool:
        """
        클래스가 안드로이드 컴포넌트 또는 보호 대상인지 확인

        Returns:
            True: 난독화 제외 (컴포넌트 or 보호 대상)
            False: 일반 클래스 (난독화 OK)
        """
        # 보호 대상 클래스 (R, BuildConfig 등)
        if class_name in self.PROTECTED_CLASSES:
            return True

        # 안드로이드 프로젝트가 아니면 나머지는 난독화 가능
        if not self.is_android_project:
            return False

        # 클래스명이 안드로이드 컴포넌트 서픽스로 끝나는지 확인
        for suffix in self.ANDROID_COMPONENT_SUFFIXES:
            if class_name.endswith(suffix):
                return True

        return False

    def should_obfuscate_method_call(self, qualifier: str, method_name: str) -> bool:
        """
        메서드 호출이 난독화 대상인지 판단
        예: obj.method() → obj의 타입이 외부면 method도 외부

        Returns:
            True: 난독화 OK
            False: 난독화 제외 (외부)
        """
        # 1. 메서드명 자체가 외부면 제외
        if self.is_external_identifier(method_name):
            return False

        # 2. Qualifier의 타입 확인
        qualifier_type = self.type_info['variables'].get(qualifier) or \
                        self.type_info['fields'].get(qualifier)

        if qualifier_type:
            # 타입이 프로젝트 내 정의된 클래스인가?
            if qualifier_type in self.project_definitions['classes']:
                # 내부 클래스 → 메서드가 이 클래스에 정의되어 있는지 확인
                if method_name in self.project_definitions['methods'].get(qualifier_type, set()):
                    return True  # 내부 메서드 → 난독화 OK
                else:
                    return False  # 정의 안 됨 → 외부 (상속받은 메서드 등)
            else:
                # 외부 타입 → 모든 메서드 제외
                return False

        # 3. 타입 정보가 없으면 보수적으로 판단
        # Qualifier 자체가 외부 클래스면 제외
        if qualifier in self.external_classes or qualifier in self.JAVA_BUILTIN_TYPES:
            return False

        # 4. 메서드가 프로젝트에서 정의되었으면 난독화
        if method_name in self.project_definitions['all_methods']:
            return True

        # 5. 그 외에는 안전하게 제외
        return False

    # ========================================================================
    # Phase 5: 난독화 맵 생성
    # ========================================================================

    def build_obfuscation_map(self):
        """스마트하게 난독화 맵 생성"""
        obfuscated_count = 0
        protected_count = 0

        for file_path in self.files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    source_code = file.read()

                tree = javalang.parse.parse(source_code)
                current_class = None

                for path, node in tree:
                    # 클래스 난독화
                    if isinstance(node, (javalang.tree.ClassDeclaration,
                                        javalang.tree.InterfaceDeclaration,
                                        javalang.tree.EnumDeclaration)):
                        current_class = node.name

                        # 안드로이드 컴포넌트 클래스는 보호
                        if self.is_android_component_class(node.name):
                            protected_count += 1
                        # Main 클래스는 보호 (엔트리 포인트)
                        elif node.name == self.main_class:
                            protected_count += 1
                        else:
                            # 일반 클래스는 난독화
                            self.generate_obfuscated_name(node.name)
                            obfuscated_count += 1

                    # 메서드 난독화
                    elif isinstance(node, javalang.tree.MethodDeclaration):
                        # @Override 메서드는 제외
                        if node.annotations and any(ann.name == "Override" for ann in node.annotations):
                            protected_count += 1
                            continue

                        # 외부 API 멤버 이름은 제외 (충돌 방지)
                        if node.name in self.EXTERNAL_API_MEMBERS:
                            protected_count += 1
                            continue

                        if self.is_external_identifier(node.name, current_class):
                            protected_count += 1
                        else:
                            self.generate_obfuscated_name(node.name)
                            obfuscated_count += 1

                        # 파라미터 난독화
                        for param in node.parameters:
                            # 외부 API 멤버 이름은 제외 (충돌 방지)
                            if param.name in self.EXTERNAL_API_MEMBERS:
                                protected_count += 1
                                continue
                            self.generate_obfuscated_name(param.name)
                            obfuscated_count += 1

                    # 변수 난독화
                    elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                        for declarator in node.declarators:
                            # 외부 API 멤버 이름은 제외 (충돌 방지)
                            if declarator.name in self.EXTERNAL_API_MEMBERS:
                                protected_count += 1
                                continue
                            self.generate_obfuscated_name(declarator.name)
                            obfuscated_count += 1

                    # 필드 난독화
                    elif isinstance(node, javalang.tree.FieldDeclaration):
                        # R 클래스나 BuildConfig 클래스의 필드는 보호
                        if current_class in self.PROTECTED_CLASSES:
                            protected_count += len(node.declarators)
                            continue

                        for declarator in node.declarators:
                            # 외부 API 멤버 이름은 제외 (충돌 방지)
                            if declarator.name in self.EXTERNAL_API_MEMBERS:
                                protected_count += 1
                                continue
                            self.generate_obfuscated_name(declarator.name)
                            obfuscated_count += 1

            except Exception as e:
                pass

        print(f"  Identifiers to obfuscate: {obfuscated_count}")
        print(f"  Identifiers protected: {protected_count}")

    def generate_obfuscated_name(self, name: str, length: int = 8):
        """난독화된 이름 생성 (기존 로직 유지)"""
        if name in self.identifier_map:
            return  # 이미 생성됨

        # 변수/파라미터/필드는 is_external_identifier() 체크 안 함
        # (호출하는 쪽에서 이미 결정함)

        ran = self.ran

        while True:
            if ran == 0:
                obfuscated_name = (''.join(secrets.choice(["l", "I"])) +
                                  ''.join(self.choose_chars(['l', '1', 'I'], length)))
            elif ran == 1:
                obfuscated_name = (''.join(secrets.choice(['O', 'o'])) +
                                  ''.join(self.choose_chars(['0', 'O', 'o'], length)))

            if obfuscated_name not in self.identifier_map.values():
                self.identifier_map[name] = obfuscated_name
                break

    def choose_chars(self, random_list, k):
        """랜덤 문자 선택"""
        return [secrets.choice(random_list) for _ in range(k)]

    # ========================================================================
    # Phase 6: 난독화 적용
    # ========================================================================

    def apply_obfuscation(self):
        """난독화 적용 (기존 로직 재사용)"""
        # 이 부분은 기존 ob_identifier의 obfuscate_java_file과
        # replace_identifiers_in_code를 그대로 사용할 수 있습니다.
        # 여기서는 간략하게 표현

        for file_path in self.files:
            print(f"  Obfuscating: {os.path.basename(file_path)}")
            self.obfuscate_java_file(file_path)

        # 파일명 매핑을 JSON으로 저장
        mapping_file = os.path.join(self.output_folder, 'identifier_mapping.json')
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.file_mapping, f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] File mapping saved to: {mapping_file}")

    def obfuscate_java_file(self, file_path: str):
        """파일에 난독화 적용 (기존 로직 간소화 버전)"""
        with open(file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()

        # 난독화 적용
        obfuscated_code = self.replace_identifiers(source_code)

        # 파일 저장
        class_name = os.path.splitext(os.path.basename(file_path))[0]
        obfuscated_class_name = self.identifier_map.get(class_name, class_name)

        relative_path = os.path.relpath(file_path, self.folder_path)
        output_path = os.path.join(
            self.output_folder,
            os.path.dirname(relative_path),
            f"{obfuscated_class_name}.java"
        )

        # 파일명 매핑 저장 (원본 → 난독화)
        self.file_mapping[file_path] = output_path

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.remove(file_path)

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(obfuscated_code)

    def _is_protected_qualifier(self, qualifier: str) -> bool:
        """
        qualifier가 보호 대상인지 확인
        - R, BuildConfig, Log, Message 등 외부 클래스
        - R 내부 클래스 (id, layout 등)
        """
        if qualifier is None:
            return False

        return (
            qualifier in self.PROTECTED_CLASSES or
            qualifier in self.R_INNER_CLASSES or
            qualifier in self.KNOWN_EXTERNAL_CLASSES or
            qualifier in self.external_classes or
            qualifier in self.JAVA_BUILTIN_TYPES
        )

    def _replace_with_context_check(self, code: str) -> str:
        """
        컨텍스트를 확인하면서 식별자 치환
        - qualifier.identifier 형태에서 qualifier가 보호 대상이면 치환 안 함
        - 예: R.id → 치환 안 함 (R이 보호 대상)
        - 예: Log.d → 치환 안 함 (Log가 보호 대상)
        - 예: int id = 5 → 치환 (독립적 사용)
        """
        for identifier, obfuscated in self.identifier_map.items():
            # (선택적 qualifier.)identifier 패턴 매칭
            # (?:...)? : non-capturing group, optional
            pattern = r'(?:(\w+)\s*\.\s*)?\b' + re.escape(identifier) + r'\b'

            def replace_func(match):
                qualifier = match.group(1)  # 있으면 qualifier, 없으면 None

                # qualifier가 보호 대상이면 치환 안 함
                if self._is_protected_qualifier(qualifier):
                    return match.group(0)  # 원본 그대로

                # 독립적이거나 내부 클래스 멤버면 난독화
                if qualifier is None:
                    # 독립적 사용 (예: int id = 5)
                    return obfuscated
                else:
                    # 내부 클래스 멤버 (예: myObj.id)
                    # qualifier가 보호 대상이 아니므로 치환
                    return match.group(0).replace(identifier, obfuscated)

            code = re.sub(pattern, replace_func, code)

        return code

    def replace_identifiers(self, source_code: str) -> str:
        """식별자 치환 (기존 로직 통합 버전)"""
        lines = source_code.splitlines()
        start_package = True

        for i, line in enumerate(lines):
            # 패키지 선언은 스킵
            if line.strip().startswith("package"):
                if start_package:
                    start_package = False
                    continue

            # Import 처리: 내부 패키지는 난독화, 외부는 그대로
            if line.strip().startswith('import'):
                package_match = re.match(r'import\s+(static\s+)?([\w\.]+(\*)?);', line)
                if package_match:
                    package_name = package_match.group(2)

                    # 내부 패키지인지 확인
                    is_internal = any(
                        package_name.startswith(pkg)
                        for pkg in self.project_definitions['packages']
                    )

                    if is_internal:
                        # 내부 패키지의 클래스명도 난독화
                        class_name = package_name.split('.')[-1]
                        if class_name in self.identifier_map:
                            obfuscated = self.identifier_map[class_name]
                            line = line.replace(class_name, obfuscated)

                lines[i] = line
                continue

            # 어노테이션 내부는 난독화 안 함 (사용자 정의 어노테이션 제외)
            if line.strip().startswith("@"):
                # 기존 로직 유지
                lines[i] = line
                continue

            # getMethod() 리플렉션: 메서드명 문자열도 난독화
            get_method_matches = re.finditer(r'getMethod\("([A-Za-z_]\w*)"', line)
            for match in get_method_matches:
                method_name_literal = match.group(1)
                if method_name_literal in self.identifier_map:
                    obfuscated = self.identifier_map[method_name_literal]
                    line = line.replace(f'"{method_name_literal}"', f'"{obfuscated}"')

            # 문자열 리터럴과 제네릭 분리 (이스케이프 문자 고려)
            parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|<[^>]*>)', line)

            for j, part in enumerate(parts):
                # 문자열 리터럴은 그대로
                if part.startswith('"') or part.startswith("'"):
                    continue

                # 제네릭 내부도 난독화 (<Password> → <난독화된이름>)
                if part.startswith('<'):
                    # < > 안의 내용만 추출해서 난독화
                    if self.identifier_map:
                        part = self._replace_with_context_check(part)
                    parts[j] = part
                    continue

                # 코드 부분 난독화 (컨텍스트 확인)
                if self.identifier_map:
                    part = self._replace_with_context_check(part)

                parts[j] = part

            lines[i] = ''.join(parts)

        return '\n'.join(lines)


# 기존 인터페이스 호환성을 위한 래퍼
class ob_identifier(SmartIdentifierObfuscator):
    """기존 코드 호환성을 위한 래퍼 클래스"""
    pass


if __name__ == '__main__':
    import sys
    ob_identifier(sys.argv[1], sys.argv[1])
