"""불투명 술어(Opaque Predicate) 기반 난독화.

메서드 본문 시작 지점에 "항상 거짓"이지만 컴파일러가 정적으로 접을 수 없는 술어로
가드된 junk 블록을 삽입한다. 술어가 런타임에 절대 참이 아니므로 동작은 그대로지만,
디컴파일러/정적 분석기 입장에서는 죽은 코드인지 알기 어렵다.

핵심 설계:
- 술어는 갓 선언한 비-final 지역 변수에 대해 평가하므로 javac 가 상수 폴딩하지 못한다.
  (지역 변수가 final/상수가 아니면 `v & 0`, `(v*v) & 3` 등을 컴파일 타임에 접지 않는다.)
- import 가 전혀 필요 없다(정수 산술/비트 연산만 사용). 따라서 dummyInsert 의
  `new Random()`(java.util.Random import 누락 시 컴파일 깨짐) 문제를 대체할 수 있다.
- junk 본문은 메서드 호출 없이 지역 변수 산술만 해서 심볼 해석 위험이 없다.

수학적 근거(항상 거짓):
- (v & 0) != 0            : v & 0 == 0 이므로 거짓
- (v | 1) == 0           : 최하위 비트가 1 이므로 0 이 될 수 없음
- (v ^ v) > 0            : v ^ v == 0
- ((v * v) & 3) == 3     : 임의의 정수의 제곱은 (mod 4) 0 또는 1 → & 3 이 3 이 될 수 없음
                           (2의 보수 곱셈의 하위 2비트는 정확하므로 오버플로에도 성립)
"""

import secrets
import string


def _rand_name(length=8):
    first = secrets.choice(string.ascii_lowercase)
    rest = "".join(secrets.choice(string.ascii_lowercase + string.digits)
                   for _ in range(length - 1))
    return first + rest


def _always_false_predicate(var):
    """`var` 에 대한 항상-거짓 불투명 술어 문자열을 무작위로 하나 고른다."""
    forms = [
        f"({var} & 0) != 0",
        f"({var} | 1) == 0",
        f"({var} ^ {var}) > 0",
        f"(({var} * {var}) & 3) == 3",
        f"(({var} * {var} + {var}) & 3) == 2",  # n^2+n 는 짝수 → &3 ∈ {0,2}? 아래 주석 참고
    ]
    # 주: n^2+n = n(n+1) 은 항상 짝수이므로 (mod 4) 0 또는 2. == 2 는 참이 될 수 있어
    # 마지막 form 은 제외하고 "확실히 거짓"인 것만 사용한다.
    safe_forms = forms[:4]
    return secrets.choice(safe_forms)


def make_opaque_block(indent="        "):
    """import 불필요한 불투명-거짓 가드 junk 블록 문자열을 생성한다.

    dummyInsert 등 다른 모듈이 재사용할 수 있도록 분리. 호출자는 메서드 본문 안
    (지역 변수 선언이 허용되는 위치)에 그대로 끼워 넣으면 된다.
    """
    v = _rand_name()
    seed = secrets.randbelow(2_000_000_000) + 1
    pred = _always_false_predicate(v)
    # junk 는 지역 변수 산술만. 절대 실행되지 않지만 컴파일은 된다.
    block = (
        f"{indent}int {v} = {seed};\n"
        f"{indent}if ({pred}) {{\n"
        f"{indent}    {v} = {v} * 31 + 17;\n"
        f"{indent}    {v} = ({v} >>> 3) ^ {secrets.randbelow(2_000_000_000) + 1};\n"
        f"{indent}    {v} = {v} ^ ({v} << 2);\n"
        f"{indent}}}\n"
    )
    return block


class OpaquePredicate:
    """메서드 본문 시작부에 불투명-거짓 junk 블록을 1개 이상 삽입한다."""

    def __init__(self, code, count=1):
        self.code = code
        self.count = max(1, count)
        self.obfuscated = self._obfuscate(code)

    def _obfuscate(self, code):
        if not code:
            return None

        brace = self._find_body_brace(code)
        if brace == -1:
            return None

        blocks = "".join(make_opaque_block() for _ in range(self.count))
        # 여는 중괄호 바로 뒤에 삽입.
        new_code = code[:brace + 1] + "\n" + blocks + code[brace + 1:]
        return new_code

    @staticmethod
    def _find_body_brace(code):
        """메서드 시그니처를 닫는 첫 '{' 의 인덱스를 찾는다.

        추출된 단일 메서드 스니펫에서는 첫 번째 '{' 가 본문 시작이다.
        문자열/문자 리터럴 안의 '{' 는 건너뛴다.
        """
        in_str = False
        str_ch = ""
        i = 0
        n = len(code)
        while i < n:
            ch = code[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == str_ch:
                    in_str = False
            else:
                if ch in ("\"", "'"):
                    in_str = True
                    str_ch = ch
                elif ch == "{":
                    return i
            i += 1
        return -1

    def get_obfuscated_code(self):
        return self.obfuscated


if __name__ == "__main__":
    sample = (
        "public int compute(int a, int b) {\n"
        "    int result = a + b;\n"
        "    result = result * 2;\n"
        "    return result;\n"
        "}\n"
    )
    print(OpaquePredicate(sample, count=2).get_obfuscated_code())
