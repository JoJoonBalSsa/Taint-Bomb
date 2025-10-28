# Taint Bomb auto Java Obfuscator by 조준발싸!

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
    <div><img alt="Get from marketplace" src="./getFromMarketplace.png" width="500px"></div>
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
  <a href="../README.md">
    <div style="font-size:250%">🇬🇧🇺🇸 영어 문서</div>
  </a>
</div>

# 요구사항

## 플러그인 요구사항

- 인터넷 연결
  - Python 라이브러리들을 설치하는데 필요합니다.
- Python 3.7 이상
- IntelliJ 2023.3 이상
- Windows, macOS, Linux 지원
- Claude, Chat GPT, Gemini API 키 지원

## 난독화 대상 프로젝트 요구사항

- Java SE 8 문법
  - 공식 문서 참고 - <http://docs.oracle.com/javase/specs/jls/se8/html/>

- gradle(8 이상) or maven(3.9 이상)
  - 그래들 사용시 jar 속성이 build.gradle 안에 정의되어 있어야 합니다.
- 주의사항 참고

# 사용법

1. 플러그인을 IntelliJ에 설치합니다
  - [GitHub Releases](https://github.com/JoJoonBalSsa/Taint-Bomb/releases)에서 설치하거나 [IntelliJ marketplace](https://plugins.jetbrains.com/plugin/25629-taint-bomb-auto-java-obfuscator)에서 설치하세요.
2. 난독화 대상 프로젝트를 IntelliJ에서 연 다음, 좌측 화면에서 Taint Bomb아이콘을 클릭하여 창을 열어주세요.
3. Configuration 탭에서 적용할 난독화 기법, AI api 키(선택사항) 등을 설정해줍니다.
4. Obfuscate 버튼을 클릭합니다.
5. 프로젝트 폴더 내에 난독화 된 프로젝트 폴더인 'obfuscated_project_folder'가 생성됩니다. 내부에는 난독화 된 코드와 빌드가 완료된 jar 파일이 있습니다. 또, Taint 분석 결과(taint_anlaysis.txt & analysis_result.md)와 AI를 사용한 분석 결과(llm_analysis_result.md)가 생성됩니다.

## 주의사항

- 모든 오버라이딩 함수는 @Overide 어노테이션을 포함해야 합니다.
- 난독화 대상 프로젝트가 테스트 코드를 포함하고 있다면 난독화가 제대로 이루어지지 않습니다.
- 분석된 Taint 흐름에 2, 3 단계 민감도가 존재하지 않는다면 일부 난독화 기법은 생략됩니다.(식별자 난독화, 함수 분할, 더미 코드 삽입)
