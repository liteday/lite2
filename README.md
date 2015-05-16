# LITE2

The Little IT Emulator (v1.0).

LITE is a work exercise with no practical functionality.

LITE reads a system specification from a database and presents a web-page where
systems may be deployed, checked and stopped.

To run:

    python web.py

To see more command-line options:

    python web.py --help

LITE requires a database. By default this is `sample.db`. If a database does not
exist, LITE will attempt to build one from an XML file of the same base name as
the database (`sample.xml`).

Visit http://localhost:50000/ to access a web-page where systems may be
deployed, checked and stopped.

To manually build a database from an XML file, or to add the contents of an XML
file to an existing database:

    python reader.py


