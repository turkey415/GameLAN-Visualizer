# gamedig game data

Generated from [node-gamedig](https://github.com/gamedig/node-gamedig) (MIT, see `LICENSE` here) by `tools/sync_gamedig.mjs`. Don't edit by hand; re-run the script. Each file's `_meta` block records the gamedig version and commit.

- `games.json`: 362 games: name, protocol, game port, query port(s), whether it can be queried over the LAN
- `protocols.json`: 79 protocols: UDP/TCP/HTTP, parent protocol, LAN or internet-only, source file in gamedig, games using it
- `query-ports.json`: the scan list, a list of `{port, protocols, games}` ordered by how many games share the port (LAN-queryable only)

What it means and how to use it: [docs/gamedig.md](../../docs/gamedig.md).
