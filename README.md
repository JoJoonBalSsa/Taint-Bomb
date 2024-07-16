# TaintBomb Obfuscator by GoForIt
![TaintBombLogo](./src/main/resources/META-INF/pluginicon.svg)

<!-- Plugin description -->
Taint Bomb is an one click IntelliJ plugin obfuscator, with light but strong obfuscate feature. It analysis project's source codes with Taint Analysis and set obfuscate level by auto defined sensitivity.

---
Taint Bomb은 IntelliJ에서 작동하는 원클릭 난독화 플러그인입니다. 가볍지만 강력한 난독화 기능을 지원하며, Taint 분석을 통해 자동으로 코드의 민감도를 식별하고 그에 기반하여 부분 난독화를 진행합니다.
<!-- Plugin description end -->

# resources/pyscipts
- check_hash :  pyscript 폴더 밑의 모든 .py 파일의 해시 정보가 저장되어있습니다.
- create_hasy.py : 실행하면 pyscript 폴더 밑의 모든 .py 파일의 해시 정보를 check_hash에 저장합니다.
- removeComments : 프로젝트의 모든 .java 파일에서 주석을 제거합니다.
- taintAnalysis : 프로젝트를 taint 분석합니다.

# services/RunPyScripts.kt
- readHashInfo() : check_hash 파일을 읽어와 리스트에 저장합니다.
- copyScripts() : check_hash 리스트에 존재하는 pyscripts 밑의 파일을 시스템 tmp폴더 밑에 복사합니다.
- compareFileHashes() : tmp폴더 밑의 스크립트들의 해시값을 검증합니다.
- executePythonScript() : main 스크립트를 실행합니다.
- deleteTempFiles() : tmp폴더 밑에 생성되었던 스크립트들을 삭제합니다.
