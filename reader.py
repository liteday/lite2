"""XML file reader which imports a test-system specification in XML format
into a database. Can be invoked as a CLI, or imported and used as a module.
"""

from lxml import etree # pragme: no cover
import database
import os


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


class XMLProcessor(object):
    """Translates an XML file to/from a database."""

    def __init__(self, name, tsdb):
        """Set the XML filename and database object."""
        self.xmlname = name
        self.tsdb = tsdb

    def read_xml(self):
        """Read in the XML specification."""
        return etree.parse(open(self.xmlname, 'rb'))

    def write_xml(self):
        """Write XML generated from database to the XML file."""
        fpx = open(self.xmlname, 'wb')
        fpx.write(self.gen_xml())
        fpx.close()

    def save(self):
        """Save the XML specification to the datbase."""
        tree = self.read_xml()
        lastts = None
        for tss in tree.getroot():
            if tss != lastts:
                ts_id = self.tsdb.write_system(tss.get('name'))
                lastts = tss
            for sys in tss:
                self.tsdb.write_server(ts_id, sys.get('addr'), sys.get('name'))
        self.tsdb.commit()

    def gen_xml(self):
        """Generate XML from the database."""
        root = etree.Element('testsystem')
        allsys = self.tsdb.read_all()
        for tss in allsys:
            tse = etree.Element('system', name=tss.name)
            root.append(tse)
            for srv in tss:
                tse.append(
                    etree.Element('server', addr=srv.addr, name=srv.name))
        return etree.tostring(root, pretty_print=True)



def import_xml(xmlname, dbname, create=False):
    """API function which can be called to read an XML file into a database.
    Add to the database by default, or if create is True,
    clear database first."""
    create = create or (not os.path.exists(dbname))
    tsdb = database.Database(dbname)
    if create:
        tsdb.create()
    xml = XMLProcessor(xmlname, tsdb)
    xml.save()


def do_list(args): # pragma: no cover
    """CLI list command. List database contents to stdout."""
    tsdb = database.Database(args.db)
    for sys in tsdb.read_all():
        for srv in sys:
            print '#{0:3d} ts={1} addr={2} name={3}'.format(
                sys.tsid, sys.name, srv.addr, srv.name)


def do_add(args): # pragma: no cover
    """CLI add command. Read XML file and store in database,
    optionally clearing database first."""
    import_xml(args.xml, args.db, args.create)


def do_gen(args): # pragma: no cover
    """CLI gen command. Generate an XML file from the stored
    data in the database."""
    tsdb = database.Database(args.db)
    xml = XMLProcessor(args.xml, tsdb)
    xml.write_xml()


def main():
    """CLI: process command line. There are two sub-commands:
        add: to add an XML specification to the database
        list: to list the contents of the database
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test system XML reader")
    parser.add_argument('db', help='Target Database')
    sub = parser.add_subparsers()
    p_add = sub.add_parser('add', help='Add data from XML')
    p_add.set_defaults(func=do_add)
    p_add.add_argument('-c', '--create', action='store_true', help="Create new database")
    p_add.add_argument('-x', '--xml', default='sample.xml', help='Input XML file')
    p_list = sub.add_parser('list', help='List data in database')
    p_list.set_defaults(func=do_list)
    p_gen = sub.add_parser('gen', help='Generate XML from database')
    p_gen.set_defaults(func=do_gen)
    p_gen.add_argument('-x', '--xml', default='sample.xml', help='Input XML file')
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

