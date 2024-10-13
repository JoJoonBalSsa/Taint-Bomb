package org.example;

public class Main {

    public static void main(String[] args) {
        // TODO Auto-generated method stub
        int a = 1;
        int b = 3;
        char d='a';
        int c = 1;
        char e='a';
        char h='k';

        if((78+a)+123-(~d+1)-110-91==98)
        {
            int result = a-(~d + 1);
            System.out.println("+"+result);
        }

        if((45+d)+75+(~a + 1)-58-62==96)
        {
            int result = d+(~a + 1);
            System.out.println("-"+result);
        }



        if (((a*100 + (a - c + 1 - 1) == c*100) && (a != c) ? ((true && !false) ? false : (true || false)) : ((false || true) && !false))
                && ((a * 1 + 0) / 1 == c)) {
            System.out.println("hiahi");
        }



        if ((a*100 + (b - a + 1) != b*100) && ((a != b) ? ((true || false) && !false) : (false && true || false))
                && ((a * 1 + 1) / 1 != b)) { // a가 b와 같지 않도록 조건 추가
            System.out.println("!!!!!!!!");
        }








/**
        if( (int resultObfuscated = 0; for(int i = 0; i < b; i++) {{ resultObfuscated -= ~a+1; }})==3)
        {
            System.out.println("x");
        }

        if( (int resultObfuscated = 0; int temp = a; int bInverted = ~(~b + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; resultObfuscated++;}}) ==(1/3))
        {
            System.out.println("/");
        }


/**
                "%": "{a} - (int temp = {a}; int bInverted = ~(~{b} + 1) + 1; while (temp >= bInverted) {{ temp -= bInverted; }} temp * {b})",
                "!":"{a} ? ({b} ? false : (true ? false : false)) : (true  ? true : true)",
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
    **/



    }

}
