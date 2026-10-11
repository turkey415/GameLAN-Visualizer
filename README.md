# GameLAN-Visualizer

See every game being played on your LAN.

GameLAN-Visualizer scans the local network for game servers, including "listen" servers a player started from inside a game, and lists them: game, server name, map, players and the host running it. It is built for LAN parties, where the question is always "what is everyone playing, and where?"

**Status: just started. Nothing here works yet.**

## How it will find games

- **Ask.** Send a broadcast query and decode the replies, the way a game's own LAN tab does.
- **Listen.** Pick up the announcements many games send out without being asked.
- **Unknown list.** Show anything broadcasting that no decoder recognizes, so new games can be identified and added.

Most games share a handful of query protocols, so each decoder covers a whole family of titles.

## Plan

1. Source / Steam query: Counter-Strike, Team Fortress 2, Left 4 Dead 2, Garry's Mod and the rest of the family
2. A games data file, so adding a title is a few lines rather than code
3. The unknown list
4. Minecraft (Java and Bedrock)
5. Quake 3 style, GameSpy and Unreal LAN beacon
6. One-offs: Warcraft III, StarCraft, Factorio, Terraria and others

It is a Python package with its own command line. [PorkChopCheck](https://github.com/turkey415/PorkChopCheck) will use it for its LAN game browser page and add the seat each game is being played at.

## Limits

Games with no LAN discovery cannot be seen this way. A title that only plays through the internet never announces itself on the local network.

## License

MIT
