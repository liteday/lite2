"""Test suite for LITE."""

import unittest
import threading
import socket
from hashlib import sha256
import sqlite3
from lxml import etree # pragma: no cover
import time
import os

import reader
import coord
import database
import server
import web


SHA_INDEX_TMPL = "9ae200dde1dd0fabe4d55d7d1bc342fe0d62e1471e97f72dc8c1cf7e0dc52d31"
SHA_GO_TMPL = "dd28282ff76c760002e33b1a2c14c82267befa3752750b894bf53b21e17162de"
SHA_INDEX_PAGE = "9bb2f95a95d14e39a451d809e7c1b648064f4730a4efed2c129f1a08f45da159"
SHA_DEPLOY_PAGE = "b7e118a695530f5f9ddd24030b4bb408eba1e1bb9a41de921a5771e40e6309a3"
SHA_CHECK_PAGE = "827c5f0237a70f1d7899d918a7bbe241c4775fbba3a648f3a68e6af5197d871d"
SHA_STOP_PAGE = "748ef386d245cc0427d1d5545e24168eb6b6a392aa46e7aae66129335a6bcbf8"


def sha(data, hex=False):
    return sha256(data).digest() if not hex else sha256(data).hexdigest()


def create_xml(name, spec, port_base=2050, ts_base=0):
    """Create an XML file based on a specification. See gen_xml() for
    details of spec."""
    fpw = open(name, 'wb')
    fpw.write(gen_xml(spec, port_base, ts_base))
    fpw.close()


def gen_xml(spec, port_base=2050, ts_base=0):
    """Generate XML from a specification. spec is a test-system
    specification."""
    root = etree.Element('testsystem')
    porti = port_base
    for tsi in xrange(len(spec)):
        idx = tsi + ts_base
        tss = etree.Element('system', name="ts{0}".format(idx))
        for ssi in xrange(spec[tsi]):
            tss.append(etree.Element('server', addr="localhost:{0}".format(porti),
                name="ts{0}:test{0}-{1}".format(idx, ssi)))
            porti += 1
        root.append(tss)
    return etree.tostring(root, pretty_print=True)


class ReaderTests(unittest.TestCase):
    """Test reader module. Also exercises the supporting database module.
    Test systems are generated from a specification with the following format.
    The specification is a sequence of int values. Each represents a
    test-system, and the int value represents the number of servers in that
    test-system. The test-system and server names are procedurally generated.
    The addresses are localhost:<port>, where port numbers are allocated
    sequentially increasing from a provided base."""

    def setUp(self):
        """Setup support files for reader tests."""
        self.xml = 'test.xml'
        self.dbname = 'test.db'
        self.spec = (10, 15, 8, 23)
        create_xml(self.xml, self.spec)
        if os.path.exists(self.dbname):
            os.unlink(self.dbname)

    def check_db(self, spec, port_base=2050, dbname='test.db'):
        """Check database is consistent with a test-system specification (spec).
        In particular, a database generated from XML produced by the gen_xml()
        with the same spec should match. Check database contains matching
        entries with procedurally-generated names as per gen_xml()."""
        dbc = sqlite3.connect(dbname)
        cur = dbc.cursor()
        cur.execute("SELECT COUNT(*) FROM system")
        self.assertEqual(int(cur.fetchone()[0]), len(spec))
        cur.execute("SELECT * FROM system")
        for idx, row in zip(range(len(spec)), cur):
            self.assertEqual("ts{0}".format(idx), row[1])
        porti = port_base
        for tsi in xrange(len(spec)):
            tss = spec[tsi]
            cur.execute("SELECT COUNT(*) FROM server WHERE system_id=?",
                (tsi+1,))
            self.assertEqual(int(cur.fetchone()[0]), tss)
            cur.execute("SELECT * FROM server WHERE system_id=?", (tsi+1,))
            for idx, row in zip(range(tss), cur):
                name = "ts{0}:test{0}-{1}".format(tsi, idx)
                addr = "localhost:{0}".format(porti)
                self.assertEqual(addr, row[2])
                self.assertEqual(name, row[3])
                porti += 1

    def test_create(self):
        """Create a database from an XML specification."""
        self.assertTrue(not os.path.exists(self.dbname))
        reader.import_xml(self.xml, self.dbname, create=True)
        self.assertTrue(os.path.exists(self.dbname))
        self.check_db(self.spec)

    def test_add(self):
        """Create a database from an XML specification and add a second XML specification."""
        self.assertTrue(not os.path.exists(self.dbname))
        reader.import_xml(self.xml, self.dbname, create=True)
        create_xml(
            self.xml, self.spec, port_base=2050+sum(self.spec), ts_base=len(self.spec))
        spec = self.spec + self.spec
        reader.import_xml(self.xml, self.dbname, create=False)
        self.assertTrue(os.path.exists(self.dbname))
        self.check_db(spec)

    def test_gen(self):
        """Check that generating XML from a database is same as XML used to 
        create database."""
        self.assertTrue(not os.path.exists(self.dbname))
        data1 = gen_xml(self.spec)
        reader.import_xml(self.xml, self.dbname, create=True)
        self.assertTrue(os.path.exists(self.dbname))
        xml = reader.XMLProcessor(None, database.Database(self.dbname))
        data2 = xml.gen_xml()
        self.assertEqual(sha(data1), sha(data2))


class CoordTests(unittest.TestCase):
    """Coordinator test suite."""

    def setUp(self):
        """Create a coordinator for tests."""
        self.coo = coord.Coordinator()

    def test_deploy(self):
        """Deploy a server, check its ID and shut it down."""
        self.coo.deploy((0, 'ts0'), 'test-coord', 'localhost:2050')
        self.assertTrue(self.coo.bool_check('localhost:2050'))
        self.assertEqual(self.coo.ask_id('localhost', '2050'), 'test-coord')
        self.coo.stop(0, 'localhost:2050')
        self.assertFalse(self.coo.bool_check('localhost:2050'))


class ServerThread(threading.Thread):
    def run(self):
        self.server = server.Server('test-server', 'localhost', '2050')
        self.server.run()


class ServerTests(unittest.TestCase):
    """Server test suite. Runs a standalone server in a thread."""

    def setUp(self):
        """Start server thread."""
        self.host = 'localhost'
        self.port = '2050'
        srv = ServerThread()
        srv.daemon = True
        srv.start()
        time.sleep(0.1) # Allow time for server (in thread) to start
    
    def tearDown(self):
        """Tell server to shutdown."""
        self.req_resp('QUIT')

    def req_resp(self, cmd):
        """Open a connection, send a request, get a response, close connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, int(self.port)))
            sock.send("{0}\n". format(cmd))
            data = sock.recv(1024) # Naive TCP stream handling ... :-)
            sock.close()
            return data
        except IOError:
            return -1

    def test_helo(self):
        """Try a HELO command."""
        resp = self.req_resp('HELO')
        self.assertEqual(resp, 'OLEH\n')

    def test_id(self):
        """Try an ID command."""
        resp = self.req_resp('ID')
        self.assertEqual(resp, 'ID test-server\n')

    def test_quit(self):
        """Try quitting (exception check only)."""
        self.req_resp('QUIT')


class WebTests(unittest.TestCase):
    """Web test suite.
    Tests are numbered to ensure they are carried out in a specific order."""

    def setUp(self):
        """Importing web as a module means dbname global isn't set so do here."""
        self.xml = 'test.xml'
        self.dbname = 'test.db'
        self.spec = (10, 15, 8, 23)
        create_xml(self.xml, self.spec)
        reader.import_xml(self.xml, self.dbname, create=True)
        web.dbname = self.dbname

    def tearDown(self):
        """Try to ensure all processes are shutdown, even if the tests failed."""
        dbc = sqlite3.connect(web.dbname)
        cur = dbc.execute('SELECT * FROM system')
        allsys = (row[0] for row in cur)
        for tsi in allsys:
            web.stop(tsi)

    @staticmethod
    def shafile(name):
        """Calculates SHA256 (as hex string) of data in a file."""
        fpc = open(name, 'rb')
        data = fpc.read()
        fpc.close()
        return sha(data, hex=True)

    def test_0_templates(self):
        """Check SHA checksum for raw templates.
        If they don't match, none of the other tests in WebTest will work,
        because the template has changed."""
        self.assertEqual(self.shafile('index.html'), SHA_INDEX_TMPL,
             "index.html template changed: WebTest test SHA values won't match")
        self.assertEqual(self.shafile('go.html'), SHA_GO_TMPL,
             "go.html template changed: WebTest test SHA values won't match")

    def test_1_index(self):
        """Check root page."""
        self.assertEqual(sha(web.index(), hex=True), SHA_INDEX_PAGE)

    def test_2_deploy(self):
        """Simulate click on "Deploy" for first test-system."""
        self.assertEqual(sha(web.go(1), hex=True), SHA_DEPLOY_PAGE)

    def test_3_check(self):
        """Simulate click on "Check" for first test-system."""
        self.assertEqual(sha(web.check(1), hex=True), SHA_CHECK_PAGE)

    def test_4_stop(self):
        """Simulate click on "Stop" for first test-system."""
        self.assertEqual(sha(web.stop(1), hex=True), SHA_STOP_PAGE)
        

if __name__ == "__main__":
    unittest.main()

