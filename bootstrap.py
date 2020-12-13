  
import argparse
import asyncio
import logging

from proxy import ProxyServer

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Boot a Houdini server')
    parser.add_argument('type', action='store', default='login',
                        choices=['login', 'world'], help='Name of the server to boot')

    parser.add_argument('-n', '--name', action='store', help='Houdini server name')
    parser.add_argument('-a', '--address', action='store', default='0.0.0.0',
                        help='Houdini server address')
    parser.add_argument('-p', '--port', action='store', help='Proxy server port', default=None, type=int)
    parser.add_argument('-s', '--server', action='store', help='Proxy server Destination', default='newcp.net', type=str)


    args = parser.parse_args()

    args.port = args.port if args.port else 9875 if args.type == 'world' else 6112


    factory_instance = ProxyServer(args)
    try:
        asyncio.run(factory_instance.start())
    except KeyboardInterrupt:
        factory_instance.logger.info('Shutting down...')