import json


class OperationDB:
    def __init__(self):
        self.__op = {
            "+": "(78+{a})+123-(~{b}+1)-110-91",
            "-": "(45+{b})+75+(~{a} + 1)-58-62",

            "*": "int resultObfuscated = 0; for(int i = 0; i < {b}; i++) {{ resultObfuscated -= ~{a}+1; }}",
            "/": "int resultObfuscated = 0; int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; resultObfuscated++;}}",
            "%": "{a} - (int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; }} temp * {b})",
            "!":"{a} ? ({b} ? false : (true ? false : false)) : (true  ? true : true)",



            "==":"(({a}*100 + ({a} - {b} + 1 - 1) == {b}*100) && ({a} != {b}) ? ((true && !false) ? false : (true || false)) : ((false || true) && !false)) && (({a} * 1 + 0) / 1 == {b})",
            "!=":"(({a}*100 + ({b} - {a} + 1) != {b}*100)&& ({a} != {b}) ? ((true || false) && !false) : (false && true || false)) && (({a} * 1 + 1) / 1 != {b})",


            ">":"((127 + 28 + ~{a} + 42 > 88 + ~{b} + 28 + 81) && (({a} ^ {b}) != 0)) || (({a} & {b}) == 0)",
            "<":"((47 + ~{b} + 444 + 85 < 70 + ~{a} + 444 + 62) ? true : false) && (({a} | {b}) != 0)",


            ">=":"((43 + ~{a} + 89 >= 16 +22+ ~{b} + 94) || ({a} == {b})) || (({a}^{b}) == 0)",
            "<=":"((48 + 11 + ~{b} + 29 + 66 <= 22 + 60 + 3 + ~{a} + 69) || ({a} == {b})) || (({a}^{b}) == 0)",



            "&":"~(~(-{a}-1)|~(-{b}-1))",
            "|":"~(~(-{a}-1)&~(-{b}-1))",
            "^":"~(~(-{a}-1)&~(-{b}-1))&~(~(~(-{a}-1)|~(-{b}-1)))",
            "~":"-{a}-1",
            "<<":"{a}*(int)Math.pow(2, {b})",
            ">>":"{a}/(int)Math.pow(2, {b})",
            ">>>":"({a} & 0x7fffffff)/(int)Math.pow(2, {b})",
            "&&":"({a}?({b}?true:false):false)",
            "||":"({a}?true:({b}?true:false))",
            "=":"{a}={b}^00",
            "+=":"{a}={a} + (~(~{b} + 1) + 1)",
            "-=":"{a}={a} + ~{b} + 1",
            "*=":"{a}=(int resultObfuscated = 0; for(int i = 0; i < {b}; i++) { resultObfuscated += (~(~{a} + 1) + 1); })",
            "/=":"{a}=(int resultObfuscated = 0; int temp = a; int bInverted = ~(~b + 1) + 1; while (temp >= bInverted) { temp -= bInverted; resultObfuscated++;})",
            "%=":"{a}={a} - (int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) { temp -= bInverted; } temp * {b})",
            "&=":"{a}=~(~(-{a}-1) | ~(-{b}-1))",
            "|=":"{a}=~(~(-{a}-1) & ~(-{b}-1))",
            "^=":"{a}=~(~(-{a}-1) & ~(-{b}-1)) & ~(~(~(-{a}-1) | ~(-{b}-1)))",
            "<<=":"{a}={a}*(int)Math.pow(2, {b})",
            ">>=":"{a}={a}/(int)Math.pow(2, {b})",
            ">>>=":"{a}=({a} & 0x7fffffff)/(int)Math.pow(2, {b})"
        }

    def op_db(self):
        return self.__op
        # return json.dumps(self.__op, ensure_ascii=False)
