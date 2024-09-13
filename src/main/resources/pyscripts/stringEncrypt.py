import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from keyObfuscate import KeyObfuscate

class StringEncrypt:
    def __init__(self,Literals):
        self.encrypted_Literals = self.encrypt_string_literals(Literals)


    def encrypt_string(self, plain_text, key):
        cipher = AES.new(key, AES.MODE_ECB)
        padded_text = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted_text = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted_text).decode('utf-8')
    

    # 암호화
    def encrypt_string_literals(self, string_literals): 
        encrypted_Literals = []
        
        for p, c, strings,_ in string_literals:
            aes_key = os.urandom(16)
            enc_aes_key = os.urandom(8)

            ko = KeyObfuscate(aes_key, enc_aes_key)
            encrypted_aes_key = ko.enc_aes_key

            enc_aes_key = base64.b64encode(enc_aes_key).decode('utf-8').replace("=","")
            encrypted_aes_key = base64.b64encode(encrypted_aes_key).decode('utf-8').replace("=","")

            encrypted_Literals.append([p, c, encrypted_aes_key, enc_aes_key,[(self.encrypt_string(literal, aes_key), _) for literal, _ in strings],_])

        return encrypted_Literals
    

