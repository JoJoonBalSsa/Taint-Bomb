import secrets


class DumbDB:
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
            if len(self.dummy_list) == len(self.generated_numbers):
                return None

    dummy_list = [
        """
    private byte[] unusedFunction0() {
         byte[] key = {0x66};
         int rounds = 7;
         
         return unusedFunction0(key, rounds);
    }
    
    private byte[] unusedFunction0(byte[] key, int rounds) {
        try{ 
            int keyLength = key.length;
            byte[] backKey = new byte[keyLength];
    
            for (int i = 1; i < rounds; i++) {
                byte[] prevKey = key;
                byte[] newKey = new byte[keyLength];
        
                for (int j = 0; j < keyLength; j++) {
                    newKey[j] = (byte) (prevKey[(j + 1) % keyLength] ^
                            prevKey[(j + 5) % keyLength] ^
                            prevKey[(j + 13) % keyLength]);
                }
        
                for (int j = 0; j < keyLength; j++) {
                    if (j % 2 == 0) {
                        newKey[j] = (byte) (~newKey[j] & 0xFF);
                    }
                }
                backKey = newKey;
            }
        
            return backKey;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
    private byte[] unusedFunction1() {
                 byte[] key = {99, 18, 57, 17};
                 byte[] key2 =  {66, 88, 69};
                 return unusedFunction1(key, key2);
    }

    private byte[] unusedFunction1(byte[] a , byte[] b) {
        try {
            byte[] result = new byte[a.length + b.length];
            System.arraycopy(a, 0, result, 0, a.length);
            System.arraycopy(b, 0, result, a.length, b.length);
            return result;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
    public byte[] unusedFunction2() {

                 byte[] data = {66, 123, 87, 88};
                 return unusedFunction2(data);
    }

    public byte[] unusedFunction2(byte[] data) {
        try {
            int i = data.length - 1;
            while (i >= 0 && data[i] == 0) {
                i--;
            }
            return data;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
    private byte[] unusedFunction3() {
                 byte[] data = {29, 31};
                 byte[] data2 = {1, 95};
        return unusedFunction3(data, data2);
    }
    private byte[] unusedFunction3(byte[] a, byte[] b) {
        try {
            byte[] result = new byte[a.length];
            for (int i = 0; i < a.length; i++) {
                result[i] = (byte) (a[i] ^ b[i]);
            }
            return result;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
        private byte[] unusedFunction4() {
        byte[] block = {0x66, 0x67, 0x68, 0x69};
                 return unusedFunction4(block);
    }
    private byte[] unusedFunction4(byte[] block) {
        try {
            byte[] result = block;
            
            return result;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """
    ]
