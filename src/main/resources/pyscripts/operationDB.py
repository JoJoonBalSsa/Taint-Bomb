import json


class OperationDB:
    def __init__(self):
        self.__op = {
            "+": "{a}-(~{b}+1)",
            "-": "{a}+(~{b} + 1)",
            "*": "int resultObfuscated = 0; for(int i = 0; i < {b}; i++) {{ resultObfuscated -= ~{a}+1; }}",
            "/": "int resultObfuscated = 0; int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; resultObfuscated++;}}",
            "%": "{a} - (int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; }} temp * {b})",
            "!":"{a} ? ({b} ? false : (true ? false : false)) : (true  ? true : true)",
            "==":"({a} != {b}) ? (true ? false : (true ? false : false)) : (false ? true : true)",
            "!=":"({a} == {b}) ? (true ? false : (true ? false : false)) : (true ? true : true)",
            ">":"~{b} + 1 > ~{a} + 1",
            "<":"~{b} + 1 < ~{a} + 1",
            ">=":"(~{b} + 1 > ~{a} + 1)",
            "<=":"(~{b} + 1 < ~{a} + 1)",
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