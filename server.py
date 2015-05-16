"""Server. Independent server process which is part of a set of
servers which make up a (simulated) test-system. The server
implements a very simple half-duplex protocol::

    Coordinator request     Server response     Server action
    HELO                    OLEH                -
    ID                      ID <id-string>      -
    QUIT                    -                   Quits

A new socket connection must be opened for each request-response.
"""

import time
import socket


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


class Server(object):
    """Simple TCP server."""
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port

    def run(self):
        """Main server process. Listen for socket connections,
        process one incoming command, respond and drop connection."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, int(self.port)))
        s.listen(1)
        while 1:
            self.conn, self.addr = s.accept()
            data = self.conn.recv(1024)
            data = data.replace('\n', '')
            if data == "HELO":
                self.conn.send("OLEH\n")
            elif data == "ID":
                self.conn.send("ID {0}\n".format(self.name))
            elif data == "QUIT":
                break
            self.conn.close()
        self.conn.close()


# Test suite
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port')
    parser.add_argument('name')
    args = parser.parse_args()
    Server(args.name, args.host, args.port).run()


if __name__ == "__main__":
    main()

