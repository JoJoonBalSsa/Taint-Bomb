# TaintBomb Obfuscator by GoForIt
![TaintBombLogo](./src/main/resources/META-INF/pluginicon.svg)

<!-- Plugin description -->
Taint Bomb is an one click IntelliJ plugin obfuscator, with light but strong obfuscate feature. It analysis project's source codes with Taint Analysis and set obfuscate level by auto defined sensitivity.

---
Taint Bomb은 IntelliJ에서 작동하는 원클릭 난독화 플러그인입니다. 가볍지만 강력한 난독화 기능을 지원하며, Taint 분석을 통해 자동으로 코드의 민감도를 식별하고 그에 기반하여 부분 난독화를 진행합니다.
<!-- Plugin description end -->

# Usage
- Install jar file of plugin to intelliJ.
- Open the project to obfuscate on intelliJ, open Taint-Bomb window and click Obfuscate button.
- 'obfuscated_project_folder' will be created in the project folder, and it contains obfuscated project code, result.txt contains Taint-Analysis result, and obfuscated project's jar build file is in build/libs.

# Develop Document
## How to Build
- Clone the project and debug with 'Run IDE for UI Test' debug menu.
- You can build jar file by running 'gradle jar'.

## resources/pyscipts
- main.py : is main script that all scripts are executed.
- obfuscateTool.py : is a class that contains functions commonly used in multiple scripts.
- check_hash : contains hash information of all '.py' files under the pyscript folder.
- create_hasy.py : saves hash information of all '.py' files under the pyscript folder to check_hash. Should be executed after adding or editing python scripts.
- taintAnalysis : performs taint analysis on the project. If there is no Source/Sink flow in the project, nothing will be output.
- removeComments : removes comments from all '.java' files in the project.
- stringObfuscate : script that performs string obfuscation.
- stringSearch : script that finds strings in the project.
- stringEncrypt : script that encrypts found strings.
- stringInsert : inserts encrypted strings, changes string calls to decrypted string calls, and inserts decryption code into randomly selected classes.
- keyObfuscate : encrypts the key for string encryption.

## resource/java
- keyDecrypt.java : a class that decrypts the key for string encryption.
- stringDecrypt.java : a class that decrypts the encrypted string.

## services/RunPyScripts.kt
- readHashInfo() : is a method that reads the check_hash file and saves it to a list.
- copyScripts() : is a method that copies files under the pyscripts folder to the system tmp folder.
- compareFileHashes() : is a method that verifies the hash values of the scripts under the tmp folder.
- executePythonScript() : is a method that executes the main script.
- runGradle() : is a method that builds a jar file using Gradle. jar properties must be defined in build.gradle.
- deleteTempFiles() : is a method that deletes the scripts created under the tmp folder.


