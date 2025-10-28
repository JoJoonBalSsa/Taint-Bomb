# Taint Bomb auto Java Obfuscator by JoJoonBalSsa!

---


<div style="text-align: center;"><img src=".idea/icon.png" width="600px" height="600px" alt="Taint Bomb logo"></div>


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
  <a href="./docs/README-KOR.md">
    <div style="font-size:250%">🇰🇷 한국어 문서</div>
  </a>
</div>

# Requirements

## for Plugin

- Internet Connection
  - required when installing python dependencies.
- Python 3.7 or later
- IntelliJ 2023.3 or later
- support Windows, macOS, Linux
- Support AI API of Claude, Chat GPT and Gemini

## for Target Project

- Java SE 8 syntax
  - checkout official docs- <http://docs.oracle.com/javase/specs/jls/se8/html/>

- gradle(8 or later) or maven(3.9 or later)
  - When using gradle, the jar property must be defined in build.gradle.
- checkout Caution

# How to use

1. Install plugin to IntelliJ.
  - install from [GitHub Releases](https://github.com/JoJoonBalSsa/Taint-Bomb/releases) or [IntelliJ marketplace](https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator)
2. Open the target project to obfuscate on IntelliJ, and open Taint Bomb window.
3. Set obfuscation methods and AI api key(optional) on Configuration tab.
4. Click Obfuscate button.
5. 'obfuscated_project_folder' will be created in the project files. It contains obfuscated project code and built jar file. And also Taint-Analysis result(taint_anlaysis.txt & analysis_result.md) and analysis result by AI(llm_analysis_result.md).

## Caution

- Make sure that all overriding methods has @Override annotation.
- If the target project contains test codes, it might not be obfuscated properly.
- If there is no 2 or 3 level of sensitivity in taint analysis result, some obfuscation operation will be skipped.(operator obfuscation, method splitting, dummy code insertion)
