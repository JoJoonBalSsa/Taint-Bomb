"""Java 구문 검증 안전망 (syntax-validation safety net).

난독화 변환들은 모두 정규식/문자열 조작으로 Java 소스를 생성하기 때문에,
잘못 변환되면 컴파일이 깨질 수 있다. 이 모듈은 변환 결과(메서드 단위 스니펫)를
가짜 클래스로 감싸 javalang 으로 파싱해 보고, 파싱이 되면 "구문상 안전"으로 본다.

levelObfuscate 가 각 변환 후 이 검사를 호출해, 검사에 실패하면 직전의 유효한
소스로 되돌린다(revert-on-failure). 덕분에 어떤 변환도 절대 깨진 Java 를 파일에
쓰지 않는다.

주의: javalang 파싱 통과는 "구문(syntax)"만 보장한다. 타입/심볼 해석(javac
semantics)까지 보장하지는 않으므로, 의미를 바꿀 수 있는 공격적 변환(리플렉션 등)은
보수적으로만 사용한다.
"""

import javalang

# 메서드 스니펫을 감쌀 합성 클래스. import 가 필요 없는 형태로 최대한 관대하게 만든다.
_WRAPPER_HEAD = (
    "class __TaintBombSyntaxProbe__ {\n"
)
_WRAPPER_TAIL = "\n}\n"


def is_valid_java_method(snippet):
    """메서드(들) 스니펫이 구문상 유효한 Java 인지 검사.

    snippet 은 클래스 본문에 들어갈 수 있는 멤버 선언(메서드/필드)들의 모음이라고
    가정한다. 합성 클래스로 감싼 뒤 파싱한다.
    """
    if snippet is None:
        return False
    if not isinstance(snippet, str):
        return False
    if snippet.strip() == "":
        # 빈 스니펫은 "변환이 아무것도 만들지 못함"이므로 안전하지 않다고 본다.
        return False

    wrapped = _WRAPPER_HEAD + snippet + _WRAPPER_TAIL
    return is_valid_java_source(wrapped)


def is_valid_java_source(source):
    """완전한 컴파일 단위(파일 전체) 문자열이 구문상 유효한지 검사."""
    if not source or not isinstance(source, str):
        return False
    try:
        javalang.parse.parse(source)
        return True
    except (javalang.parser.JavaSyntaxError,
            javalang.parser.JavaParserError,
            javalang.tokenizer.LexerError):
        return False
    except Exception:
        # javalang 은 일부 입력에서 IndexError/RecursionError 등을 던질 수 있다.
        # 검증기는 절대 예외로 죽지 않고 "안전하지 않음"으로 답해야 한다.
        return False


def safe_transform(original, transformed):
    """변환 결과가 구문상 유효하면 transformed, 아니면 original 을 돌려준다.

    변환 함수들을 체이닝할 때, 각 단계 출력이 깨졌으면 그 단계를 통째로 버리고
    이전 단계 결과를 유지하기 위한 헬퍼.
    """
    if transformed is None:
        return original
    if transformed == original:
        return original
    if is_valid_java_method(transformed):
        return transformed
    return original
