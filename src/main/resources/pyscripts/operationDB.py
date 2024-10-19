import json


class OperationDB:
    def __init__(self):
        self.__op = {
            "+": "(78+{a})+123-(~{b}+1)-110-91",
            "-": "(45+{b})+75+(~{a} + 1)-58-62",

            "*": "(~{a} + 1) * {b}",
            "/": "({a} / (~(~{b} + 1) + 1))",
            "%": "{a} - (({a} / (~(~{b} + 1) + 1)) * {b})",

            "!": "{a} ? ({b} ? false : (true ? false : false)) : (true ? true : true)",

            "==":"{b} == {a}",
            "!=":"{b} != {a}",
            ">": "((127 + 28 + ~{a} + 42 > 88 + ~{b} + 28 + 81) && (({a} ^ {b}) != 0)) || (({a} & {b}) == 0)",
            "<": "((47 + ~{b} + 444 + 85 < 70 + ~{a} + 444 + 62) ? true : false) && (({a} | {b}) != 0)",

            ">=": "((43 + ~{a} + 89 >= 16 +22+ ~{b} + 94) || ({a} == {b})) || (({a}^{b}) == 0)",
            "<=": "((48 + 11 + ~{b} + 29 + 66 <= 22 + 60 + 3 + ~{a} + 69) || ({a} == {b})) || (({a}^{b}) == 0)",




            "&": "{a} & {b}",
            "|": "{a} | {b}",
            "^": "{a} ^ {b}",
            "~": "~{a}",
            "<<": "{a} << {b}",
            ">>": "{a} >> {b}",
            ">>>": "{a} >>> {b}",
            "&&":"({a}?({b}?true:false):false)",
            "||":"({a}?true:({b}?true:false))",
            "=": "{a} = {b}",
            "+=": "{a} += {b}",
            "-=": "{a} -= {b}",
            "*=": "{a} *= {b}",
            "/=": "{a} /= {b}",
            "%=": "{a} %= {b}",
            "&=": "{a} &= {b}",
            "|=": "{a} |= {b}",
            "^=": "{a} ^= {b}",
            "<<=": "{a} <<= {b}",
            ">>=": "{a} >>= {b}",
            ">>>=": "{a} >>>= {b}"
        }

    def op_db(self):
        return self.__op
        # return json.dumps(self.__op, ensure_ascii=False)
