"""Web server for LITE.
Reads database and presents the contents as a web-page.
If <name>.db file not found, attempts to create from <name>.xml.
Processes requests to deploy, check and stop test-systems.
"""

from flask import Flask
from jinja2 import Environment, FileSystemLoader
import database
import coord
import os


__author__ = "Rory MacHale"
__version__ = "1.0"
__date__ = "2015-05-15"


app = Flask(__name__)
dbname = None


def setup():
    """Create support objects for each web-page."""
    tsdb = database.Database(dbname)
    env = Environment(loader=FileSystemLoader('./'))
    coo = coord.Coordinator()
    return tsdb, env, coo


def talk(func, tsdb, env, ts_id):
    """Communicate with the coordinator and display web-page with
    results for a single specified test-system ts_id."""
    servers = tsdb.read_servers(ts_id)
    status = [func(ts_id, server[2]) for server in servers]
    tmpl = env.get_template('go.html')
    return tmpl.render(status=status)


@app.route('/')
def index():
    """Display the main status page, with clickable links, for LITE."""
    tsdb, env, coo = setup()
    tsdb = database.Database(dbname)
    allsys = list(tsdb.read_all())
    status = {}
    for tsi in xrange(len(allsys)):
        tss = allsys[tsi]
        status.update({server.name: coo.bool_check(server.addr)
            for server in tss})
    tmpl = env.get_template('index.html')
    return tmpl.render(systems=allsys, status=status)


@app.route('/go/<int:ts_id>')
def go(ts_id):
    """Web-page invoked when test-system ts_id is to be deployed.
    Display status of outcome."""
    tsdb, env, coo = setup()
    tss = tsdb.read_system(ts_id)
    servers = tsdb.read_servers(ts_id)
    status = [coo.deploy(tss, server[3], server[2]) for server in servers]
    tmpl = env.get_template('go.html')
    return tmpl.render(status=status)


@app.route('/check/<int:ts_id>')
def check(ts_id):
    """Web-page invoked when test-system ts_id status is to be checked."""
    tsdb, env, coo = setup()
    return talk(coo.check, tsdb, env, ts_id)


@app.route('/stop/<int:ts_id>')
def stop(ts_id):
    """Web-page invoked when test-system ts_id is to be stopped."""
    tsdb, env, coo = setup()
    return talk(coo.stop, tsdb, env, ts_id)


def initialise(dbname, port):
    """Check database. If not found, look for <name>.xml corresponding
    to <name>.db database, and try to import the XML into the database
    automatically."""
    print
    if not os.path.exists(dbname):
        import reader
        path, _ = os.path.splitext(dbname)
        xmlname = path+'.xml'
        reader.import_xml(xmlname, dbname, create=True)
        print "** Created {0}".format(dbname)
    print "** Now browse to localhost:{0}".format(port)
    print


# Run flask webserver
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("LITE: Little IT Environment - emulator")
    parser.add_argument('-d', '--db', default='sample.db', help="SQLite DB filename")
    parser.add_argument('-p', '--port', default=50000, type=int, help="Web server port")
    args = parser.parse_args()
    dbname = args.db
    initialise(args.db, args.port)
    app.run(debug=True, port=args.port)

