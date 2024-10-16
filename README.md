# Taint Bomb auto Java Obfuscator by GoForIt
![TaintBombLogo](./.idea/icon.png)

<!-- Plugin description -->
Taint Bomb is an one click IntelliJ plugin obfuscator, with light but strong obfuscate feature. It analysis project's source codes with Taint Analysis and set obfuscate level by auto defined sensitivity.

---
Taint Bomb은 IntelliJ에서 작동하는 원클릭 난독화 플러그인입니다. 가볍지만 강력한 난독화 기능을 지원하며, Taint 분석을 통해 자동으로 코드의 민감도를 식별하고 그에 기반하여 부분 난독화를 진행합니다.
<!-- Plugin description end -->

<a href="/docs/README-eng.md">English Docs</a>

# Usage
- 플러그인의 jar 파일을 intelliJ에 설치합니다.
- 난독화 할 프로젝트를 intelliJ에서 열고, Taint-Bomb 창을 열어 Obfuscate 버튼을 클릭합니다.
- 프로젝트 폴더 내에 'obfuscated_project_folder' 가 생성되며, 내부에는 난독화된 프로젝트 코드가, result.txt에는 Taint-Analysis 결과가, build/libs 내부에는 난독화된 프로젝트의 jar 빌드 파일이 존재합니다.

[주의 사항]
- 난독화 전 프로젝트의 모든 override함수에 @Override 어노테이션이 붙어있어야 합니다.

# Dependencies
## 플러그인
- python 3.6 이상
- intelliJ : 2023.2.7 이상

## 난독화 대상 프로젝트
- 난독화 전 프로젝트의 모든 override함수에 @Override 어노테이션이 붙어있어야 합니다.
- Java SE 8 지원
  - 다음 문서에 해당하는 문법을 가져야 합니다. http://docs.oracle.com/javase/specs/jls/se8/html/
- gradle 8.0 이상
  - build.gradle에서 jar 속성이 정의되어 있어야 합니다.

# Develop Document
## How to Build
- 디버깅 : 프로젝트를 클론해 'Run IDE for UI Test' 로 디버깅합니다.
- 빌드 : gradle 메뉴에서 jar을 실행합니다.

## kotlin/services
- ManageBuild : 프로젝트의 빌드를 관리합니다.
- ManageHash : pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 관리합니다.
- ManageObfuscate : 난독화를 관리합니다.
- ManagePreTask : 난독화 전 사전 작업을 관리합니다.
- TasksManager : 플러그인의 모든 작업을 관리합니다.
- TaintBombService : 플러그인의 메인 서비스입니다.

## kotlin/toolWindow
- MyConsoleLogger : 디버깅을 위한 콘솔 로거입니다.
- MyConsoleViewer : 사용자를 위한 콘솔 로거입니다.
- TaintBombFactory : 플러그인의 메인 툴 윈도우입니다.

## resources/pyscipts
### 코드 분석
- analysisResultManager.py : Taint 분석 결과를 Json으로 출력하는 클래스입니다.
- methodEndLineFinder.py : 메소드의 끝을 찾아주는 클래스입니다.
- sensitivityDB.py : 민감도 레벨을 정의하는 클래스입니다.
- taintAnalysis.py : 프로젝트를 taint 분석합니다. 프로젝트에 Source/Sink 흐름이 없다면 아무 것도 출력되지 않습니다.
- makeMD.py : 프로젝트의 taint 분석 결과를 md 파일로 출력합니다.
- 
### 난독화
#### 주석 제거
- removeComments.py : 프로젝트의 모든 .java 파일에서 주석을 제거합니다.
#### 문자열 난독화
- stringObfuscate.py : 문자열 난독화를 실행하는 스크립트입니다.
- stringSearch.py : 프로젝트에서 문자열을 찾아내는 스크립트입니다.
- stringEncrypt.py : 찾은 문자열들을 암호화하는 스크립트입니다.
- stringInsert.py : 암호화된 문자열을 삽입하고, 문자열 호출을 복호화된 문자열 호출로 변경하고, 복호화 코드를 랜덤으로 선택한 클래스에 삽입합니다.
- keyObfuscate.py : 문자열 암호화의 키를 암호화합니다.
#### 연산자 난독화
- operationDB.py : 연산자 난독화를 위한 연산자 데이터베이스입니다.
- operationExtract.py : 파일에서 연산자를 추출합니다.
- operationObfuscate.py : 추출한 연산자를 난독화합니다.
#### 식별자 난독화
- identifierObfuscate.py : 식별자 난독화를 실행하는 스크립트입니다.
### Plugin
- applyObfuscated.py : 민감도 레벨별로 난독화된 코드를 파일에 적용하는 클래스입니다.
- levelObfuscate.py : 민감도 레벨별로 난독화를 진행하는 클래스입니다.
- obfuscateTool.py : 여러 스크립트에서 공통적으로 사용되는 함수들을 모아둔 클래스입니다.
- checkJavaSyntax.py : 프로젝트의 모든 .java 파일의 문법을 검사합니다.
- installScripts.py : 플러그인 실행에 필요한 라이브러리를 설치합니다.
- check_hash :  pyscript 폴더 밑의 모든 .py 파일의 해시 정보가 저장되어있습니다.
- create_hash.py : 실행하면 pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 check_hash에 저장합니다.

## resource/java
- keyDecrypt.java : 암호화된 문자열 암호화 키를 복호화하는 클래스입니다.
- stringDecrypt.java : 암호화된 문자열을 복호화하는 클래스입니다.
