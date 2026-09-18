# Security Policy & Authorized Use

CyberSecuritySuite includes active scanning capabilities (TCP port scanning,
dependency auditing via Safety, static analysis via Bandit). These features
exist for **authorized security testing of systems you own or have explicit
written permission to test** — for example, your own lab environment, a
CTF target, or a client engagement with signed authorization.

Scanning networks, hosts, or code you do not own or have authorization to
test may be illegal in your jurisdiction (e.g. under the U.S. Computer Fraud
and Abuse Act or equivalent laws elsewhere), independent of whether any
vulnerability is actually exploited. You are solely responsible for
ensuring you have authorization before pointing any endpoint in this project
at a target.

## Reporting a vulnerability in this project

If you find a security issue in CyberSecuritySuite itself (as opposed to a
finding *produced by* the scanner), please open a private security advisory
on this repository (GitHub → Security → Report a vulnerability) rather than
a public issue.

## Known limitations (by design, for a portfolio/demo project)

- The bundled auth blueprint uses a single hardcoded demo account
  (`admin`) with a hashed password stored in memory. It is a demonstration
  of correct password hashing, not a production user-management system.
- The encrypted chat demo generates a fresh key per process and has no
  persistent key management, user identity, or authentication of chat
  peers. It is disabled by default (`ENABLE_CHAT_DEMO=false`).
- The port scanner is capped (`SCAN_MAX_PORT_RANGE`) and is not intended
  for large-scale or internet-wide scanning.
