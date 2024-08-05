# TaintBomb Obfuscator by GoForIt
![TaintBombLogo](./src/main/resources/META-INF/pluginicon.svg)

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

# Develop Document
## How to Build
- 디버깅은 프로젝트를 클론해 'Run IDE ㄴfor UI Test' 로 디버깅합니다.
- 빌드는 gradle 메뉴에서 jar을 실행합니다.

## resources/pyscipts
- main.py : 모든 스크립트가 실행되는 메인 스크립트입니다.
- obfuscateTool.py : 여러 스크립트에서 공통적으로 사용되는 함수들을 모아둔 클래스입니다.
- check_hash :  pyscript 폴더 밑의 모든 .py 파일의 해시 정보가 저장되어있습니다.
- create_hasy.py : 실행하면 pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 check_hash에 저장합니다.
- taintAnalysis : 프로젝트를 taint 분석합니다. 프로젝트에 Source/Sink 흐름이 없다면 아무 것도 출력되지 않습니다.
- removeComments : 프로젝트의 모든 .java 파일에서 주석을 제거합니다.
- stringObfuscate : 문자열 난독화를 실행하는 스크립트입니다.
- stringSearch : 프로젝트에서 문자열을 찾아내는 스크립트입니다.
- stringEncrypt : 찾은 문자열들을 암호화하는 스크립트입니다.
- stringInsert : 암호화된 문자열을 삽입하고, 문자열 호출을 복호화된 문자열 호출로 변경하고, 복호화 코드를 랜덤으로 선택한 클래스에 삽입합니다.
- keyObfuscate : 문자열 암호화의 키를 암호화합니다.

## resource/java
- keyDecrypt.java : 암호화된 문자열 암호화 키를 복호화하는 클래스입니다.
- stringDecrypt.java : 암호화된 문자열을 복호화하는 클래스입니다.

## services/RunPyScripts.kt
- readHashInfo() : check_hash 파일을 읽어와 리스트에 저장합니다.
- copyScripts() : check_hash 리스트에 존재하는 pyscripts 밑의 파일을 시스템 tmp폴더 밑에 복사합니다.
- compareFileHashes() : tmp폴더 밑의 스크립트들의 해시값을 검증합니다.
- executePythonScript() : main 스크립트를 실행합니다.
- runGradle() : Gradle을 사용하여 jar 파일을 빌드합니다. build.gradle에서 jar 속성이 정의되어있어야 합니다.
- deleteTempFiles() : tmp폴더 밑에 생성되었던 스크립트들을 삭제합니다.

