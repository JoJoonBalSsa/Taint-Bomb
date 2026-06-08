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
    """,
        """
    private int unusedFunction5() {
        int[] state = {0x9e, 0x37, 0x79, 0xb9};
        return unusedFunction5(state, 16);
    }

    private int unusedFunction5(int[] seed, int rounds) {
        try {
            int h = 0x811c9dc5;
            for (int r = 0; r < rounds; r++) {
                for (int i = 0; i < seed.length; i++) {
                    h ^= (seed[i] + r) & 0xff;
                    h *= 0x01000193;
                    h = (h << 13) | (h >>> 19);
                }
            }
            return h;
        }
        catch (Exception e){
            throw new RuntimeException("Mixing failed", e);
        }
    }
    """,
        """
    private long unusedFunction6() {
        long[] vec = {1469598103934665603L, 1099511628211L};
        return unusedFunction6(vec);
    }

    private long unusedFunction6(long[] vec) {
        try {
            long acc = vec[0];
            for (int i = 1; i < vec.length; i++) {
                acc ^= vec[i];
                acc *= 0x100000001b3L;
                acc ^= (acc >>> 32);
            }
            return acc;
        }
        catch (Exception e){
            throw new RuntimeException("Hashing failed", e);
        }
    }
    """,
        """
    private char[] unusedFunction7() {
        char[] table = {'a', 'f', '3', '9', 'z'};
        return unusedFunction7(table, 5);
    }

    private char[] unusedFunction7(char[] table, int n) {
        try {
            char[] out = new char[n];
            int idx = 7;
            for (int i = 0; i < n; i++) {
                idx = (idx * 31 + 17) & 0x7fffffff;
                out[i] = table[idx % table.length];
            }
            return out;
        }
        catch (Exception e){
            throw new RuntimeException("Encoding failed", e);
        }
    }
    """,
        """
    private byte[] unusedFunction8() {
        byte[] iv = {0x10, 0x32, 0x54, 0x76, (byte) 0x98};
        return unusedFunction8(iv);
    }

    private byte[] unusedFunction8(byte[] iv) {
        try {
            byte[] out = new byte[iv.length];
            byte carry = 1;
            for (int i = iv.length - 1; i >= 0; i--) {
                int v = (iv[i] & 0xff) + (carry & 0xff);
                out[i] = (byte) (v & 0xff);
                carry = (byte) (v >>> 8);
            }
            return out;
        }
        catch (Exception e){
            throw new RuntimeException("Counter failed", e);
        }
    }
    """,
        """
    private int unusedFunction9() {
        int[] lut = {2, 3, 5, 7, 11, 13, 17, 19};
        return unusedFunction9(lut, 23);
    }

    private int unusedFunction9(int[] lut, int salt) {
        try {
            int crc = 0xffffffff;
            for (int i = 0; i < lut.length; i++) {
                crc ^= (lut[i] ^ salt);
                for (int b = 0; b < 8; b++) {
                    int mask = -(crc & 1);
                    crc = (crc >>> 1) ^ (0xedb88320 & mask);
                }
            }
            return ~crc;
        }
        catch (Exception e){
            throw new RuntimeException("Checksum failed", e);
        }
    }
    """
    ]