# GameLAN-Visualizer: notes for Claude

## What this is
A Python package and CLI that finds game servers on a LAN, including listen servers a player started inside a game, and lists game, server name, map, players and host. Built for LAN parties. Owner is a networking person; explain network behavior precisely.

## Who uses it
- **PorkChopCheck** (github.com/turkey415/PorkChopCheck): its LAN game browser page, adding the seat each game is played at.
- **GXL-LANapp** (github.com/turkey415/GXL-LANapp): the LAN party suite. Runs this on its on-site Event Server to power feature 8 (game server list) and feature 9 (discovery). Specs: `docs/features/08-game-servers.md`, `09-discovery.md`, `docs/research/gamedig.md` in that repo. Results get linked to seats through IP → switch port → seat, so keep `host` and `port` accurate on every result.

Keep it a plain library with no knowledge of those apps.

## Layout
- `gamelan/source.py`: Valve A2S_INFO and A2S_PLAYER request building and reply decoding only (no sockets)
- `gamelan/scan.py`: sockets: broadcast or targeted queries, challenge handling, ping, `players()`
- `gamelan/cli.py`: `python -m gamelan` / `gamelan` command
- `gamelan/gamedig/`: game, protocol and port data generated from node-gamedig. **Read `docs/gamedig.md` before adding any protocol, game, or port list.**
- `tools/sync_gamedig.mjs`: regenerates `gamelan/gamedig/` (needs Node and a gamedig clone)
- `tests/`: plain scripts with `check()` asserts and fake UDP servers on 127.0.0.1; no pytest

## Conventions (follow what's here)
- Python 3.9+, **standard library only**. No runtime dependencies.
- Decoders build requests and decode bytes; they never touch sockets. Sockets live in `scan.py`.
- Tests run as `python tests/test_<name>.py` and are listed in `.github/workflows/tests.yml`; add a line there for any new test file. Test against fake servers, never the internet.
- Plain, short docstrings and comments that explain *why*.
- Don't edit `gamelan/gamedig/*.json` by hand; change `tools/sync_gamedig.mjs` and regenerate.
- `.gitignore` ignores any folder named `data/`; that's why the data lives in `gamelan/gamedig/`.

## Roadmap (from README) with where to look
1. Source / Steam: started. Split packets (`\xfe\xff\xff\xff`) not handled yet; see gamedig `protocols/valve.js`.
2. Games data file: done as `gamelan/gamedig/`. Wire it into the scanner and CLI (friendly names, `--sweep` using `query-ports.json`).
3. Unknown list: replies on known query ports that no decoder understands.
4. Minecraft Java (TCP) and Bedrock (UDP); Java LAN worlds also announce on multicast 224.0.2.60:4445.
5. Quake 3, GameSpy 1/2/3, Unreal 2.
6. One-offs.

Port protocols in order of game count in `protocols.json`. Skip `lan_queryable: false` protocols.

## Gotchas
- A port doesn't identify a game (7777 = 18 games). Identify from the reply; Valve's `app_id` is exact.
- Broadcast to 255.255.255.255 only leaves by the default route on Linux; `scan.broadcast_addresses()` adds each interface's own broadcast address.
- Sweeps must be paced: this runs on networks where people are mid-match.
