# GameLAN-Visualizer

See every game being played on your LAN.

GameLAN-Visualizer scans the local network for game servers, including "listen" servers a player started from inside a game, and lists them: game, server name, map, players and the host running it. It is built for LAN parties, where the question is always "what is everyone playing, and where?"

**Status: early.** It finds Source engine servers (Counter-Strike and its family). It has been tested against pretend servers only, not yet against real games.

## Try it

Needs Python 3.9 or newer and nothing else.

```
python -m gamelan                        # broadcast on the LAN and list what answers
python -m gamelan --host 10.2.1.50       # ask one server (port 27015 unless you add :PORT)
python -m gamelan --json                 # full details
```

```
GAME              SERVER        MAP       PLAYERS        TYPE              HOST             PING
Counter-Strike 2  kturk's game  de_dust2  4/10 (5 bots)  listen, password  10.2.1.50:27015  0 ms
```

`TYPE` says whether it is a dedicated server or a listen server a player started from inside the game. Broadcasting asks ports 27015 to 27030; change that with `--ports`.

## How it will find games

- **Ask.** Send a broadcast query and decode the replies, the way a game's own LAN tab does.
- **Listen.** Pick up the announcements many games send out without being asked.
- **Unknown list.** Show anything broadcasting that no decoder recognizes, so new games can be identified and added.

Most games share a handful of query protocols, so each decoder covers a whole family of titles.

## Plan

1. Source / Steam query: Counter-Strike, Team Fortress 2, Left 4 Dead 2, Garry's Mod and the rest of the family (started)
2. A games data file, so adding a title is a few lines rather than code (data in place: `gamelan/gamedig/`, 362 games from [gamedig](https://github.com/gamedig/node-gamedig); see [docs/gamedig.md](docs/gamedig.md))
3. The unknown list
4. Minecraft (Java and Bedrock)
5. Quake 3 style, GameSpy and Unreal LAN beacon
6. One-offs: Warcraft III, StarCraft, Factorio, Terraria and others

It is a Python package with its own command line. [PorkChopCheck](https://github.com/turkey415/PorkChopCheck) will use it for its LAN game browser page and add the seat each game is being played at.

## Limits

Games with no LAN discovery cannot be seen this way. A title that only plays through the internet never announces itself on the local network.

## License

MIT
