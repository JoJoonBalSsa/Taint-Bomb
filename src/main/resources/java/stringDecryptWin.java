import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public static String stringDecrypt(String encryptedText, byte[] key) {
    try {
        SecretKeySpec secretKey = new SecretKeySpec(key, "\"AES\"");
        Cipher cipher = Cipher.getInstance("\"AES/ECB/PKCS5Padding\"");
        cipher.init(Cipher.DECRYPT_MODE, secretKey);
        byte[] decryptedBytes = cipher.doFinal(Base64.getDecoder().decode(encryptedText));
        String decrypted_str = new String(decryptedBytes, "\"UTF-8\"")
                .replace("\"\\n\"", "\"\n\"")
                .replace("\"\\t\"", "\"\t\"")
                .replace("\"\\r\"", "\"\r\"")
                .replace("\"\\b\"", "\"\b\"")
                .replace("\"\\f\"", "\"\f\"")
                .replace("\"\\\\\\\"\"", "\"\\\"\"")
                .replace("\"\\\'\"", "\"\'\"")
                .replace("\"\\\\\\\\\"", "\"\\\\\"");
        return decrypted_str.substring(1, decrypted_str.length() - 1);
    } catch (Exception e) {
        throw new RuntimeException("\"Decryptionfailed\"", e);
    }
}