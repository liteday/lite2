"""Server. Independent server process which is part of a set of
servers which make up a (simulated) test-system. The server
implements a very simple half-duplex protocol::

    Coordinator request     Server response     Server action
    HELO                    OLEH                -
    ID                      ID <id-string>      -
    QUIT                    -                   Quits

A new socket connection must be opened for each request-response.
"""

import socket


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


class Server(object):
    """Simple TCP server."""
    def __init__(self, name, host, port, debug=False):
        self.name = name
        self.host = host
        self.port = port
        self.conn = None
        self.addr = None
        self.debug = debug

    def recv(self, sock):
        """Receive a command from the socket."""
        self.conn, self.addr = sock.accept()
        data = self.conn.recv(1024)
        data = data.replace('\n', '')
        data = data.replace('\r', '') # Telnet will send \r as well
        if self.debug: # pragma: no cover
            print "server {0}: received {1}".format(self.name, data)
        return data

    def send(self, msg):
        """Send a response to the socket."""
        if self.debug: # pragma: no cover
            print "server {0}: sending {1}".format(self.name, msg)
        self.conn.send("{0}\n".format(msg))

    def run(self):
        """Main server process. Listen for socket connections,
        process one incoming command, respond and drop connection."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, int(self.port)))
        sock.listen(1)
        while 1:
            data = self.recv(sock)
            if data == "HELO":
                self.send("OLEH")
            elif data == "ID":
                self.send("ID {0}".format(self.name))
            elif data == "QUIT":
                if self.debug: # pragma: no cover
                    print "server {0}: quitting".format(self.name)
                break
            self.conn.close()
        self.conn.close()


def main():
    """Test suite."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port')
    parser.add_argument('name')
    args = parser.parse_args()
    Server(args.name, args.host, args.port).run()


if __name__ == "__main__":
    main()

