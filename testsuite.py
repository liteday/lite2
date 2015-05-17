"""Test suite for LITE."""

import unittest
import sqlite3
from lxml import etree
import os

import reader


class ReaderTests(unittest.TestCase):
    """Test reader module.
    Test systems are generated from a specification with the following format.
    The specification is a sequence of int values. Each represents a
    test-system, and the int value represents the number of servers in that
    test-system. The test-system and server names are procedurally generated.
    The addresses are localhost:<port>, where port numbers are allocated
    sequentially from a provided base."""

    def setUp(self):
        """Setup support files for reader tests."""
        self.xml = 'test.xml'
        self.dbname = 'test.db'
        self.spec = (10, 15, 8, 23)
        #self.spec = (3, 2, 4)
        self.create_xml(self.spec)
        if os.path.exists(self.dbname):
            os.unlink(self.dbname)

    def create_xml(self, spec, port_base=2050, ts_base=0):
        """Create an XML file based on a specification. See gen_xml() for
        details of spec."""
        fpw = open(self.xml, 'wb')
        fpw.write(self.gen_xml(spec, port_base, ts_base))
        fpw.close()

    @staticmethod
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
        self.create_xml(
            self.spec, port_base=2050+sum(self.spec), ts_base=len(self.spec))
        spec = self.spec + self.spec
        reader.import_xml(self.xml, self.dbname, create=False)
        self.assertTrue(os.path.exists(self.dbname))
        self.check_db(spec)

