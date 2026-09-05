import { buildIndex, getIndex, getAliases, variantsOf, resolveId, search } from "/home/ghost/.claude/mcp-servers/skill-router/lib.mjs";
const c = await buildIndex();
console.log("counts:", c);
const idx = getIndex();
console.log("indexed ids:", idx.size, " bare aliases:", getAliases().size);
const dupNames = [...new Set([...idx.values()].map(i => i.slug))].filter(s => variantsOf(s).length > 1);
console.log("names with >1 copy:", dupNames.length,
            " extra copies now reachable:", dupNames.reduce((a,s)=>a+variantsOf(s).length-1,0));
console.log("\nno bare ids lost (every old bare slug still resolves):",
  [...getAliases().keys()].every(s => resolveId(s)));
console.log("all qualified ids resolve:", [...idx.keys()].every(k => resolveId(k) === idx.get(k)));
const fs = [...idx.values()].filter(i => i.path.includes("/skill-vault/financial-services/"));
console.log("\nfinancial-services indexed:", fs.length);
console.log("sample qualified ids:", fs.slice(0,3).map(i=>i.id).join("  |  "));
const worst = dupNames.map(s=>[s,variantsOf(s).length]).sort((a,b)=>b[1]-a[1]).slice(0,5);
console.log("\nmost-duplicated names:", worst.map(([s,n])=>`${s}(${n})`).join(", "));
console.log("\nsearch 'discounted cash flow valuation model' ->");
for (const r of search("discounted cash flow valuation model", 5))
  console.log("  ", r.id, r.variants ? `+${r.variants.length} variants` : "");
