public static List<byte[]> keySchedule(byte[] key, int rounds) throws NoSuchAlgorithmException {
        List<byte[]> schedule = new ArrayList<>();
        schedule.add(key);

        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        for (int i = 1; i < rounds; i++) {
            byte[] newKey = digest.digest(schedule.get(schedule.size() - 1));
            schedule.add(Arrays.copyOf(newKey, 16)); // 16바이트로 제한
        }
        return schedule;
    }

    public static byte[] inverseFeistelNetwork(byte[] block, byte[] roundKey) {
        byte[] left = Arrays.copyOfRange(block, 0, 8);
        byte[] right = Arrays.copyOfRange(block, 8, 16);
        byte[] f_result = new byte[8];
        for (int i = 0; i < 8; i++) {
            f_result[i] = (byte) (left[i] ^ roundKey[i]);
        }
        byte[] newLeft = new byte[8];
        for (int i = 0; i < 8; i++) {
            newLeft[i] = (byte) (right[i] ^ f_result[i]);
        }
        return concatenate(newLeft, left);
    }

    public static byte[] keyDecryptAlg(byte[] data, byte[] key, int rounds) throws NoSuchAlgorithmException {
        List<byte[]> keySched = keySchedule(key, rounds);
        byte[] decrypted = new byte[data.length];
        for (int i = 0; i < data.length; i += 16) {
            byte[] block = Arrays.copyOfRange(data, i, i + 16);
            for (int j = keySched.size() - 1; j >= 0; j--) {
                block = inverseFeistelNetwork(block, keySched.get(j));
            }
            System.arraycopy(block, 0, decrypted, i, 16);
        }
        return removePadding(decrypted);
    }

    public static byte[] concatenate(byte[] a, byte[] b) {
        byte[] result = new byte[a.length + b.length];
        System.arraycopy(a, 0, result, 0, a.length);
        System.arraycopy(b, 0, result, a.length, b.length);
        return result;
    }

    public static byte[] removePadding(byte[] data) {
        int i = data.length - 1;
        while (i >= 0 && data[i] == 0) {
            i--;
        }
        return Arrays.copyOf(data, i + 1);
    }

    public static byte[] keyDecrypt(String key, String key2) throws NoSuchAlgorithmException {
        byte[] deckey = Base64.getDecoder().decode(key);
        byte[] deckey2 = Base64.getDecoder().decode(key2);

        byte[] decrypted_key = keyDecryptAlg(deckey, deckey2, 16);

        return decrypted_key;
    }




