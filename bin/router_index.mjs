// Reachability ground truth, taken from the skill-router's own index rather than
// simulated. scan.py cannot guess the winner: same-source ties break on directory
// order, and node's readdir order is not python's os.walk order.
//
// This stage exists because nothing previously wrote router-index.json -- the old
// verify.mjs only printed diagnostics, so the file silently went stale and
// build.py kept computing reachability from it anyway.
import { buildIndex, getIndex, getAliases } from "/home/ghost/.claude/mcp-servers/skill-router/lib.mjs";
import { writeFileSync } from "node:fs";

const outPath = process.argv[2];
if (!outPath) {
  console.error("usage: node bin/router_index.mjs <out.json>");
  process.exit(2);
}

const counts = await buildIndex();
const index = getIndex();
const aliases = getAliases();

const winnerPaths = new Set([...aliases.values()].map((i) => i.path));
// Keyed by BARE slug, matching the `id` emitted for shadowed entries -- the
// qualified id would never match and phantom detection would silently fail.
const winners = [...aliases.entries()].map(([slug, i]) => ({
  id: slug, qualified_id: i.id, name: i.name, source: i.source, path: i.path,
}));

// A skill that does not win its bare name needs a qualified id to reach.
// Before the 2026-09-04 namespacing fix these were unreachable outright;
// they are now indexed, and dataset.py reports them as "needs qualified id".
const shadowed = [...index.values()]
  .filter((i) => !winnerPaths.has(i.path))
  .map((i) => ({ id: i.slug, qualified_id: i.id, source: i.source, path: i.path }));

writeFileSync(outPath, JSON.stringify({
  generated: new Date().toISOString(),
  counts, size: index.size, aliases: aliases.size,
  winners, shadowed,
}, null, 0));

console.log(`router: ${index.size} ids indexed, ${aliases.size} bare names, ` +
            `${shadowed.length} needing a qualified id`);
