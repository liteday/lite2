"""Database API for the test-system database."""


import sqlite3
from collections import namedtuple


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


# Represents a single server, with an (IP or domain) address and a name
Server = namedtuple('Server', ('addr', 'name'))


class SystemIterator(object):
    """Iterator for a System object. Iterates over the stored servers."""
    def __init__(self, system):
        self.system = system
        self.idx = 0

    def next(self):
        """Return next system."""
        if self.idx >= len(self.system):
            raise StopIteration
        sys = self.system.servers[self.idx]
        self.idx += 1
        return sys


class System(object):
    """Encapsulates a test-system, which contains a number of servers."""
    def __init__(self, tsid, name):
        self._tsid = tsid
        self._name = name
        self._servers = []

    def __repr__(self):
        return "System({}, {})".format(self._name, self._servers)

    def __len__(self):
        return len(self._servers)

    def __getitem__(self, i):
        """Sequence access to the stored servers."""
        return self._servers[i]

    def __iter__(self):
        """Obtain an iterator over the stored servers."""
        return SystemIterator(self)

    @property
    def tsid(self):
        return self._tsid

    @property
    def name(self):
        return self._name

    @property
    def servers(self):
        return self._servers

    def add_server(self, addr, name):
        """Add a new server, with associated address and name."""
        self.servers.append(Server(addr, name))


class Database(object):
    """Encapsulates an sqlite3 database storing test-systems and servers."""
    def __init__(self, name):
        self.dbc = sqlite3.connect(name)

    def create(self):
        """Drop an existing database and create empty tables. There are two
        tables::

            system - stores test-systems with their names
            server - stores servers with their names, and addresses

        There is a 1:N relation between system and server rows."""
        cur = self.dbc.cursor()
        cur.execute("DROP TABLE IF EXISTS system")
        cur.execute("CREATE TABLE system (id integer primary key, name varchar(32))")
        cur.execute("DROP TABLE IF EXISTS server")
        cur.execute("CREATE TABLE server"+
            "(id integer primary key, system_id integer, addr varchar(32), name varchar(32))")
        self.dbc.commit()

    def write_system(self, name):
        """Add a new test-system entry. Returns the id value so it may be
        used as a foreign key.
        NB: You must exlicitly call db.commit() to save changes."""
        cur = self.dbc.cursor()
        cur.execute("INSERT INTO system (name) VALUES (?)", (name,))
        return cur.lastrowid

    def write_server(self, system_id, addr, name):
        """Add a new server entry. Requires the foreign key (id) of the
        associated test-system.
        NB: You must exlicitly call db.commit() to save changes."""
        cur = self.dbc.cursor()
        cur.execute("INSERT INTO server (system_id, addr, name) VALUES (?, ?, ?)",
            (system_id, addr, name))

    def read_system(self, system_id):
        """Returns the test-system name corresponding to system_id."""
        cur = self.dbc.cursor()
        cur.execute("SELECT * from system WHERE id=?", (system_id,))
        return cur.fetchone()

    def read_servers(self, system_id):
        """Generator for all servers associated with system_id."""
        cur = self.dbc.cursor()
        cur.execute("SELECT * FROM server WHERE system_id=?", (system_id,))
        for row in cur:
            yield row

    def read_all(self):
        """Generator for all test-systems. Each test-system is returned as
        a System object, with associated servers already added."""
        cur = self.dbc.cursor()
        cur.execute("SELECT * FROM system")
        for row in cur:
            sys = System(*row)
            for srv in self.read_servers(row[0]):
                sys.add_server(*srv[2:])
            yield sys

    def commit(self):
        """Commit changes to the database. This is not done automatically within
        the database object, as committing after every change will very
        significantly slow database updates. So manual commit is required from
        the application when updates are complete."""
        self.dbc.commit()

