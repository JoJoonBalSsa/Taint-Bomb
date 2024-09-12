import re


class SplitMethod:
    def __init__(self, method):
        self.method = method


    def obfuscate_method(self):
        # 메소드 선언부와 본문 추출
        match = re.match(r'(.*?)\s*\{(.*?)\}', self.method, re.DOTALL)
        if match:
            declaration = match.group(1).strip()
            method_body = match.group(2).strip()
        else:
            raise ValueError("유효한 메소드 선언과 본문을 찾을 수 없습니다.")

        if "try" in method_body:
            print("try-catch 문이 포함된 메소드는 난독화하지 않습니다.")
            return None  # 원본 메소드를 그대로 반환

        # 메소드를 여러 블록으로 분할
        blocks = re.split(r';|\{|\}', method_body)
        blocks = [block.strip() for block in blocks if block.strip()]

        # 각 블록에 레이블 할당
        labeled_blocks = []
        for i, block in enumerate(blocks):
            if block.strip().startswith("return"):
                labeled_blocks.append(f'case {i}: {block};')
            else:
                labeled_blocks.append(f'case {i}: {{{block}; state++;}}')

        # 난독화된 메소드 구성
        obfuscated_body = f"""{{
            int state = 0
            while(state != -1) {{
                switch(state) {{
                    {' '.join(labeled_blocks)}
                }}
            }}
        }}"""

        # 원래 메소드 선언과 난독화된 본문 결합
        obfuscated_method = f"{declaration} {obfuscated_body}"

        print(obfuscated_method)
        return obfuscated_method
