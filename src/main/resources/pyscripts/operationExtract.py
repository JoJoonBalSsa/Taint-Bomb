import re


class ExtractOperations:
    def __init__(self, method_code):
        self.method_code = method_code
        self.expressions = self.extract_all_conditions()

        # """
        #  public class AgeChecker {
        #      public static void main(String[] args) {
        #          int age = 20; // 나이를 설정합니다.
        #
        #          if (age >=  18 + 1) {
        #              System.out.println("당신은 성인입니다.");
        #          } else if (age >=  18 - 1) {
        #              System.out.println("당신은 성인입니다.");
        #          }else if (age >=  18 * 1) {
        #              System.out.println("당신은 성인입니다.");
        #          } else if (age >=  18 / 1) {
        #              System.out.println("당신은 성인입니다.");
        #          }
        #          else {
        #              System.out.println("당신은 미성년자입니다.");
        #          }
        #      }
        #  }
        # """


    def find_if_conditions(self):
        if_pattern = re.compile(r'\bif\s*\((.*?)\)\s*\{', re.DOTALL)
        return if_pattern.findall(self.method_code)


    def find_for_conditions(self):
        for_pattern = re.compile(r'\bfor\s*\((.*?)\)\s*\{', re.DOTALL)
        return for_pattern.findall(self.method_code)


    def find_while_conditions(self):
        while_pattern = re.compile(r'\bwhile\s*\((.*?)\)\s*\{', re.DOTALL)
        return while_pattern.findall(self.method_code)


    def find_do_while_conditions(self):
        do_while_pattern = re.compile(r'\bdo\s*\{.*?\}\s*while\s*\((.*?)\);', re.DOTALL)
        return do_while_pattern.findall(self.method_code)


    def extract_all_conditions(self):
        expressions = [self.find_if_conditions(), self.find_for_conditions(), self.find_while_conditions(),
                       self.find_do_while_conditions()]
        print(expressions)
        return expressions