# Taint Bomb auto Java Obfuscator by JoJoonBalSsa!

---


<div style="text-align: center;"><img src="../.idea/icon.png" width="600px" height="600px" alt="Taint Bomb logo"></div>


####
<div style="text-align: center">
  <a href="https://github.com/JoJoonBalSsa/Taint-Bomb/releases"><img src="https://img.shields.io/github/release/JoJoonBalSsa/Taint-Bomb.svg" width="100px"></a>
  <img alt="JetBrains Plugin Downloads" src="https://img.shields.io/jetbrains/plugin/d/25629" width="100px">
  <img alt="JetBrains Plugin Rating" src="https://img.shields.io/jetbrains/plugin/r/rating/25629" width="90px">
</div>
<div style="text-align: center">
  <a href="https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator">
    <div><img alt="Get from marketplace" src=".././docs/getFromMarketplace.png" width="500px"></div>
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
  <a href="/docs/README-eng.md">
    <div style="font-size:130%">🇰🇷 한글 문서</div>
  </a>
</div>

# Usage

---

- Install plugin to IntelliJ.
  - Check [GitHub Releases](https://github.com/JoJoonBalSsa/Taint-Bomb/releases) or [IntelliJ marketplace](https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator)
- Open the project to obfuscate on IntelliJ, open Taint Bomb window and click Obfuscate button.
- 'obfuscated_project_folder' will be created in the project folder. It contains obfuscated project code and built jar file. And 'analysis_result.md' contains Taint-Analysis result.

## Caution

---

- Before usage, please make sure that all overriding methods has @Override annotation.
- The project with test code may not be obfuscated properly.

# Dependencies

---

## For Plugin
- python : version 3.7 or later
- IntelliJ : version 2023.3 or later
- Windows, macOS, linux is supported

## Obfuscatable Project
- Java SE 8
  - The code syntax must be fit with this doc http://docs.oracle.com/javase/specs/jls/se8/html/
- gradle 8.0 or later
    - jar properties must be defined in build.gradle.
- maven 3.9 or later

# Develop Document

---

## How to Build
- You can build plugin by running gradle task 'build'.
- After editing python scripts, run 'Create Hash' task to update 'check_hash' file which contains all hash information of python scripts under '/src/main/resources/pyscripts'.
- Debug with 'Run Plugin' task.

## kotlin/services
- ManageBuild : Manages building tasks.
- ManageHash : Manages hash tasks.
- ManageObfuscate : Manages obfuscation tasks.
- ManagePreTask : Manages pre-task before obfuscation.
- TasksManager : Manages all tasks of plugin.
- TaintBombService : Plugin's main service.

## kotlin/toolWindow
- MyConsoleLogger : Console logger for debug.
- MyConsoleViewer : Console logger for User.
- TaintBombFactory : Main ToolWindow of plugin.

## resources/pyscipts
### Plugin

---

- applyObfuscated.py : A class that applies obfuscated code to a file.
- levelObfuscate.py : A class that performs obfuscation by sensitivity level.
- obfuscateTool.py : A class that contains functions which are commonly used in multiple scripts.
- checkJavaSyntax.py : Checks project's java syntax error with 'javalang parser'.
- intallScripts.py : Install required python libraries for plugin.
- create_hash.py : When executed, it saves the hash information of all .py files under the pyscript folder to check_hash.
- check_hash :  Contains hash information of all .py files under the pyscript folder.

### Code Analysis

---

- analysisResultManager.py : A class that outputs Taint analysis results in Json.
- methodEndLineFinder.py : A class that finds the end of a method.
- sensitivityDB.py : A class that defines sensitivity levels.
- taintAnalysis.py : Analyzes the project with Taint analysis. 
- makeMD.py : Prints analysis result as markdown file. If there is no Source/Sink flow in the project, nothing will be there.

### Obfuscation

---

#### Comment Remove
- removeComments.py : Removes comments from all .java files in the project.
#### String Obfuscate
- stringObfuscate.py : A script that performs string obfuscation.
- stringSearch.py : A script that finds strings in the project.
- stringEncrypt.py : A script that encrypts found strings.
- stringInsert.py : Inserts encrypted strings, changes string calls to decrypted string calls, and inserts decryption code into randomly selected classes.
- keyObfuscate.py : Encrypts the key for string encryption.
#### Conditinal / loop state's operator Obfuscate
- operationDB.py : Operator database for operator obfuscation.
- operationExtract.py : Extracts operators from files.
- operationObfuscate.py : Obfuscates extracted operators.
#### Identifier Obfuscate
- identifierObfuscate.py : Obfuscated identifiers.
#### DummyCode Insertion
- dumbDB.py : Dummy-codes database.
- dummyInsert.py : A class inserts dummy-codes in project codes.
#### Method split
- methodSplit.py : A class that splits methods.

## resource/java

---

- keyDecrypt.java : a class that decrypts the key for string encryption.
- stringDecrypt.java : a class that decrypts the encrypted string.


