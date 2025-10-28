import json
import os
import re

# 사용 가능한 AI 모델 확인
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("WARNING: anthropic module not found.")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("WARNING: google-generativeai module not found.")

try:
    import openai
    CHATGPT_AVAILABLE = True
except ImportError:
    CHATGPT_AVAILABLE = False
    print("WARNING: openai module not found.")


def detect_api_key_type(api_key):
    """
    API 키의 형식을 분석하여 어떤 AI 서비스의 키인지 판단

    Args:
        api_key: 검사할 API 키

    Returns:
        str: "claude", "gemini", "chatgpt", 또는 "unknown"
    """
    if not api_key or not isinstance(api_key, str):
        return "unknown"

    api_key = api_key.strip()

    # Claude API 키 패턴: sk-ant-api03-... (보통 100자 이상)
    if api_key.startswith("sk-ant-"):
        return "claude"

    # OpenAI API 키 패턴: sk-... 또는 sk-proj-... (보통 40-60자)
    if api_key.startswith("sk-") and not api_key.startswith("sk-ant-"):
        return "chatgpt"

    # Gemini API 키 패턴: AIza... (보통 39자)
    if api_key.startswith("AIza"):
        return "gemini"

    return "unknown"


def validate_api_key(api_key, ai_type):
    """
    API 키가 실제로 작동하는지 간단한 테스트

    Args:
        api_key: 검증할 API 키
        ai_type: AI 타입 ("claude", "gemini", "chatgpt")

    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        if ai_type == "claude" and CLAUDE_AVAILABLE:
            client = anthropic.Anthropic(api_key=api_key)
            # 간단한 테스트 요청
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True

        elif ai_type == "gemini" and GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # 간단한 테스트 요청
            response = model.generate_content("test")
            return True

        elif ai_type == "chatgpt" and CHATGPT_AVAILABLE:
            client = openai.OpenAI(api_key=api_key)
            # 간단한 테스트 요청
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True

        return False

    except Exception as e:
        print(f"API 키 검증 실패 ({ai_type}): {e}")
        return False


def get_analysis_prompt(flow_text):
    """분석 프롬프트 생성"""
    return f"""
당신은 Java 애플리케이션 보안 전문가입니다. 다음 taint flow 분석 결과를 바탕으로 전문적인 보안 분석 보고서를 마크다운 형식으로 작성해주세요.

# 분석 데이터
{flow_text}

각 flow의 형식: [민감도, 메소드1, 메소드2, ...]
- 민감도: 1(낮음), 2(중간), 3(높음)

---

# 보고서 작성 지침

## 문서 구조 원칙
1. **계층적 구조**: 대분류(#) → 중분류(##) → 소분류(###) → 상세(####)를 일관되게 유지
2. **시각적 구분**: 각 주요 섹션 사이에 구분선(---) 사용
3. **표준화된 포맷**: 모든 취약점 분석은 동일한 템플릿 적용
4. **명확한 레이블**: 각 항목에 **굵은 글씨** 레이블 사용
5. **간결성**: 불필요한 반복 제거, 핵심만 전달

## 스타일 가이드
- 이모지 사용 금지
- 표는 깔끔하게 정렬
- 코드 블록은 언어 태그 포함 (```java)
- 다이어그램은 텍스트 기반으로 명확하게
- 번호 매김과 불릿 포인트를 적절히 혼용

---

# 보고서 구성 요구사항

## 1. Executive Summary
- 분석 대상 애플리케이션 개요
- 발견된 전체 취약점 수 및 심각도 분포
- 핵심 보안 이슈 요약
- 전반적인 보안 상태 평가

## 2. 통합 위험도 분석

### 2.1 위험도별 분포
심각도별 건수와 비율을 표로 정리하고, 시각적으로 표현하세요.

### 2.2 다층적 분석 관점
- Taint flow 분석에서 발견된 데이터 흐름 취약점
- 정적 분석 도구 관점에서 발견 가능한 코드 품질 이슈
- 프레임워크/라이브러리 사용 패턴에서 추론되는 취약점

### 2.3 취약점 패턴 분석
발견된 취약점들을 유형별로 분류하고 통계를 제시하세요.

### 2.4 주요 데이터 흐름 시각화
가장 심각한 taint flow들의 데이터 흐름을 다이어그램으로 표현하세요.

## 3. 취약점 상세 분석

각 taint flow에 대해 다음 형식으로 분석하세요:

---

### 취약점 #[번호]: [취약점 유형명]

**위험도**: [높음/중간/낮음]

**보안 표준 매핑**
- 해당하는 CWE 분류
- 관련 OWASP 카테고리
- 기타 보안 프레임워크 매핑

#### 데이터 흐름 분석
Source부터 Sink까지의 데이터 흐름을 단계별로 시각화하고 각 단계의 역할을 설명하세요.

#### 취약점 상세 설명
- 이 취약점이 발생하는 근본 원인
- 소스코드 레벨에서의 문제점
- 데이터가 오염되는 과정

#### 공격 시나리오
실제 공격자가 이 취약점을 악용하는 구체적인 방법을 시나리오로 작성하세요.

#### 영향도 평가
CIA Triad(기밀성, 무결성, 가용성) 관점에서 영향도를 평가하고, 가능하다면 CVSS 점수를 추정하세요.

#### 보안 대응방안

**1. 즉시 조치**
당장 적용 가능한 임시 완화 방법을 제시하세요.

**2. 근본 해결방법**
취약한 코드와 보안이 강화된 코드를 Before/After로 비교하여 제시하세요. 핵심 보안 원칙을 설명하세요.

**3. 추가 보안 강화**
심층 방어(Defense in Depth) 관점에서 추가 보안 레이어를 제안하세요.

**4. 코드 품질 개선**
정적 분석 도구들이 권장하는 코드 개선 사항을 반영하세요.

**5. 검증 방법**
보안 패치가 효과적으로 적용되었는지 확인하는 테스트 방법을 제시하세요.

---

# 작성 지침
- 모든 발견된 취약점을 빠짐없이 분석하세요
- Taint flow 데이터를 기반으로 하되, 전문가적 관점에서 다른 도구들이 발견할 수 있는 이슈도 예측하세요
- 메소드명, 패턴, 데이터 흐름을 보고 어떤 프레임워크나 라이브러리가 사용되었는지 추론하세요
- 기술적으로 정확하고 명확한 설명을 제공하세요
- 실행 가능하고 구체적인 해결방안을 제시하세요
- 전문적이면서도 이해하기 쉬운 한국어로 작성하세요
- 마크다운 문법을 올바르게 사용하세요
- 다이어그램이나 표를 활용하여 가독성을 높이세요
"""


def send_to_claude(priority_flow, user_api_key=None):
    """priority_flow를 Claude에게 전달"""
    if not CLAUDE_AVAILABLE:
        print("ERROR: Claude (anthropic module) is not available.")
        return None

    if not user_api_key:
        print("ERROR: Can't find user API key.")
        return None

    try:
        client = anthropic.Anthropic(api_key=user_api_key)
        flow_text = "\n".join([str(flow) for flow in priority_flow])
        prompt = get_analysis_prompt(flow_text)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text
        print("Claude 분석 완료")
        return result

    except Exception as e:
        print(f"Claude API 호출 실패: {e}")
        return None


def send_to_gemini(priority_flow, user_api_key=None):
    """priority_flow를 Gemini에게 전달"""
    if not GEMINI_AVAILABLE:
        print("ERROR: Gemini (google-generativeai module) is not available.")
        return None

    if not user_api_key:
        print("ERROR: Can't find user API key.")
        return None

    try:
        genai.configure(api_key=user_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        flow_text = "\n".join([str(flow) for flow in priority_flow])
        prompt = get_analysis_prompt(flow_text)

        response = model.generate_content(prompt)
        result = response.text

        print("Gemini 분석 완료")
        return result

    except Exception as e:
        print(f"Gemini API 호출 실패: {e}")
        return None


def send_to_chatgpt(priority_flow, user_api_key=None):
    """priority_flow를 ChatGPT에게 전달"""
    if not CHATGPT_AVAILABLE:
        print("ERROR: ChatGPT (openai module) is not available.")
        return None

    if not user_api_key:
        print("ERROR: Can't find user API key.")
        return None

    try:
        client = openai.OpenAI(api_key=user_api_key)

        flow_text = "\n".join([str(flow) for flow in priority_flow])
        prompt = get_analysis_prompt(flow_text)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 Java 애플리케이션 보안 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16000
        )

        result = response.choices[0].message.content
        print("ChatGPT 분석 완료")
        return result

    except Exception as e:
        print(f"ChatGPT API 호출 실패: {e}")
        return None


def send_to_ai(priority_flow, user_api_key=None, ai_type=None, auto_detect=True, validate_key=False):
    """
    통합 AI 분석 함수 - API 키 자동 감지 기능 포함

    Args:
        priority_flow: 분석할 taint flow 데이터
        user_api_key: API 키
        ai_type: 사용할 AI 모델 ("claude", "gemini", "chatgpt") - None이면 자동 감지
        auto_detect: True면 API 키 타입을 자동으로 감지
        validate_key: True면 API 키가 실제로 작동하는지 검증

    Returns:
        분석 결과 문자열 또는 None
    """
    if not user_api_key:
        print("ERROR: API key is required.")
        return None

    # AI 타입이 지정되지 않았거나 auto_detect가 True면 자동 감지
    if ai_type is None or auto_detect:
        detected_type = detect_api_key_type(user_api_key)

        if detected_type == "unknown":
            print("ERROR: Could not detect API key type.")
            print("Please specify ai_type manually: 'claude', 'gemini', or 'chatgpt'")
            return None

        print(f"✓ API 키 타입 감지: {detected_type.upper()}")
        ai_type = detected_type

    ai_type = ai_type.lower()

    # API 키 검증 (선택적)
    if validate_key:
        print(f"API 키 검증 중... ({ai_type})")
        if not validate_api_key(user_api_key, ai_type):
            print(f"ERROR: Invalid {ai_type.upper()} API key.")
            return None
        print(f"✓ API 키 검증 완료")

    # 해당 AI로 분석 실행
    if ai_type == "claude":
        return send_to_claude(priority_flow, user_api_key)
    elif ai_type == "gemini":
        return send_to_gemini(priority_flow, user_api_key)
    elif ai_type == "chatgpt":
        return send_to_chatgpt(priority_flow, user_api_key)
    else:
        print(f"ERROR: Unknown AI type '{ai_type}'. Choose from: claude, gemini, chatgpt")
        return None


def get_available_models():
    """사용 가능한 AI 모델 목록 반환"""
    available = []
    if CLAUDE_AVAILABLE:
        available.append("claude")
    if GEMINI_AVAILABLE:
        available.append("gemini")
    if CHATGPT_AVAILABLE:
        available.append("chatgpt")
    return available


