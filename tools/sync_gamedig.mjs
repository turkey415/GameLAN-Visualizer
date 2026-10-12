// Regenerates gamelan/gamedig/*.json from a local clone of https://github.com/gamedig/node-gamedig
//
// Usage:
//   git clone --depth 1 https://github.com/gamedig/node-gamedig /tmp/node-gamedig
//   node tools/sync_gamedig.mjs /tmp/node-gamedig            (writes gamelan/gamedig/)
//
// gamedig is MIT licensed; its LICENSE is copied into gamelan/gamedig/ alongside the data.

import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'

const src = process.argv[2]
if (!src) { console.error('usage: node tools/sync_gamedig.mjs <path to node-gamedig clone>'); process.exit(1) }

const out = path.resolve(process.argv[3] || path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'gamelan', 'gamedig'))
fs.mkdirSync(out, { recursive: true })

const { games } = await import(pathToFileURL(path.join(src, 'lib', 'games.js')).href)
const pkg = JSON.parse(fs.readFileSync(path.join(src, 'package.json'), 'utf8'))
let commit = 'unknown'
try { commit = execSync('git rev-parse HEAD', { cwd: src }).toString().trim() } catch {}

// ---- Protocols -------------------------------------------------------------
// Which protocols can be asked directly over the LAN, and which only talk to an
// internet service (master server list, cloud API). Internet-only ones are no use
// with the venue uplink down, and never see a LAN-only listen server.
const INTERNET_ONLY = new Set([
  'altvmp', 'beammpmaster', 'brokeprotocol', 'brokeprotocolmaster', 'discord',
  'epic', 'asa', 'renown', 'squad', 'theisleevrima', 'factorio', 'geneshift',
  'hawakening', 'hawakeningmaster', 'minetest', 'ragemp', 'renegadex',
  'renegadexmaster', 'scpsl', 'tribes1master', 'vintagestorymaster'
])

const protoDir = path.join(src, 'protocols')
const protocols = {}
for (const file of fs.readdirSync(protoDir).sort()) {
  if (!file.endsWith('.js') || ['index.js', 'core.js'].includes(file)) continue
  const id = file.slice(0, -3)
  const code = fs.readFileSync(path.join(protoDir, file), 'utf8')
  const transports = []
  if (/udpSend|withUdp|\.udp/.test(code)) transports.push('udp')
  if (/withTcp|tcpSend/.test(code)) transports.push('tcp')
  if (/this\.request\(/.test(code)) transports.push('http')
  const parent = (code.match(/extends\s+([A-Za-z0-9]+)/) || [])[1]
  protocols[id] = {
    extends: parent && parent.toLowerCase() !== 'core' ? parent.toLowerCase() : null,
    transports,
    lan_queryable: !INTERNET_ONLY.has(id),
    source_file: `protocols/${file}`,
    games: []
  }
}

// ---- Games -----------------------------------------------------------------
const gamesOut = {}
const queryPorts = {}
const addPort = (port, id) => { (queryPorts[port] ||= []).includes(id) || queryPorts[port].push(id) }

for (const [id, g] of Object.entries(games)) {
  const o = g.options || {}
  const offsets = o.port_query_offset === undefined ? [0]
    : Array.isArray(o.port_query_offset) ? o.port_query_offset : [o.port_query_offset]
  // gamedig tries: game port + each offset, then the fixed query port if one is set
  const candidates = []
  if (o.port) offsets.forEach(off => candidates.push(o.port + off))
  if (o.port_query) candidates.push(o.port_query)
  const query_ports = [...new Set(candidates)]
  const proto = protocols[o.protocol]

  gamesOut[id] = {
    name: g.name,
    release_year: g.release_year ?? null,
    protocol: o.protocol,
    game_port: o.port ?? null,
    query_port: o.port_query ?? null,
    query_port_offset: o.port_query_offset ?? null,
    query_ports,
    lan_queryable: proto ? proto.lan_queryable : null,
    old_ids: g.extra?.old_id ? [].concat(g.extra.old_id) : [],
    has_notes: !!g.extra?.doc_notes
  }
  if (proto) proto.games.push(id)
  if (!proto || proto.lan_queryable) query_ports.forEach(p => addPort(p, id))
}

// An array, not an object: JS always orders integer-like keys numerically, which would undo the sort.
const sortedPorts = Object.entries(queryPorts)
  .sort((a, b) => b[1].length - a[1].length || a[0] - b[0])
  .map(([port, ids]) => ({ port: Number(port), protocols: [...new Set(ids.map(id => gamesOut[id].protocol))], games: ids }))

const meta = { source: 'https://github.com/gamedig/node-gamedig', version: pkg.version, commit, generated: new Date().toISOString().slice(0, 10), license: 'MIT' }
const write = (name, data) => fs.writeFileSync(path.join(out, name), JSON.stringify({ _meta: meta, ...data }, null, 2) + '\n')

write('games.json', { games: gamesOut })
write('protocols.json', { protocols })
write('query-ports.json', { _note: 'Query port -> games that answer on it by default. LAN-queryable protocols only. Ordered by how many games share the port.', ports: sortedPorts })
fs.copyFileSync(path.join(src, 'LICENSE'), path.join(out, 'LICENSE'))

const lan = Object.values(gamesOut).filter(g => g.lan_queryable).length
console.log(`gamedig ${pkg.version} @ ${commit.slice(0, 7)}: ${Object.keys(gamesOut).length} games (${lan} LAN-queryable), ${Object.keys(protocols).length} protocols, ${sortedPorts.length} query ports`)
