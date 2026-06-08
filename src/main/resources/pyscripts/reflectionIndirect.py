r"""리플렉션 기반 호출 우회 (reflection-based call indirection) — 실험적/옵트인.

직접 메서드 호출을 java.lang.reflect 를 통한 동적 호출로 바꿔, 정적 분석기/디컴파일러가
호출 그래프를 곧바로 보지 못하게 한다.

    obj.doWork();
    ->
    try {
        java.lang.reflect.Method _m = obj.getClass().getDeclaredMethod("doWork");
        _m.setAccessible(true);
        _m.invoke(obj);
    } catch (Exception _e) {
        throw new RuntimeException(_e);
    }

★ 왜 기본 파이프라인에 넣지 않는가(중요):
  - javaValidate 안전망은 "구문(syntax)"만 검증한다. 리플렉션 우회는 구문상 항상
    올바르지만 런타임/타입 의미를 바꿀 수 있다:
      * getDeclaredMethod 는 "선언 클래스"의 메서드만 찾는다. 상속받은 메서드면
        런타임 NoSuchMethodException 이 날 수 있다.
      * 검사 예외(checked exception)가 InvocationTargetException 으로 감싸여
        예외 전파 의미가 달라진다.
  파싱만으로는 이런 회귀를 잡을 수 없으므로, 자동 적용은 위험하다. 따라서 이 모듈은
  명시적 옵트인으로만 쓰고, levelObfuscate 의 기본 변환 체인에는 포함하지 않는다.

적용 범위(매우 보수적):
  - "단독 문장"이면서 인자가 없는 void 호출 `<recv>.<method>();` 형태만 변환한다.
    (`<recv>` 는 단순 식별자, 체이닝/인자/대입 없음.)
  - 그 외에는 원본을 그대로 반환한다(None).
  - java.lang.reflect.Method 를 완전 수식명으로 써서 import 추가가 필요 없다.
"""

import re
import secrets

# 정확히 `ident.ident();` 한 줄(앞뒤 공백 허용)인 단독 void 호출만.
_SIMPLE_VOID_CALL = re.compile(
    r'^\s*([A-Za-z_$]\w*)\s*\.\s*([A-Za-z_$]\w*)\s*\(\s*\)\s*;\s*$'
)


def _rand(name):
    return name + str(secrets.randbelow(100000))


class ReflectionIndirect:
    """메서드 본문 안의 인자 없는 단독 void 호출들을 리플렉션 블록으로 치환한다."""

    def __init__(self, code):
        self.code = code
        self.obfuscated = self._obfuscate(code)

    def _obfuscate(self, code):
        if not code:
            return None

        lines = code.splitlines(keepends=True)
        changed = False
        out_lines = []
        for line in lines:
            m = _SIMPLE_VOID_CALL.match(line)
            if m:
                recv, method = m.group(1), m.group(2)
                # this/super 수신자는 getClass()가 의도와 다를 수 있어 건너뛴다.
                if recv in ("this", "super"):
                    out_lines.append(line)
                    continue
                indent = re.match(r'^\s*', line).group(0)
                out_lines.append(self._reflect_block(indent, recv, method))
                changed = True
            else:
                out_lines.append(line)

        if not changed:
            return None
        return "".join(out_lines)

    @staticmethod
    def _reflect_block(indent, recv, method):
        mvar = _rand("_m")
        evar = _rand("_e")
        return (
            f"{indent}try {{\n"
            f"{indent}    java.lang.reflect.Method {mvar} = "
            f"{recv}.getClass().getDeclaredMethod(\"{method}\");\n"
            f"{indent}    {mvar}.setAccessible(true);\n"
            f"{indent}    {mvar}.invoke({recv});\n"
            f"{indent}}} catch (Exception {evar}) {{\n"
            f"{indent}    throw new RuntimeException({evar});\n"
            f"{indent}}}\n"
        )

    def get_obfuscated_code(self):
        return self.obfuscated


if __name__ == "__main__":
    sample = (
        "public void run(Worker w) {\n"
        "    w.start();\n"
        "    int x = 1 + 2;\n"
        "    w.finish();\n"
        "}\n"
    )
    print(ReflectionIndirect(sample).get_obfuscated_code())
