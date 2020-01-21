import argparse
import socket
import logging
import threading

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('simple_example')


def debug(func):
    def wrapper(*args, **kwargs):
        logger.debug('start execute \033[31m{}\033[0m'.format(func.__name__))
        result = func(*args, **kwargs)
        logger.debug('end execute \033[31m{}\033[0m'.format(func.__name__))
        return result
    return wrapper


class ProxyServer:
    def __init__(self, args):
        self.args = args
        self._init_server()

    @debug
    def _init_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.args.lhost, self.args.lport))
        print('[*] Listening on %s:%d' % (self.args.lhost, self.args.lport))
        self.server.listen(5)

    @debug
    def server_loop(self):
        while True:
            client_sock, addr = self.server.accept()
            print('[==>] Received incoming connection from %s:%d' %
                  (addr[0], addr[1]))

            p = threading.Thread(target=self.proxy_handler,
                                 args=(client_sock, self.args))
            p.start()

    @debug
    def proxy_handler(self, client_sock, args):
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.connect((args.rhost, args.rport))

        remote_thread = threading.Thread(
            target=self.transform_remote_data, args=(client_sock, remote_sock))

        local_thread = threading.Thread(
            target=self.transform_local_data, args=(client_sock, remote_sock))

        remote_thread.start()
        local_thread.start()
        remote_thread.join()
        local_thread.join()

    @debug
    def transform_local_data(self, client_sock, server_sock):
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            data = self.request_filter(data)
            server_sock.sendall(data)

    @debug
    def transform_remote_data(self, client_sock, server_sock):
        while True:
            data = server_sock.recv(1024)
            if not data:
                break
            data = self.response_filter(data)
            client_sock.sendall(data)

    @debug
    def response_filter(self, buffer):
        logger.debug(buffer)
        return buffer

    @debug
    def request_filter(self, buffer):
        logger.debug(buffer)
        return buffer

    @debug
    def recv_timeout(self, sock):
        buffer = b''
        try:
            sock.settimeout(2)
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data
        except socket.timeout:
            logger.debug('socket timeout')
        finally:
            sock.settimeout(None)
        return buffer


def main():

    parser = argparse.ArgumentParser(description="a tcp proxy tool")
    parser.add_argument('lhost')
    parser.add_argument('lport', type=int)
    parser.add_argument('rhost')
    parser.add_argument('rport', type=int)
    parser.add_argument('-rf', '--recv_first',
                        default=False, action='store_true')
    parser.add_argument('-d', '--debug', default=False,
                        action='store_true')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    s = ProxyServer(args)
    s.server_loop()


if __name__ == "__main__":
    main()
