import secrets


class DumbDB :
    def __init__(self):
        self.generated_numbers = set()
        self.list_length = len(self.dummy_list)

    def get_dumb(self, index):
        return self.dummy_list[index]

    def get_unique_random_number(self):
        if len(self.generated_numbers) == self.list_length:
            return None

        while True:
            rand = secrets.randbelow(self.list_length)
            if rand not in self.generated_numbers:
                self.generated_numbers.add(rand)
                return rand

    dummy_list = [
        """
    private void unusedFunction0() {
        // This function does nothing but adds noise to the code
        System.out.println("This is a dummy function0 to obfuscate the code.");
    }
        """,
        """
    private void unusedFunction1() {
        // This function does nothing but adds noise to the code
        System.out.println("This is a dummy function1 to obfuscate the code.");
    }
        """,
        """
    private void unusedFunction2() {
        // This function does nothing but adds noise to the code
        System.out.println("This is a dummy function2 to obfuscate the code.");
    }
        """
    ]
