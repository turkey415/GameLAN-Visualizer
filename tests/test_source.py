"""Source query decoder: replies built byte by byte to the published A2S_INFO layout."""
import os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gamelan import source

ok = 0
def check(name, cond, extra=""):
    global ok
    assert cond, f"FAIL {name} {extra}"
    ok += 1
    print("ok ", name)

def z(text):
    return text.encode() + b"\x00"

def info_reply(name="LAN Finals", map_="de_mirage", folder="csgo", game="Counter-Strike 2", app_id=730,
               players=9, max_players=10, bots=1, kind=b"l", env=b"w", password=1, vac=1,
               version="1.40.2.1", extra=b""):
    return (b"\xff\xff\xff\xffI" + bytes([17]) + z(name) + z(map_) + z(folder) + z(game)
            + struct.pack("<H", app_id) + bytes([players, max_players, bots]) + kind + env
            + bytes([password, vac]) + z(version) + extra)

# the request
check("request", source.info_request() == b"\xff\xff\xff\xffTSource Engine Query\x00")
check("request with challenge", source.info_request(b"\x01\x02\x03\x04").endswith(b"Query\x00\x01\x02\x03\x04"))

# challenge replies
check("challenge found", source.challenge_from(b"\xff\xff\xff\xffA\x0a\x0b\x0c\x0d") == b"\x0a\x0b\x0c\x0d")
check("info is not a challenge", source.challenge_from(info_reply()) is None)
check("short challenge ignored", source.challenge_from(b"\xff\xff\xff\xffA\x01") is None)

# a plain reply
s = source.decode_info(info_reply())
check("name", s.name == "LAN Finals")
check("map", s.map == "de_mirage")
check("folder and game", (s.folder, s.game) == ("csgo", "Counter-Strike 2"))
check("app id", s.app_id == 730)
check("players", (s.players, s.max_players, s.bots) == (9, 10, 1))
check("listen server", s.server_type == "listen")
check("windows", s.environment == "windows")
check("password and vac", s.password and s.vac)
check("version", s.version == "1.40.2.1")
check("engine", s.engine == "source")
check("no optional fields", (s.game_port, s.steam_id, s.keywords) == (0, 0, ""))

check("dedicated on linux", (lambda d: (d.server_type, d.environment))(
    source.decode_info(info_reply(kind=b"d", env=b"l", password=0, vac=0))) == ("dedicated", "linux"))
check("relay", source.decode_info(info_reply(kind=b"p")).server_type == "relay")
check("open server", not source.decode_info(info_reply(password=0)).password)

# the optional fields on the end
extra = (bytes([0x80 | 0x10 | 0x40 | 0x20 | 0x01]) + struct.pack("<H", 27016) + struct.pack("<Q", 90071992547409920)
         + struct.pack("<H", 27020) + z("GOTV") + z("competitive,secure") + struct.pack("<Q", 730))
s = source.decode_info(info_reply(extra=extra))
check("game port", s.game_port == 27016)
check("steam id", s.steam_id == 90071992547409920)
check("keywords", s.keywords == "competitive,secure")

s = source.decode_info(info_reply(app_id=0, extra=bytes([0x01]) + struct.pack("<Q", 1203220)))
check("big app id from game id", s.app_id == 1203220)
s = source.decode_info(info_reply(extra=bytes([0x80]) + b"\x88"))
check("cut-off optional fields keep the rest", s.name == "LAN Finals" and s.game_port == 0)

# The Ship has three extra bytes before the version
ship = (b"\xff\xff\xff\xffI" + bytes([7]) + z("Ship") + z("batavier") + z("ship") + z("The Ship")
        + struct.pack("<H", 2400) + bytes([2, 8, 0]) + b"lw" + bytes([0, 0]) + bytes([1, 2, 3]) + z("1.0.0.4"))
check("the ship", source.decode_info(ship).version == "1.0.0.4")

# names are not always clean text
check("bad bytes in a name", source.decode_info(info_reply().replace(b"LAN Finals", b"LAN \xff\xfeals")).map == "de_mirage")

# the older GoldSrc reply
gold = (b"\xff\xff\xff\xffm" + z("10.2.1.50:27015") + z("Old School") + z("de_dust2") + z("cstrike")
        + z("Counter-Strike") + bytes([4, 16, 47]) + b"LW" + bytes([0, 0, 1, 2]))
s = source.decode_info(gold)
check("goldsrc name and map", (s.name, s.map) == ("Old School", "de_dust2"))
check("goldsrc players", (s.players, s.max_players, s.bots) == (4, 16, 2))
check("goldsrc listen on windows", (s.server_type, s.environment) == ("listen", "windows"))
check("goldsrc port and vac", s.game_port == 27015 and s.vac)
check("goldsrc engine", s.engine == "goldsrc")
gold_mod = (b"\xff\xff\xff\xffm" + z("10.2.1.50:27016") + z("Mod") + z("map") + z("mod") + z("A Mod")
            + bytes([1, 8, 47]) + b"dl" + bytes([1, 1]) + z("http://a") + z("http://b") + b"\x00"
            + struct.pack("<II", 1, 2) + bytes([0, 0]) + bytes([0, 3]))
s = source.decode_info(gold_mod)
check("goldsrc mod skipped", (s.bots, s.password, s.server_type) == (3, True, "dedicated"))

# things that are not info replies
def rejects(data):
    try:
        source.decode_info(data)
    except source.DecodeError:
        return True
    return False

check("empty", rejects(b""))
check("wrong header", rejects(b"hello world"))
check("split reply", rejects(b"\xfe\xff\xff\xff" + b"\x00" * 20))
check("challenge is not info", rejects(b"\xff\xff\xff\xffA\x01\x02\x03\x04"))
check("players reply is not info", rejects(b"\xff\xff\xff\xffD\x00"))
check("cut off in a name", rejects(info_reply()[:12]))
check("cut off before the type", rejects(info_reply()[:-14]))

# A2S_PLAYER
def player(name, score, seconds):
    return b"\x00" + z(name) + struct.pack("<if", score, seconds)

check("player request", source.player_request() == b"\xff\xff\xff\xffU\xff\xff\xff\xff")
check("player request with challenge", source.player_request(b"\x01\x02\x03\x04") == b"\xff\xff\xff\xffU\x01\x02\x03\x04")
ps = source.decode_players(b"\xff\xff\xff\xffD\x03" + player("s1mple", 21, 1830.5) + player("", 0, 4.0) + player("BOT Ivan", -2, 90.0))
check("players count", len(ps) == 3)
check("player fields", (ps[0].name, ps[0].score, ps[0].seconds) == ("s1mple", 21, 1830.5))
check("connecting player has no name", ps[1].name == "")
check("negative score (team kills)", ps[2].score == -2)
check("empty server", source.decode_players(b"\xff\xff\xff\xffD\x00") == [])
cut = source.decode_players(b"\xff\xff\xff\xffD\x02" + player("whole", 5, 10.0) + player("cut", 1, 1.0)[:-3])
check("cut-off list keeps the whole players", [p.name for p in cut] == ["whole"])
def rejects_players(data):
    try:
        source.decode_players(data)
    except source.DecodeError:
        return True
    return False
check("info reply is not players", rejects_players(info_reply()))
check("split players reply", rejects_players(b"\xfe\xff\xff\xff\x01"))

print(f"\n{ok} checks passed")
