# NetPulse — Network Health Dashboard

A local network monitoring project built with Python, SQLite, and vanilla HTML/CSS/JavaScript. No third-party packages required. Python 3.10+ recommended.

## Run on macOS

Extract the ZIP, open Terminal, and enter the project directory (you can type `cd ` and drag the folder into Terminal).

```bash
cd ~/Downloads/network-health-dashboard
python3 --version
python3 server.py
```

Open http://localhost:8000 in your browser. Keep Terminal running. Stop with Control+C. If Python is missing, install Python 3 from python.org. If port 8000 is in use, stop the other application or change the port in server.py.

## What it does

- Checks configured HTTP endpoints and TCP ports every 30 seconds.
- Measures elapsed HTTP request time or TCP connection time, rather than ICMP ping.
- Marks successful checks over 1,000 ms as slow; failures have no latency value.
- Saves real observations to a local SQLite database, retaining the latest 10,000 checks across all targets.
- Shows the last 60 checks per target and observed availability (slow counts as available).
- Refreshes the browser view every five seconds without creating extra probes.
- Lists recent failed checks, including repeated failures from the same outage.

Monitoring continues with the browser closed while the Python process runs. There is no historical data before the first run, no monitoring while the process is stopped, and no automatic startup or alerts. Gaps between runs are not counted as downtime. A TCP port opening does not verify the full application protocol. HTTP errors, DNS errors, TLS errors, and timeouts count as failures. The initial serial check cycle can take several seconds.

## Configure targets

Edit `targets.json`, then restart the server. Give every target a unique name. Use endpoints you own or are permitted to check.

```json
[
  {"name":"My Website","type":"http","url":"https://example.com"},
  {"name":"Local App","type":"tcp","host":"127.0.0.1","port":9000}
]
```

To demonstrate a failure and recovery, add the Local App target, restart NetPulse, and observe the failed connection. In a second Terminal, start:

```bash
python3 -m http.server 9000 --bind 127.0.0.1
```

Wait for the next check to see recovery. Stop that server with Control+C and observe a failure on the next cycle.

## Verify

```bash
python3 -m unittest -v
```

Tests mock external networks and verify success handling, timeout handling, persistence, and availability calculations. For a real local end-to-end check, run the failure/recovery demo above.

## Publish source on GitHub

Create an empty repository named `network-health-dashboard` at https://github.com/new. Leave README, .gitignore, and license unchecked because this folder already contains project files.

In the project directory:

```bash
git init
git add .
git commit -m "Build network health dashboard with HTTP and TCP monitoring"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/network-health-dashboard.git
git push -u origin main
```

Replace YOUR_USERNAME with your GitHub username. GitHub may prompt you to authenticate; use a credential manager, GitHub CLI login, or a personal access token rather than your account password. Local health databases are excluded by .gitignore. Check your targets for private hostnames before uploading. Publishing source does not host the Python backend, and GitHub Pages cannot run it.

## Project structure

- `server.py`: monitoring loop, SQLite storage, local API, static file server.
- `targets.json`: monitored services.
- `static/index.html`: dashboard layout.
- `static/style.css`: responsive dashboard styling.
- `static/app.js`: API requests and rendering.
- `test_monitor.py`: deterministic monitoring tests.

## Portfolio demonstration

Record a short clip showing the dashboard, stopping and restarting the local demo service, and its status changing. Explain what you built, how you calculated availability, and how you verified failure and recovery. Report measured results from your own run.

This is a learning project. It binds only to localhost and has no authentication; keep it local. Future extensions could include concurrent probes, explicit incident start/end records, notifications, and per-target thresholds.
