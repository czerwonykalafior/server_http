import os
import socket
import threading


def recvuntil(sock, text):
    d = ""
    while d.find(text) == -1:
        try:
            dnow = sock.recv(1).decode("utf-8")
            if len(dnow) == 0:
                print("-=(warning)=- recvuntil() failed at recv")
                print("Last received data:")
                print(d)
                return False
        except socket.error as msg:
            print("-=(warning)=- recvuntil( failed:", msg)
            print("Last received data: ")
            print(d)
            return False
        d += dnow
    return d


def recvall(sock, n):
    d = ""
    while len(d) != n:
        try:
            dnow = sock.recv(n - len(d))
            if len(dnow) == 0:
                print("-=(warning)=- recvuntil() failed at recv")
                print("Last received data:")
                print(d)
                return False
        except socket.error as msg:
            print("-=(warning)=- recvuntil( failed:", msg)
            print("Last received data: ")
            return False
        d += dnow
    return d


# Proxy object for sockets.
class Gsocket(object):
    def __init__(self, *p):
        self._sock = socket.socket(*p)

    def __getattr__(self, name):
        return getattr(self._sock, name)

    def recvall(self, n):
        return recvall(self._sock, n)

    def recvuntil(self, txt):
        return recvuntil(self._sock, txt)


class Handler(threading.Thread):
    def __init__(self, s, addr):
        super(Handler, self).__init__()

        self.s = s
        self.addr = addr

    def return_http(self, data, status=200, status_text="OK",
                    mime='aplication/binary'):

        # python 3 encoding got in the way
        response = {
            'f_line': "HTTP/1.1 %i %r\r\n" % (status, status_text),
            'c_type': "Content-Type: %s\r\n" % mime,
            'c_length': "Content-Length: %i\r\n" % len(data),
        }
        self.s.sendall(response['f_line'].encode())
        self.s.sendall(response['c_type'].encode())
        self.s.sendall(response['c_length'].encode())
        self.s.sendall("\r\n".encode())
        self.s.sendall(data)

    def run(self):
        data = recvuntil(self.s, "\r\n\r\n").splitlines()
        verb, path, ver = data[0].split(" ")
        # print("Method: %s, Path: %s, ver: %s" % (verb, path, ver))

        try:
            if ".." in path or not path.startswith("/"):
                raise Exception("bye")

            if path == "/":
                path = "/index.html"

            final_path = "public_html" + path
            with open(final_path, "rb") as f:
                d = f.read()
            # print("Resource:", d)

            _, ext = os.path.splitext(path)

            mime = {
                ".html": "text/html;charset=utf-8",
                ".png": "image/png",
            }

            mtype = "application/binary"

            if ext in mime:
                mtype = mime[ext]

            self.return_http(d, mime=mtype)

        except:
            self.return_http("No!", status=403, status_text="Forbidden", mime="text/plain")

        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()


def main():
    # Create a socket. Params: Address (and protocol) families, socket type (protocol)
    server = Gsocket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to given interface and port
    server.bind(("0.0.0.0", 8080))
    # listen on the socket queueing upcoming connections
    server.listen(5)

    while True:
        conn, addr = server.accept()
        # print("[  INFO  ] New connection: %s:%i" % addr)

        th = Handler(conn, addr)
        th.deamon = False
        th.start()


if __name__ == '__main__':
    main()
