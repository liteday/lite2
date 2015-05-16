"""XML file reader which imports a test-system specification in XML format
into a database. Can be invoked as a CLI, or imported and used as a module.
"""

from lxml import etree
import database
import os


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


class Reader(object):
    """Translates an XML file into a database."""

    def __init__(self, name, tsdb):
        """Read in the XML specification. Link the database."""
        self.tree = etree.parse(open(name, 'rb'))
        self.tsdb = tsdb

    def save(self):
        """Save the XML specification to the datbase."""
        lastts = None
        for tss in self.tree.getroot():
            if tss != lastts:
                ts_id = self.tsdb.write_system(tss.get('name'))
                lastts = tss
            for sys in tss:
                self.tsdb.write_server(ts_id, sys.get('addr'), sys.get('name'))
        self.tsdb.commit()


def import_xml(xmlname, dbname, create=False):
    """API function which can be called to read an XML file into a database.
    Add to the database by default, or if create is True,
    clear database first."""
    create = create or (not os.path.exists(dbname))
    tsdb = database.Database(dbname)
    if create:
        tsdb.create()
    rdr = Reader(xmlname, tsdb)
    rdr.save()


def do_list(args):
    """CLI list command. List database contents to stdout."""
    tsdb = database.Database(args.db)
    for sys in tsdb.read_all():
        for srv in sys:
            print '#{0:3d} ts={1} addr={2} name={3}'.format(
                sys.tsid, sys.name, srv.addr, srv.name)


def do_add(args):
    """CLI add command. Read XML file and store in database,
    optionally clearing database first."""
    import_xml(args.xml, args.db, args.create)


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
    p_add.add_argument('xml', help='Input XML file')
    p_list = sub.add_parser('list', help='List data in database')
    p_list.set_defaults(func=do_list)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

