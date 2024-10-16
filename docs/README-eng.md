# TaintBomb auto Java Obfuscator by GoForIt
![TaintBombLogo](../.idea/icon.png)

<!-- Plugin description -->
Taint Bomb is an one click IntelliJ plugin obfuscator, with light but strong obfuscate feature. It analysis project's source codes with Taint Analysis and set obfuscate level by auto defined sensitivity.

---
Taint Bomb은 IntelliJ에서 작동하는 원클릭 난독화 플러그인입니다. 가볍지만 강력한 난독화 기능을 지원하며, Taint 분석을 통해 자동으로 코드의 민감도를 식별하고 그에 기반하여 부분 난독화를 진행합니다.
<!-- Plugin description end -->

# Usage
- Install jar file of plugin to intelliJ.
- Open the project to obfuscate on intelliJ, open Taint-Bomb window and click Obfuscate button.
- 'obfuscated_project_folder' will be created in the project folder, and it contains obfuscated project code, result.txt contains Taint-Analysis result, and obfuscated project's jar build file is in build/libs.

## Caution
- Before usage, please make sure that all overriding methods has @Override annotation.


# Dependencies
## For Plugin
- python : version 3.6 or later
- intelliJ : version 2023.2.7 or later

## Obfuscatable Project
- Java SE 8
  - The code syntax must be fit in this doc http://docs.oracle.com/javase/specs/jls/se8/html/
 
- gradle : 8.0 or later
    - jar properties must be defined in build.gradle.

# Develop Document
## How to Build
- Clone the project and debug with 'Run IDE for UI Test' debug menu.
- You can build jar file by running 'gradle jar' task.

## kotlin/services
- ManageBuild : Manages building tasks.
- ManageHash : Manages hash tasks.
- ManageObfuscate : Manages obfuscation tasks.
- ManagePreTask : Manages pre-task before obfuscation.
- TasksManager : Manages all tasks of plugin.
- TaintBombService : Plugin's main service.

## kotlin/toolWindow
- MyConsoleLogger : 디버깅을 위한 콘솔 로거입니다.
- MyConsoleViewer : 사용자를 위한 콘솔 로거입니다.
- TaintBombFactory : 플러그인의 메인 툴 윈도우입니다.

## resources/pyscipts
### Code Analysis
- analysisResultManager.py : A class that outputs Taint analysis results in Json.
- methodEndLineFinder.py : A class that finds the end of a method.
- sensitivityDB.py : A class that defines sensitivity levels.
- taintAnalysis.py : Analyzes the project with Taint analysis. If there is no Source/Sink flow in the project, nothing will be output
- makeMD.py : print analysis result as markdown file
### Obfuscation
#### Comment Remove
- removeComments.py : Removes comments from all .java files in the project.
#### String Obfuscate
- stringObfuscate.py : A script that performs string obfuscation.
- stringSearch.py : A script that finds strings in the project.
- stringEncrypt.py : A script that encrypts found strings.
- stringInsert.py : Inserts encrypted strings, changes string calls to decrypted string calls, and inserts decryption code into randomly selected classes.
- keyObfuscate.py : Encrypts the key for string encryption.
#### Operator Obfuscate
- operationDB.py : Operator database for operator obfuscation.
- operationExtract.py : Extracts operators from files.
- operationObfuscate.py : Obfuscates extracted operators.
#### Identifier Obfuscate
- identifierObfuscate.py : Obfuscated identifiers.
### Plugin
- applyObfuscated.py : A class that applies obfuscated code to a file.
- levelObfuscate.py : A class that performs obfuscation by sensitivity level.
- obfuscateTool.py : A class that contains functions which are commonly used in multiple scripts.
- checkJavaSyntax.py : Check project's java syntax error.
- intallScripts.py : Install required python libraries
- check_hash :  Contains hash information of all .py files under the pyscript folder.
- create_hash.py : When executed, it saves the hash information of all .py files under the pyscript folder to check_hash.

## resource/java
- keyDecrypt.java : a class that decrypts the key for string encryption.
- stringDecrypt.java : a class that decrypts the encrypted string.


