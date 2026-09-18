# CyberSecuritySuite

[![CI](https://github.com/Ajafarnezhad/cybersecurity-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Ajafarnezhad/cybersecurity-suite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

A small, self-hosted Flask application bundling three OWASP-aligned
security-tooling demos behind JWT authentication: a network **port
scanner**, wrappers around **Bandit**/**Safety** for static and dependency
analysis, and an **encrypted chat** demo built on `cryptography`'s Fernet.

> ⚠️ **Authorized use only.** The scanning endpoints must only be pointed at
> hosts, networks, or code you own or have explicit permission to test. See
> [SECURITY.md](SECURITY.md).

## Why this project

Security tooling is a setting where sloppy engineering is especially costly:
a "scanner" that itself ships a path-traversal bug, or an "auth" module that
stores plaintext passwords, undermines the whole point. This repository is
built around closing exactly those gaps and making the reasoning behind each
fix explicit in code comments.

## What changed from the original prototype

- **Password storage**: plaintext credential comparison → PBKDF2 hashing via
  `werkzeug.security` (`generate_password_hash`/`check_password_hash`).
- **Static-analysis endpoint**: accepted an arbitrary user-supplied file
  path with no bounds check (path traversal) → resolved and validated
  against a configured `SCAN_ALLOWED_ROOT`.
- **Config secrets**: hardcoded fallback `SECRET_KEY`/`JWT_SECRET_KEY` →
  required from the environment in production, with a clear startup error
  if missing (a fresh disposable key is generated only in debug mode).
- **Logging**: `setup_logger` attached duplicate handlers on every call
  (multiplying every log line) and wrote to a `logs/` directory that was
  never created → handlers are attached once, directory is created
  automatically.
- **Chat demo**: opened a background TCP listener as a side effect of
  *importing* the module (so even running the test suite spun up a network
  server) → moved behind an explicit `start_chat_server()` call, gated by
  `ENABLE_CHAT_DEMO` (off by default).
- **Dependency scan endpoint**: referenced `json` without importing it
  (guaranteed `NameError` on first use) → fixed, plus graceful handling for
  a missing `safety`/`bandit` binary and scan timeouts.
- **IP validation**: a regex that accepted invalid addresses like
  `999.999.999.999` → replaced with the standard library's `ipaddress`
  module.
- **Port scanning**: sequential, unbounded loop over the requested range →
  bounded (`SCAN_MAX_PORT_RANGE`) and parallelized with a thread pool.
- **Docker Compose**: hardcoded `SECRET_KEY: your_secret_key` committed to
  the repo → required via `.env`, with the build failing fast if unset.
- **Testability**: module-level `Flask(__name__)` → an application-factory
  pattern (`create_app`), so tests exercise a fully isolated instance.

Removed entirely: a `src/rce/` folder in the original prototype contained
someone else's public router exploit PoC and an unrelated class assignment,
neither of which are appropriate (or licensed) to publish here — see the
project history if you're curious what was cut.

## Installation

```bash
git clone https://github.com/Ajafarnezhad/cybersecurity-suite.git
cd cybersecurity-suite
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in SECRET_KEY / JWT_SECRET_KEY
```

Generate strong secrets with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Running

Local development (auto-reload, throwaway secrets):

```bash
export FLASK_DEBUG=true      # Windows PowerShell: $env:FLASK_DEBUG="true"
export FLASK_APP=cybersecurity_suite.wsgi
flask run
```

Production-style (env-supplied secrets required, no debug):

```bash
export SECRET_KEY=...
export JWT_SECRET_KEY=...
python -m cybersecurity_suite.wsgi
```

With Docker:

```bash
cd docker
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
docker compose up --build
```

## API overview

| Endpoint | Method | Auth | Description |
| --- | --- | --- | --- |
| `/` | GET | none | Health/welcome message |
| `/auth/login` | POST | none | Exchange `{username, password}` for a JWT |
| `/scan/port` | POST | JWT | Scan `{target, ports: "start-end"}`; `target` must be a literal IP |
| `/scan/dependencies` | POST | JWT | Run `safety check` over installed dependencies |
| `/scan/static` | POST | JWT | Run `bandit` over `{path}`, sandboxed to `SCAN_ALLOWED_ROOT` |
| `/chat/status` | GET | none | Whether the encrypted chat demo is enabled |

Example:

```bash
TOKEN=$(curl -s -X POST localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me-please"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST localhost:5000/scan/port \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"target":"127.0.0.1","ports":"1-1024"}'
```

Change the demo password (`change-me-please`) before deploying this
anywhere beyond your own machine — see [SECURITY.md](SECURITY.md) for the
full list of by-design demo limitations.

## Project layout

```
cybersecurity-suite/
├── src/cybersecurity_suite/
│   ├── __init__.py          # application factory
│   ├── config.py            # env-driven config + production validation
│   ├── extensions.py        # shared JWT / rate-limiter instances
│   ├── wsgi.py              # entry point
│   ├── blueprints/
│   │   ├── auth.py          # JWT login (hashed demo credential)
│   │   ├── scanner.py       # port scan, dependency scan, static analysis
│   │   └── chat.py          # encrypted chat demo (opt-in)
│   └── utils/
│       ├── logger.py
│       ├── validators.py
│       └── report_generator.py
├── tests/                   # pytest suite (validators, logger, full API)
├── docker/                  # Dockerfile + docker-compose.yaml
├── .github/workflows/ci.yml
├── SECURITY.md              # authorized-use policy + known limitations
└── pyproject.toml
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
bandit -r src/ -ll
pytest --cov=cybersecurity_suite --cov-report=term-missing
```

CI runs the same lint, Bandit, and test suite on every push and pull
request across Python 3.10–3.12.

## Disclaimer

This project is for research, learning, and authorized security-testing use
only. It is provided "as is" with no warranty; see [LICENSE](LICENSE).

## License

MIT — see [LICENSE](LICENSE).

## Author

**Amirhossein Jafarnezhad** — [github.com/Ajafarnezhad](https://github.com/Ajafarnezhad)
