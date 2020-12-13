from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from base64 import b64decode, b64encode

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, data):
        try:
            iv = get_random_bytes(AES.block_size)
            self.cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return b64encode(iv + self.cipher.encrypt(pad(data.encode('utf-8'), 
                AES.block_size))).decode()
        except Exception:
            pass

    def decrypt(self, data):
        try:
            raw = b64decode(data)
            self.cipher = AES.new(self.key, AES.MODE_CBC, raw[:AES.block_size])
            return unpad(self.cipher.decrypt(raw[AES.block_size:]), AES.block_size).decode()
        except Exception:
            pass