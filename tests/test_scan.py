"""Scanner: runs against pretend game servers on this machine, so no game is needed."""
import argparse, os, socket, struct, sys, threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gamelan import cli, scan, source

ok = 0
def check(name, cond, extra=""):
    global ok
    assert cond, f"FAIL {name} {extra}"
    ok += 1
    print("ok ", name)

def z(text):
    return text.encode() + b"\x00"

def reply(name, kind=b"d"):
    return (b"\xff\xff\xff\xffI" + bytes([17]) + z(name) + z("de_inferno") + z("csgo") + z("Counter-Strike 2")
            + struct.pack("<H", 730) + bytes([3, 10, 0]) + kind + b"l" + bytes([0, 1]) + z("1.40"))

class FakeServer(threading.Thread):
    """Answers A2S_INFO like a game server. With a challenge, it only answers a request that carries it."""
    def __init__(self, name, kind=b"d", challenge=b"", junk=False):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.name_, self.kind, self.challenge, self.junk = name, kind, challenge, junk
        self.requests = []
        self.start()

    def run(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
            except OSError:
                return
            self.requests.append(data)
            if self.junk:
                self.sock.sendto(b"not a game server", addr)
            elif self.challenge and data != source.info_request(self.challenge):
                self.sock.sendto(b"\xff\xff\xff\xffA" + self.challenge, addr)
            elif data.startswith(source.info_request()):
                self.sock.sendto(reply(self.name_, self.kind), addr)

    def close(self):
        self.sock.close()

plain = FakeServer("Plain")
listen = FakeServer("Listen", kind=b"l")
guarded = FakeServer("Guarded", challenge=b"\xde\xad\xbe\xef")
junk = FakeServer("Junk", junk=True)
silent = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
silent.bind(("127.0.0.1", 0))
silent_port = silent.getsockname()[1]

# one server, asked directly
s = scan.query("127.0.0.1", plain.port, timeout=1.0)
check("query answers", s is not None and s.name == "Plain")
check("query fills in the address", (s.host, s.port) == ("127.0.0.1", plain.port))
check("query measures ping", 0 <= s.ping_ms < 1000, s.ping_ms)
check("query by name", scan.query("localhost", plain.port, timeout=1.0).name == "Plain")

# a server that wants its challenge back
s = scan.query("127.0.0.1", guarded.port, timeout=1.0)
check("challenge answered", s is not None and s.name == "Guarded")
check("challenge sent back once", guarded.requests == [source.info_request(), source.info_request(b"\xde\xad\xbe\xef")],
      guarded.requests)

# no answer, and answers that are not from a game
check("silent port", scan.query("127.0.0.1", silent_port, timeout=0.3) is None)
check("junk reply ignored", scan.query("127.0.0.1", junk.port, timeout=0.3) is None)

# several at once
ports = (plain.port, listen.port, guarded.port, junk.port, silent_port)
found = scan.scan(ports=ports, timeout=0.6, targets=["127.0.0.1"])
check("scan finds the three real ones", sorted(f.name for f in found) == ["Guarded", "Listen", "Plain"], found)
check("scan sorted by port", [f.port for f in found] == sorted(f.port for f in found))
check("scan tells listen from dedicated", {f.name: f.server_type for f in found}
      == {"Plain": "dedicated", "Listen": "listen", "Guarded": "dedicated"})
found = scan.scan(ports=(plain.port,), timeout=0.4, targets=["127.0.0.1", "127.0.0.1"])
check("same server asked twice is listed once", len(found) == 1)

# where broadcasts go
check("always the limited broadcast", scan.broadcast_addresses()[0] == "255.255.255.255")
check("default ports", scan.DEFAULT_PORTS[0] == 27015 and 27020 in scan.DEFAULT_PORTS)

# the command line
check("ports single", cli.parse_ports("27015") == (27015,))
check("ports range", cli.parse_ports("27015-27017") == (27015, 27016, 27017))
check("ports mixed, no repeats", cli.parse_ports("27015,27015-27016,4242") == (27015, 27016, 4242))
for bad in ("0", "70000", "27020-27015", "abc"):
    try:
        cli.parse_ports(bad)
        check(f"ports reject {bad}", False)
    except argparse.ArgumentTypeError:
        check(f"ports reject {bad}", True)

text = cli.table(found)
check("table has a header", text.splitlines()[0].split() == ["GAME", "SERVER", "MAP", "PLAYERS", "TYPE", "HOST", "PING"])
check("table has the server", "Counter-Strike 2" in text and "de_inferno" in text and "3/10" in text and f"127.0.0.1:{plain.port}" in text)
found[0].password, found[0].bots = True, 2
check("table shows password and bots", "dedicated, password" in cli.table(found) and "(2 bots)" in cli.table(found))

for srv in (plain, listen, guarded, junk):
    srv.close()
silent.close()
print(f"\n{ok} checks passed")
