"""Local network monitor. Python standard library only."""
import json, sqlite3, threading, time, socket, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'health.db'
STOP = threading.Event()

def connection():
    return sqlite3.connect(DB, timeout=10)

def initialize():
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY, target TEXT, checked_at TEXT, status TEXT, latency REAL, detail TEXT)')

def probe(target):
    start = time.perf_counter()
    try:
        if target['type'] == 'tcp':
            with socket.create_connection((target['host'], int(target['port'])), timeout=5):
                pass
            detail = 'TCP connection established'
        elif target['type'] == 'http':
            request = urllib.request.Request(target['url'], headers={'User-Agent': 'NetPulse/1.0'})
            with urllib.request.urlopen(request, timeout=5) as response:
                detail = f'HTTP {response.status}'
        else:
            raise ValueError('Unsupported target type')
        latency = round((time.perf_counter() - start) * 1000, 1)
        return ('slow' if latency > 1000 else 'up', latency, detail)
    except (OSError, ValueError, urllib.error.URLError) as error:
        return ('down', None, str(error))

def collect(targets):
    for target in targets:
        status, latency, detail = probe(target)
        with connection() as db:
            db.execute('INSERT INTO checks(target,checked_at,status,latency,detail) VALUES(?,?,?,?,?)',
                       (target['name'], datetime.now(timezone.utc).isoformat(), status, latency, detail))
            db.execute('DELETE FROM checks WHERE id NOT IN (SELECT id FROM checks ORDER BY id DESC LIMIT 10000)')

def snapshot(targets):
    result = []
    with connection() as db:
        db.row_factory = sqlite3.Row
        for target in targets:
            rows = [dict(row) for row in db.execute('SELECT * FROM checks WHERE target=? ORDER BY id DESC LIMIT 60', (target['name'],))]
            result.append({**target, 'history': rows[::-1], 'latest': rows[0] if rows else None,
                           'uptime': round(100 * sum(row['status'] != 'down' for row in rows) / len(rows), 1) if rows else None})
    return {'targets': result, 'interval': 30, 'generated_at': datetime.now(timezone.utc).isoformat()}

def monitor(targets):
    while not STOP.is_set():
        collect(targets)
        STOP.wait(30)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

    def do_GET(self):
        if self.path == '/api/health':
            body = json.dumps(snapshot(TARGETS)).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith('/api/'):
            self.send_error(404)
        else:
            super().do_GET()

if __name__ == '__main__':
    TARGETS = json.loads((ROOT / 'targets.json').read_text())
    initialize()
    threading.Thread(target=monitor, args=(TARGETS,), daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', 8000), Handler)
    print('NetPulse → http://localhost:8000  |  Ctrl+C to stop', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        STOP.set()
        server.server_close()
