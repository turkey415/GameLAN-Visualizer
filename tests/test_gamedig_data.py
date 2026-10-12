"""gamedig data: the files ship with the package, load, and agree with each other."""
import json, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gamelan", "gamedig")

ok = 0
def check(name, cond, extra=""):
    global ok
    assert cond, f"FAIL {name} {extra}"
    ok += 1
    print("ok ", name)

def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)

games = load("games.json")["games"]
protocols = load("protocols.json")["protocols"]
ports = load("query-ports.json")["ports"]

check("license ships with the data", os.path.exists(os.path.join(HERE, "LICENSE")))
check("hundreds of games", len(games) > 300, len(games))
check("counter-strike 2 is a valve game on 27015",
      games["counterstrike2"]["protocol"] == "valve" and 27015 in games["counterstrike2"]["query_ports"])
check("every game's protocol is known", all(g["protocol"] in protocols for g in games.values()))
check("every port entry names real games", all(i in games for p in ports for i in p["games"]))
check("internet-only games are not in the scan list",
      not any(not games[i]["lan_queryable"] for p in ports for i in p["games"]))
check("scan list is most-shared first",
      all(len(a["games"]) >= len(b["games"]) for a, b in zip(ports, ports[1:])))
check("27015 is the most-shared port", ports[0]["port"] == 27015)

print(f"\n{ok} checks passed")
