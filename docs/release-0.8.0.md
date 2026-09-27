# 0.8.0 검증 절차

## 환경과 범위

- 플러그인 빌드/테스트: JDK 17, 저장소의 Gradle Wrapper.
- 호환성 대상: IntelliJ IDEA 2026.3 EAP `263.5153.40`.
- Python 검사: `javalang`, `pycryptodome`. AI 키를 전달하지 않으며 클라우드 AI 분석은 검증 범위에서 제외한다.
- EXIF GUI 실행 검사에는 `xvfb-run`과 `timeout`이 필요하다.
- 난독화 출력에서는 원래 테스트 디렉터리가 제외된다. 따라서 `test NO-SOURCE`를 테스트 성공으로 세지 않고, 아래의 독립 실행 검사로 원본과 난독화 결과를 비교한다.
- 식별자 난독화는 보수적으로 동작한다. 수신 타입이나 멤버의 소속을 확정하지 못하면 해당 이름의 선언과 참조를 함께 보존한다. 일부 이름은 그대로 남을 수 있으며, 안전하게 확인되는 내부 식별자는 계속 난독화한다.
- 연산자 난독화는 조건식에서 타입을 확인할 수 있는 정수/long·boolean 연산을 변환한다. float/double 산술·대소 비교, 타입을 확정하지 못한 산술식, 삼항식·증감·대입/복합대입 대상 등은 원본을 보존한다. 기능을 끄거나 단계 순서를 바꿔 변환을 생략하는 방식은 사용하지 않는다.
- 문자열 분해는 일반 리터럴에 런타임 char-array 인코딩과 interning을 적용하고, 상수성이 필요한 문맥에서는 컴파일 타임 상수 XOR 표현식을 사용한다. 이 상수 표현식은 컴파일러가 접을 수 있으므로 `.class` 파일에서 해당 문자열의 평문이 사라진다고 보장하지 않는다. 상수 연결식과 동적 연결식의 참조 동일성은 별도로 검사한다(Java SE 17 JLS §15.29).
- 제어흐름 평탄화는 지역변수를 메서드 앞으로 옮기지 않는다. 첫 지역변수 선언부터 이어지는 문장들을 하나의 dispatcher case 블록으로 묶어 `final`, 초기화 순서, 스코프와 확정 할당 의미를 유지한다. 선언이 없는 앞부분은 여러 case로 나눈다. 구조적 제어문·중괄호·람다·`var`가 있는 메서드는 기존의 보수적 지원 범위를 유지한다.
- 기능별 격리 검사는 해당 변환만 직접 호출하고 원본/생성 Java를 각각 컴파일·실행한다. 모든 옵션을 꺼도 불투명 조건식이 적용되는 level 경로와 구분한다. 생성 이름 충돌, 생성자 선행 호출, 메서드 분할의 지역변수 증감, 람다의 타입 가림을 회귀 검사에 포함한다.
- AES 문자열 치환은 비BMP 문자를 포함한 실제 소스 리터럴의 끝을 찾아 치환한다. 이스케이프·파일 경로 리터럴의 기존 제외 정책과 OS별 복호화 템플릿은 유지한다. Windows/Android 디코더 지원을 검증하지 않은 Linux 전용 확장은 포함하지 않는다.

## 플러그인 및 회귀 테스트

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
bash ./gradlew --no-daemon --max-workers=2 clean test buildPlugin verifyPluginStructure
python -m unittest discover -s src/test/python -p 'test_*.py' -v
```

Python 스크립트를 수정했다면 패키징 전에 무결성 목록을 갱신한다.

```bash
(cd src/main/resources/pyscripts && python create_hash.py)
```

공식 JetBrains Plugin Verifier JAR와 대상 IDE를 준비한 뒤 실행한다. `VERIFIER_JAR`, `IDE_HOME`, `REPORT_DIR`는 각 로컬 경로다.

```bash
java -Xmx2g -jar "$VERIFIER_JAR" check-plugin build/distributions/*.zip "$IDE_HOME" \
  -verification-reports-dir "$REPORT_DIR" -runtime-dir "$IDE_HOME/jbr"
```

Verifier 종료 코드만으로 판정하지 않는다. 해당 플러그인의 `verification-verdict.txt`가 `Compatible`이고, `deprecated-usages.txt`와 `compatibility-problems.txt`에 내용이 없어야 한다. Gradle `verifyPlugin`에도 deprecated API 실패 조건이 설정되어 있다.

## 대상 저장소 검사

검증 기준 커밋:

| 저장소 | 커밋 |
|---|---|
| `DA2RIM/java-exif-remover` | `0b15c3ebeb43426655d5e597cda1288034e01276` |
| `namaek2/java-christmas-6-scienceNH` | `6436b6304d7eda855a407c375f5319fb89d49611` |

두 저장소의 깨끗한 복사본에서 먼저 JDK 17로 `./gradlew --no-daemon --max-workers=2 clean build`를 실행한다. `EXIF`, `CHRISTMAS`는 이 복사본 경로, `WORK`는 두 저장소와 플러그인 저장소 밖의 작업 디렉터리다.

```bash
python src/test/python/run_target_smoke.py \
  --repo "$PWD" --target "$EXIF" --kind exif \
  --run-root "$WORK/exif-run" --gradle-home "$WORK/gradle-exif" --jdk "$JAVA_HOME"

python src/test/python/run_target_smoke.py \
  --repo "$PWD" --target "$CHRISTMAS" --kind christmas \
  --run-root "$WORK/christmas-run" --gradle-home "$WORK/gradle-christmas" --jdk "$JAVA_HOME"
```

`--run-root`는 아직 존재하지 않는 경로여야 한다. 재실행할 때 새 경로를 사용한다. 기존 디렉터리나 원본 저장소를 삭제하지 않는다.

검사기는 리소스 해시 확인, 실제 Python 단계 전체, 대상 Wrapper 빌드, 실행 검사를 수행하고 각 단계의 종료 코드와 로그를 `summary.json`에 기록한다.

- EXIF: 이름 매핑으로 난독화된 클래스를 찾고 메서드 시그니처로 호출한다. EXIF 제거, 콜백 1회, 이미지 크기 보존을 검사하고 GUI가 예외 없이 시작되는지 확인한다. 원래 공개 메서드 이름의 유지 자체는 요구하지 않는다.
- Christmas: 정상 주문, 혜택 없는 주문, 잘못된 날짜 재입력, 잘못된 메뉴 재입력의 네 입력에 대해 원본/난독화 JAR의 종료 코드와 출력 바이트가 일치해야 한다.

이 검증은 지정한 두 Java 프로젝트에 대한 것이다. Android 기기 실행, 모든 Java 문법, 외부 AI 제공자의 라이브 응답까지 보증하지는 않는다.
