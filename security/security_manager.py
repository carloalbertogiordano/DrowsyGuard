import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


class SecurityManager:

    IV_SIZE = 16

    def __init__(self, key):
        self.key = key.encode('utf-8')
        self.block_size = AES.block_size

    def encrypt_data(self, data_dict):
        json_data = json.dumps(data_dict).encode('utf-8')
        IV = get_random_bytes(SecurityManager.IV_SIZE)

        cypher_obj = AES.new(self.key, AES.MODE_CBC, IV)
        padded_data = pad(json_data, self.block_size)

        return base64.b64encode(IV+cypher_obj.encrypt(padded_data)).decode('utf-8')


    def decrypt_data(self, encrypted_str):

        encrypted_data = base64.b64decode(encrypted_str)

        IV = encrypted_data[:SecurityManager.IV_SIZE]

        decypher_obj = AES.new(self.key, AES.MODE_CBC, IV)
        json_data_padded = decypher_obj.decrypt(encrypted_data[SecurityManager.IV_SIZE:])
        json_data = unpad(json_data_padded, self.block_size).decode('utf-8')

        return json.loads(json_data)