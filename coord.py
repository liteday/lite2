"""Coordinator for sub-processes which represent very simple servers.
Each server can respond to a number of text commands over a TCP connection.
"""

import subprocess
import socket
import time


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


class Coordinator(object):
    """Coordinates a number of servers."""
    def ping(self, host, port):
        """Send a HELO message to a server and expect OLEH in reply."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, int(port)))
        s.send("HELO\n")
        data = s.recv(1024) # Naive TCP stream handling ... :-)
        s.close()
        return data == "OLEH\n"

    @staticmethod
    def splitaddr(addr):
        """Split an IP address / domain name in to host:port, or set
        port to 20000 by default if not specified."""
        host, port = addr, '20000'
        if addr.find(':') >= 0:
            host, port = addr.split(':', 1)
        return host, port

    def ask_id(self, host, port):
        """Request the ID of a server by sending the ID message. The
        server will response with ID <id-string>."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            s.send("ID\n")
            data = s.recv(1024) # Naive TCP stream handling ... :-)
            s.close()
            sid = data[3:-1]
            return sid
        except Exception: # Extremely basic error checking
            return -1

    def quit(self, host, port):
        """Send the QUIT message to a server. It will shutdown
        immediately without sending a response."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            s.send("QUIT\n")
            time.sleep(0.1)
            s.close()
            return True
        except Exception: # Extremely basic error checking
            return False

    # The following methods represent the public API of Controller.

    def deploy(self, ts, name, addr):
        """Launch a new server as a sub-process, using the specified address."""
        if addr.find(':') >= 0:
            host, port = addr.split(':', 1)
        subprocess.Popen(['python', 'server.py', host, port, name], stdin=None, stdout=None, stderr=None)
        time.sleep(0.1)
        if not self.ping(host, port):
            return "No contact with test system #{0} '{1}', server '{2}' @{3}".format(ts[0], ts[1], name, addr)
        return "Deployed test system #{0} '{1}', server '{2}' @{3}".format(ts[0], ts[1], name, addr)

    def bool_check(self, ts_id, addr):
        """Attempt to communicate with a server. Return True if OK, False otherwise."""
        host, port = self.splitaddr(addr)
        status = self.ask_id(host, port)
        return (not isinstance(status, int)) or status != -1

    def check(self, ts_id, addr):
        """Request the ID os a server."""
        if addr.find(':') >= 0:
            host, port = addr.split(':', 1)
        sid = self.ask_id(host, port)
        return "Checking test system #{0}, server @{1}: ID={2}".format(ts_id, addr, sid)

    def stop(self, ts_id, addr):
        """Stop a running server. Does nothing if the server isn't running."""
        if addr.find(':') >= 0:
            host, port = addr.split(':', 1)
        status = self.quit(host, port)
        return "Stopped test system #{0}, server @{1}: stop={2}".format(ts_id, addr, status)


# Test suite
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    addr = 'localhost:{0}'.format(args.port)
    c = Coordinator()
    print c.deploy((1, 'ts1'), 'ts1:lawrence', addr)
    if not c.quit(*addr.split(':')):
        print "Attempt to shutdown server failed"

