from proxy.util.logger import Logger
from proxy.spheniscidae import Spheniscidae
import asyncio

class ProxyServer:


    def __init__(self, config):
        self.config = config
        self.client_class = Spheniscidae
        self.logger = Logger()
        
        
    async def start(self):
        self.server = await asyncio.start_server(
            self.client_connected, self.config.address,
            self.config.port
        )
        self.logger.info('Booting Proxy')
        self.logger.info(f'Listening on {self.config.address}:{self.config.port}')
        
        
        async with self.server:
            await self.server.serve_forever()
        
        
    async def client_connected(self, reader, writer):
        client_object = self.client_class(self, reader, writer)
        await client_object.run()