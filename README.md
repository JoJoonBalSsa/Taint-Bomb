# TaintBomb Obfuscator by GoForIt
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

# Dependencies
## 플러그인
- python 3.6 이상
- pip javalang
- pip pycryptodome
- intelliJ : 2023.2.7 이상

## 난독화 대상 프로젝트
- javalang : 기본적으로 java SE8이나, 다음 문서에 호환되면 됨 http://docs.oracle.com/javase/specs/jls/se8/html/
- gradle : 7.0 이상
  - build.gradle에서 jar 속성이 정의되어있어야 합니다.

# Develop Document
## How to Build
- 디버깅은 프로젝트를 클론해 'Run IDE for UI Test' 로 디버깅합니다.
- 빌드는 gradle 메뉴에서 jar을 실행합니다.

## resources/pyscipts
### Core1
- analysisResultManager.py : Taint 분석 결과를 Json으로 출력하는 클래스입니다.
- methodEndLineFinder.py : 메소드의 끝을 찾아주는 클래스입니다.
- sensitivityDB.py : 민감도 레벨을 정의하는 클래스입니다.
- taintAnalysis.py : 프로젝트를 taint 분석합니다. 프로젝트에 Source/Sink 흐름이 없다면 아무 것도 출력되지 않습니다.
### Core2
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
### Plugin
- main.py : 모든 스크립트가 실행되는 메인 스크립트입니다.
- applyObfuscated.py : 민감도 레벨별로 난독화된 코드를 파일에 적용하는 클래스입니다.
- levelObfuscate.py : 민감도 레벨별로 난독화를 진행하는 클래스입니다.
- obfuscateTool.py : 여러 스크립트에서 공통적으로 사용되는 함수들을 모아둔 클래스입니다.
- check_hash :  pyscript 폴더 밑의 모든 .py 파일의 해시 정보가 저장되어있습니다.
- create_hasy.py : 실행하면 pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 check_hash에 저장합니다.

## resource/java
- keyDecrypt.java : 암호화된 문자열 암호화 키를 복호화하는 클래스입니다.
- stringDecrypt.java : 암호화된 문자열을 복호화하는 클래스입니다.

## services/RunPyScripts.kt
- readHashInfo() : check_hash 파일을 읽어와 리스트에 저장합니다.
- copyScripts() : check_hash 리스트에 존재하는 pyscripts 밑의 파일을 시스템 tmp폴더 밑에 복사합니다.
- compareFileHashes() : tmp폴더 밑의 스크립트들의 해시값을 검증합니다.
- executePythonScript() : main 스크립트를 실행합니다.
- runGradle() : Gradle을 사용하여 jar 파일을 빌드합니다. 
- deleteTempFiles() : tmp폴더 밑에 생성되었던 스크립트들을 삭제합니다.

