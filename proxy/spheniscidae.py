from proxy.crypto import AESCipher
from nacl.public import PrivateKey, PublicKey, Box
from asyncio import CancelledError, IncompleteReadError, LimitOverrunError
import asyncio
import nacl.utils
import nacl
import base64
import re

class Spheniscidae:
    
    Delimiter = b'\x00'
    
    def __init__(self, server, reader, writer):
    
        self.proxy_writer = None
        self.proxy_reader = None
        self.__reader = reader
        self.client_writer = writer
        
        self.key = PrivateKey.generate()
        self.client_key = None
        self.proxy_pub_key = self.key.public_key
        self.proxy_pub_key_b64 = self.key.public_key.encode(encoder=nacl.encoding.Base64Encoder)
        self.aes_key = None
        self.encrypt = False
        self.AES = None
        
        self.server = server
        self.logger = server.logger
        
    async def client_connected(self):
        self.proxy_reader, self.proxy_writer = await asyncio.open_connection(
                self.server.config.server, self.server.config.port
        )
        while not self.proxy_writer.is_closing():
            try:
                data = (await self.proxy_reader.readuntil(
                    separator=Spheniscidae.Delimiter)).decode()
                if data:
                    self.intercept_server(data)
                else:
                    self.proxy_writer.close()
                await self.proxy_writer.drain()
            except IncompleteReadError:
                self.proxy_writer.close()
            except CancelledError:
                self.proxy_writer.close()
            except ConnectionResetError:
                self.proxy_writer.close()
            except LimitOverrunError:
                self.proxy_writer.close()
            except BaseException as e:
                self.logger.exception(e.__traceback__)
        
    async def create_server(self):
        while not self.client_writer.is_closing():
        try:
            data = await self.__reader.readuntil(
                separator=Spheniscidae.Delimiter)
            if data:
                self.intercept_client(data.decode())
            else:
                self.client_writer.close()
            await self.client_writer.drain()
        except IncompleteReadError:
            self.client_writer.close()
        except CancelledError:
            self.client_writer.close()
        except ConnectionResetError:
            self.client_writer.close()
        except LimitOverrunError:
            self.client_writer.close()
        except BaseException as e:
            self.logger.exception(e.__traceback__)
        
    async def run(self):
        asyncio.create_task(self.connect_to_server())
        asyncio.create_task(self.client_connected())
     
    def intercept_client(self, data):
        if "<body action='encryption' r='0'>" in data:
            self.client_key = re.search(r"<key>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/key>", data).group(1)
            return self.send_server(f"\
                                    <msg t='sys'><body action='encryption' r='0'>\
                                    <key><![CDATA[{self.proxy_pub_key_b64.decode()}]]></key>\
                                    </body></msg>\
                                    \x00")
            
        if self.encrypt and not data.startswith('%xt') or not data.startswith('<'):
            data = self.AES.decrypt(data)
            
        self.send_server(data)
    
    def intercept_server(self, data):
        if 'encryption' in data:
            return self.get_AES_key(data)

        self.send_client(data)
    
    def get_AES_key(self, data):
        self.encrypt = True
        splitted = data.split('%')
        self.aes_key = self.decrypt_nacl_key(splitted[6], splitted[5])
        self.AES = AESCipher(self.aes_key)
        self.send_client_key()
    
    def send_client_key(self):
        client_pub = PublicKey(self.decode_public_key(self.client_key))
        nonce = nacl.utils.random(Box.NONCE_SIZE)
        box = Box(self.key, client_pub)
        message = base64.b64encode(box.encrypt(self.aes_key, nonce))
        self.send_xt_client('secondlayer', 'encryption', self.proxy_pub_key_b64.decode(), message.decode())

    def decode_public_key(self, key:str) -> bytes: 
        return base64.b64decode(key.encode('utf-8'))

    def decrypt_nacl_key(self, message, public_key): 
        l = self.base64(message)
        pub = PublicKey(self.base64(public_key))
        box = Box(self.key, pub)
        return box.decrypt(l)
    
    def send_xt(self, handler_id, *data, handler_ext='s'):
        xt_data = '%'.join(map(str, data))
        line = f'%xt%{handler_ext}%{handler_id}%-1%{xt_data}%'
        self.send_server(line + '\x00')    
        
    def send_xt_client(self, handler_id, *data):
        xt_data = '%'.join(map(str, data))
        line = f'%xt%{handler_id}%-1%{xt_data}%'
        self.send_client(line + '\x00')
    
    async def handle_xt_data(self, data):
        parsed_data = data.split('%')[1:-1]
        
        packet_id = parsed_data[1]
        packet = XTPacket(packet_id)
        packet_data = parsed_data[3:]

        await event.emit(packet, self, *packet_data)
    
    def send_client(self, data):
        if not self.client_writer.is_closing():
            self.client_writer.write(data.encode('utf-8'))
            if self.encrypt:
                data = self.AES.decrypt(data)
            self.logger.outgoing(data)
   
    def send_server(self, data):
        if not self.proxy_writer.is_closing():
            self.logger.inbound(data)
            if self.encrypt:
                data = self.AES.encrypt(data) + '\x00'
            
            self.proxy_writer.write(data.encode('utf-8'))