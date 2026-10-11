"""Command line: list the game servers on the LAN."""
import argparse
import json
import sys

from . import __version__, scan


def parse_ports(text):
    """'27015', '27015-27030' or '27015,27020-27025' as a tuple of port numbers."""
    ports = []
    for part in text.split(","):
        lo, _, hi = part.strip().partition("-")
        try:
            lo, hi = int(lo), int(hi or lo)
        except ValueError:
            lo = hi = 0
        if not (0 < lo <= hi < 65536):
            raise argparse.ArgumentTypeError(f"bad port range: {part}")
        ports.extend(range(lo, hi + 1))
    return tuple(dict.fromkeys(ports))


def _row(s):
    players = f"{s.players}/{s.max_players}" + (f" ({s.bots} bots)" if s.bots else "")
    kind = s.server_type or "?"
    if s.password:
        kind += ", password"
    ping = f"{s.ping_ms:.0f} ms" if s.ping_ms >= 0 else ""
    return (s.game or s.folder, s.name, s.map, players, kind, f"{s.host}:{s.game_port or s.port}", ping)


def table(servers):
    head = ("GAME", "SERVER", "MAP", "PLAYERS", "TYPE", "HOST", "PING")
    rows = [head] + [_row(s) for s in servers]
    widths = [max(len(r[i]) for r in rows) for i in range(len(head))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows)


def main(argv=None):
    p = argparse.ArgumentParser(prog="gamelan", description="List the game servers on your LAN.")
    p.add_argument("--host", metavar="HOST[:PORT]", action="append",
                   help="ask this server instead of broadcasting (can be given more than once)")
    p.add_argument("--ports", type=parse_ports, default=scan.DEFAULT_PORTS, metavar="RANGE",
                   help="ports to ask on when broadcasting (default: 27015-27030)")
    p.add_argument("--timeout", type=float, default=2.0, metavar="SECONDS",
                   help="how long to wait for answers (default: 2)")
    p.add_argument("--json", action="store_true", help="print the full details as JSON")
    p.add_argument("--version", action="version", version=f"gamelan {__version__}")
    args = p.parse_args(argv)

    if args.host:
        servers = []
        for item in args.host:
            host, _, port = item.partition(":")
            try:
                info = scan.query(host, int(port or 27015), args.timeout)
            except (OSError, ValueError) as e:
                print(f"{item}: {e}", file=sys.stderr)
                continue
            if info:
                servers.append(info)
            else:
                print(f"{item}: no answer", file=sys.stderr)
    else:
        servers = scan.scan(args.ports, args.timeout)

    if args.json:
        print(json.dumps([s.as_dict() for s in servers], indent=2))
    elif servers:
        print(table(servers))
    else:
        print("No game servers found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
