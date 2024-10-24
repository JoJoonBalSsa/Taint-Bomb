# Taint Bomb auto Java Obfuscator by 조준발싸!

---


<div style="text-align: center;"><img src="./.idea/icon.png" width="600px" height="600px" alt="Taint Bomb logo"></div>


####
<div style="text-align: center">
  <a href="https://github.com/JoJoonBalSsa/Taint-Bomb/releases"><img src="https://img.shields.io/github/release/JoJoonBalSsa/Taint-Bomb.svg" width="100px"></a>
  <img alt="JetBrains Plugin Downloads" src="https://img.shields.io/jetbrains/plugin/d/25629" width="100px">
  <img alt="JetBrains Plugin Rating" src="https://img.shields.io/jetbrains/plugin/r/rating/25629" width="90px">
</div>

<div style="text-align: center">
  <a href="https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator">
    <div><img alt="Get from marketplace" src="./docs/getFromMarketplace.png" width="500px"></div>
  </a>
</div>

<!-- Plugin description -->
  Taint Bomb is a one click auto Java obfuscator IntelliJ plugin, with light but strong obfuscate feature. It analysis project's source codes with Taint Analysis and set obfuscate level by defined sensitivity.
  If you want to report a bug or request a feature, please feel free to leave an [issue](https://github.com/JoJoonBalSsa/Taint-Bomb/issues).

  ---

  Taint Bomb은 IntelliJ에서 작동하는 원클릭 자동 자바 난독화 플러그인입니다. 가볍지만 강력한 난독화 기능을 지원하며, Taint 분석을 통해 코드의 민감도를 식별하고 그 결과에 기반한 차등적 난독화를 수행합니다.
  버그나 기능 추가를 원하신다면 [이슈](https://github.com/JoJoonBalSsa/Taint-Bomb/issues)를 남겨주세요.
<!-- Plugin description end -->




<div style="text-align: center">
  <a href="./docs/README-eng.md">
    <div style="font-size:130%">🇺🇸 English Docs</div>
  </a>
</div>

# Usage

---

- 플러그인을 IntelliJ에 설치합니다.
  - [GitHub Releases](https://github.com/JoJoonBalSsa/Taint-Bomb/releases)를 확인하거나 [IntelliJ marketplace](https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator)에서 설치합니다.
- 난독화 할 프로젝트를 IntelliJ에서 열고, Taint Bomb 창을 열어 Obfuscate 버튼을 클릭합니다.
- 프로젝트 폴더 내에 'obfuscated_project_folder' 가 생성되며, 내부에는 난독화된 프로젝트 코드와 난독화된 프로젝트의 jar 빌드 파일이, 'analysis_result.md'에는 Taint-Analysis 결과가 존재합니다.

[주의 사항]
- 난독화 전 프로젝트의 모든 override함수에 @Override 어노테이션이 붙어있어야 합니다.
- 테스트 코드가 포함된 프로젝트는 난독화나 빌드가 제대로 이루어지지 않을 수 있습니다.

# Dependencies

---

## 플러그인
- python 3.7 이상
- IntelliJ : 2023.3 이상
- Windows, macOS, linux 지원

## 난독화 대상 프로젝트
- Java SE 8 지원
  - 다음 문서에 해당하는 문법을 가져야 합니다. http://docs.oracle.com/javase/specs/jls/se8/html/
- gradle 8.0 이상
  - build.gradle에 jar 속성이 정의되어 있어야 합니다.
- maven 3.9 이상

# Develop Document

---

## How to Build
- gradle task 'build'로 플러그인 jar을 빌드합니다.
- 파이썬 스크립트를 수정했을 경우 task 'Create Hash' 혹은 create_hash.py를 직접 실행해 /src/main/resources/pyscripts/check_hash 를 갱신해야 합니다.
- task 'Run Plugin'을 통해 디버깅합니다.

## kotlin/services
- ManageBuild : 프로젝트의 빌드를 관리합니다. Gradle과 Maven을 사용합니다.
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
### Plugin

---

- applyObfuscated.py : 민감도 단계별로 난독화된 코드를 파일에 적용하는 스크립트입니다.
- levelObfuscate.py : 코드를 식별된 민감도 단계별 난독화를 진행하는 스크립트입니다.
- obfuscateTool.py : 여러 스크립트에서 공통적으로 사용되는 함수들을 모아둔 클래스입니다.
- checkJavaSyntax.py : 프로젝트의 모든 .java 파일의 문법을 javalang parser로 검사합니다.
- installScripts.py : 플러그인 실행에 필요한 파이썬 라이브러리를 설치합니다.
- create_hash.py : pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 check_hash에 저장합니다.
- check_hash :  pyscript 폴더 밑의 모든 .py 파일의 해시 정보가 저장되어있습니다.

### 코드 분석

---

- analysisResultManager.py : Taint 분석 결과를 Json으로 출력하는 클래스입니다. 프로젝트에 Source/Sink 흐름이 없다면 아무 것도 출력되지 않습니다.
- methodEndLineFinder.py : 메소드의 끝을 찾아주는 클래스입니다.
- sensitivityDB.py : 소스, 싱크 그리고 소스, 싱크의 민감도 단계를 정의하는 클래스입니다.
- taintAnalysis.py : 프로젝트를 taint 분석합니다.
- makeMD.py : 프로젝트의 taint 분석 결과를 md 파일로 출력합니다.

### 난독화

---

#### 주석 제거
- removeComments.py : 프로젝트의 모든 .java 파일에서 주석을 제거합니다.
#### 문자열 난독화
- stringObfuscate.py : 문자열 난독화를 실행하는 클래스입니다.
- stringSearch.py : 프로젝트에서 문자열을 찾아내는 클래스입니다.
- stringEncrypt.py : 찾은 문자열들을 암호화하는 클래스입니다.
- stringInsert.py : 암호화된 문자열을 삽입하고, 문자열 호출을 복호화된 문자열 호출로 변경하고, 복호화 코드를 프로젝트의 클래스에 무작위로 삽입하는 클래스입니다.
- keyObfuscate.py : 문자열 암호화의 키를 암호화하는 클래스입니다.
#### 조건문/반복문 연산자 난독화
- operationDB.py : 연산자 난독화를 위한 연산자 데이터베이스입니다.
- operationExtract.py : 파일에서 연산자를 추출하는 클래스입니다.
- operationObfuscate.py : 추출한 연산자를 난독화하는 클래스입니다.
#### 식별자 난독화
- identifierObfuscate.py : 식별자 난독화를 실행하는 클래스입니다.
#### 더미 코드 삽입
- dumbDB.py : 더미 코드 데이터베이스입니다.
- dummyInsert.py : 더미 코드를 삽입하는 클래스입니다.
#### 함수 분할
- methodSplit.py : 함수 분할 클래스입니다.

## resource/java

---

- keyDecrypt.java : 암호화된 문자열 암호화 키를 복호화하는 메소드입니다.
- stringDecrypt.java : 암호화된 문자열을 복호화하는 메소드입니다.
