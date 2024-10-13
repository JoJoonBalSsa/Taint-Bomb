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

    dummy_list = [
        """
    private List<byte[]> unusedFunction0(byte[] key = {0x66}, int rounds = 7) {
        try{ 
            int keyLength = key.length;
            List<byte[]> schedule = new ArrayList<>();
            schedule.add(key);
    
            for (int i = 1; i < rounds; i++) {
                byte[] prevKey = schedule.get(schedule.size() - 1);
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
        
                schedule.add(newKey);
            }
        
            return schedule;
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
    private byte[] unusedFunction1(byte[] a = {0x99, 0x108, 0x103, 0x111}, byte[] b = {0x66, 0x88, 0x69}) {
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
    public byte[] unusedFunction2(byte[] data = {0x66, 0x67, 0x68, 0x69}) {
        try {
            int i = data.length - 1;
            while (i >= 0 && data[i] == 0) {
                i--;
            }
            return Arrays.copyOf(data, i + 1);
        }
        catch (Exception e){
            throw new RuntimeException("Decryption failed", e);
        }
    }
    """,
        """
    private byte[] unusedFunction3(byte[] a = {0x78, 0x87}, byte[] b = {0x88}) {
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
    private byte[] unusedFunction4(byte[] block = {0x88}) {
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
