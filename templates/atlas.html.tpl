<title>Skill Atlas</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Open+Sans:wght@400;600&family=Source+Sans+3:wght@400;600&display=swap">
<style>
:root{
  --ground:#faf8f2; --card:#ffffff; --sunk:#f4efe4;
  --ink:#1f1712; --ink-2:#5c4d3e; --ink-3:#8a7a68;
  --brown-900:#2e1b10; --brown-700:#55371f; --brown-500:#a8763f; --brown-100:#f0e4d3; --brown-50:#faf3e9;
  --line:#c9c6b6; --line-soft:#ece8da;
  --ok:#166a3a; --ok-bg:#e3f6e9; --warn:#93590c; --warn-bg:#fdf1de;
  --bad:#951f0f; --bad-bg:#fbe6e2; --info:#1a4d85; --info-bg:#e4eef9;
  --display:'Lato',system-ui,-apple-system,'Segoe UI',sans-serif;
  --body:'Open Sans',system-ui,-apple-system,'Segoe UI',sans-serif;
  --num:'Source Sans 3',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.6;margin:0}
.wrap{max-width:1280px;margin:0 auto;padding:0 22px 90px}
h1,h2,h3,h4{font-family:var(--display);color:var(--brown-900);text-wrap:balance;margin:0}
h1{font-weight:900;font-size:clamp(30px,4.6vw,46px);letter-spacing:-.022em;line-height:1.05}
h2{font-weight:900;font-size:25px;letter-spacing:-.01em}
h3{font-weight:700;font-size:18px}
h4{font-weight:700;font-size:15px}
p{margin:0}
a{color:var(--brown-700)}
code,.mono{font-family:var(--mono);font-size:.87em;background:var(--brown-50);border:1px solid var(--line-soft);border-radius:3px;padding:1px 5px;color:var(--brown-900)}
.num{font-family:var(--num);font-variant-numeric:tabular-nums}

/* ---------- masthead ---------- */
.mast{background:var(--brown-900);color:var(--brown-100);border-bottom:3px solid var(--brown-500)}
.mast .wrap{padding-top:30px;padding-bottom:26px}
.mast h1{color:#fff}
.eyebrow{font-family:var(--display);font-weight:700;font-size:11.5px;letter-spacing:.17em;text-transform:uppercase;color:var(--brown-500)}
.sub{font-size:15.5px;color:#d9c7ae;max-width:66ch;margin-top:11px}
.meta{margin-top:16px;font-family:var(--num);font-variant-numeric:tabular-nums;font-size:12.5px;color:#b39c7e;display:flex;flex-wrap:wrap;gap:6px 20px}

/* ---------- kpi strip ---------- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin-top:26px}
.kpi{background:var(--card);padding:13px 15px 14px}
.kpi .k{font-family:var(--display);font-weight:700;font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3)}
.kpi .v{font-family:var(--num);font-variant-numeric:tabular-nums;font-weight:600;font-size:29px;line-height:1.15;color:var(--brown-700);margin-top:3px}
.kpi .n{font-size:12px;color:var(--ink-2);line-height:1.35;margin-top:2px}

/* ---------- tabs ---------- */
.tabs{position:sticky;top:0;z-index:30;background:var(--ground);border-bottom:1px solid var(--line);margin-top:0}
.tabs .wrap{padding:0 22px;display:flex;gap:2px;overflow-x:auto}
.tab{font-family:var(--display);font-weight:700;font-size:13.5px;letter-spacing:.01em;color:var(--ink-2);background:none;border:0;border-bottom:3px solid transparent;padding:13px 14px;cursor:pointer;white-space:nowrap}
.tab:hover{color:var(--brown-700)}
.tab[aria-selected="true"]{color:var(--brown-900);border-bottom-color:var(--brown-500)}
.tab:focus-visible{outline:2px solid var(--info);outline-offset:-2px}
.panel{padding-top:30px}
.panel[hidden]{display:none!important}

/* ---------- generic blocks ---------- */
.card{background:var(--card);border:1px solid var(--line);padding:20px 22px}
.stack{display:flex;flex-direction:column;gap:22px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:2px solid var(--brown-900);padding-bottom:7px;margin-bottom:16px}
.sec-head p{font-size:13px;color:var(--ink-2)}
.lede{font-size:16px;color:var(--ink-2);max-width:72ch}

/* ---------- pills ---------- */
.pill{display:inline-block;font-family:var(--display);font-weight:700;font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;padding:2px 7px;border:1px solid;border-radius:2px;white-space:nowrap}
.p-ok{color:var(--ok);border-color:var(--ok);background:var(--ok-bg)}
.p-warn{color:var(--warn);border-color:var(--warn);background:var(--warn-bg)}
.p-bad{color:var(--bad);border-color:var(--bad);background:var(--bad-bg)}
.p-info{color:var(--info);border-color:var(--info);background:var(--info-bg)}
.p-mute{color:var(--ink-2);border-color:var(--line);background:var(--sunk)}
.mut{color:var(--ink-2);font-size:.92em;line-height:1.5;display:inline-block;margin-top:.35em}
.gA{color:var(--ok);border-color:var(--ok);background:var(--ok-bg)}
.gB{color:var(--info);border-color:var(--info);background:var(--info-bg)}
.gC{color:var(--warn);border-color:var(--warn);background:var(--warn-bg)}
.gD,.gE{color:var(--bad);border-color:var(--bad);background:var(--bad-bg)}

/* ---------- tables ---------- */
.tw{overflow-x:auto;border:1px solid var(--line);background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{font-family:var(--display);font-weight:700;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-2);text-align:left;padding:9px 11px;background:var(--sunk);border-bottom:1px solid var(--line);position:sticky;top:47px;z-index:5}
td{padding:8px 11px;border-bottom:1px solid var(--line-soft);vertical-align:top}
tbody tr:hover{background:var(--brown-50)}
td.n,th.n{text-align:right;font-family:var(--num);font-variant-numeric:tabular-nums}
th.s{cursor:pointer;user-select:none}
th.s:hover{color:var(--brown-700)}
th.s::after{content:'';opacity:.45;font-size:9px}
th.s[data-dir="a"]::after{content:' ▲';opacity:1}
th.s[data-dir="d"]::after{content:' ▼';opacity:1}

/* ---------- score bar ---------- */
.sbar{display:flex;align-items:center;gap:7px;justify-content:flex-end}
.sbar i{display:block;height:6px;width:46px;background:var(--brown-100);position:relative;flex:0 0 auto}
.sbar i b{position:absolute;inset:0 auto 0 0;background:var(--brown-500)}
.sbar span{font-family:var(--num);font-variant-numeric:tabular-nums;font-weight:600;min-width:22px;text-align:right}

/* ---------- filters ---------- */
.filters{background:var(--card);border:1px solid var(--line);padding:14px 16px;display:flex;flex-direction:column;gap:11px;margin-bottom:16px}
.frow{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.frow>.lbl{font-family:var(--display);font-weight:700;font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;color:var(--ink-3);min-width:56px}
.chip{font-family:var(--display);font-weight:700;font-size:12px;padding:4px 10px;border:1px solid var(--line);background:var(--ground);color:var(--ink-2);cursor:pointer;border-radius:2px}
.chip:hover{border-color:var(--brown-500);color:var(--brown-700)}
.chip[aria-pressed="true"]{background:var(--brown-700);border-color:var(--brown-700);color:#fff}
.chip:focus-visible{outline:2px solid var(--info);outline-offset:1px}
input[type=search]{font-family:var(--body);font-size:14px;padding:7px 11px;border:1px solid var(--line);background:var(--ground);color:var(--ink);flex:1;min-width:180px;border-radius:2px}
input[type=search]:focus-visible{outline:2px solid var(--brown-500);outline-offset:-1px;border-color:var(--brown-500)}
.count{font-family:var(--num);font-variant-numeric:tabular-nums;font-size:13px;color:var(--ink-2)}

/* ---------- tree ---------- */
.tree{background:var(--card);border:1px solid var(--line)}
.tnode{display:grid;grid-template-columns:1fr 62px 70px 84px 150px;gap:10px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--line-soft);cursor:pointer;background:none;width:100%;text-align:left;font:inherit;color:inherit}
.tnode:hover{background:var(--brown-50)}
.tnode:focus-visible{outline:2px solid var(--info);outline-offset:-2px}
.tnode.d1{background:var(--sunk);border-bottom:1px solid var(--line)}
.tnode.d1 .tname{font-family:var(--display);font-weight:900;font-size:16px;color:var(--brown-900)}
.tnode.d2 .tname{font-family:var(--display);font-weight:700;font-size:14px;padding-left:20px}
.tnode.d3 .tname{font-size:13.5px;padding-left:42px;color:var(--ink-2)}
.tnode.d4 .tname{font-size:13px;padding-left:64px;color:var(--ink-3)}
.tname{display:flex;align-items:center;gap:8px;min-width:0}
.tname em{font-style:normal;font-family:var(--mono);font-size:10px;color:var(--ink-3);flex:0 0 11px}
.tbar{height:9px;background:var(--brown-100);position:relative}
.tbar b{position:absolute;inset:0 auto 0 0;background:var(--brown-500)}
.tnode .n{font-family:var(--num);font-variant-numeric:tabular-nums;font-size:13px;text-align:right}
.tleaf{padding:6px 14px 6px 86px;border-bottom:1px solid var(--line-soft);font-size:13px;display:grid;grid-template-columns:1fr 60px 70px;gap:10px;align-items:baseline}
.tleaf:hover{background:var(--brown-50)}
.tleaf .ln{font-weight:600;color:var(--brown-700)}
.tleaf .ld{color:var(--ink-3);font-size:12px}

/* ---------- findings ---------- */
.find{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);padding:15px 18px;display:flex;flex-direction:column;gap:7px}
.find.sev-hi{border-left-color:var(--bad)}
.find.sev-md{border-left-color:var(--warn)}
.find.sev-lo{border-left-color:var(--info)}
.find.sev-ok{border-left-color:var(--ok)}
/* Finding STATUS is orthogonal to severity: severity says how bad it was,
   status says whether it is still work. Rendering only severity is why a
   fixed Critical finding still read as an open red item. */
.find.st-closed{opacity:.6}
.find.st-closed:hover,.find.st-closed:focus-within{opacity:1}
.find.st-closed .fh h3{text-decoration:line-through;text-decoration-thickness:1px;text-decoration-color:var(--ink-2)}
.find.st-closed{border-left-color:var(--ok)!important}
.find.st-decl{border-left-color:var(--info)!important;border-left-style:dashed}
.p-mute{color:var(--ink-2);border-color:var(--line);background:transparent;opacity:.8}
.ledger{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:2px 0 14px;font-family:var(--display);font-size:12px}
.ledger b{font-weight:700}
.find .fh{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.find .fh h3{flex:1;min-width:200px}
.find p{font-size:14px;color:var(--ink-2);max-width:78ch}
.find .fix{font-size:13.5px;background:var(--brown-50);border:1px solid var(--line-soft);padding:9px 12px;color:var(--brown-900)}
.find .fix b{font-family:var(--display);font-weight:700}

ul.list{margin:0;padding-left:19px;font-size:14px;color:var(--ink-2);display:flex;flex-direction:column;gap:6px}
ul.list b{color:var(--ink)}
.foot{margin-top:36px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--ink-3);max-width:78ch}
@media (max-width:720px){
  .tnode{grid-template-columns:1fr 48px 56px;}
  .tnode .hidesm{display:none}
  .tleaf{padding-left:30px;grid-template-columns:1fr 56px}
  .tleaf .hidesm{display:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<header class="mast">
  <div class="wrap">
    <div class="eyebrow">Capability audit · Zanzibar FM dev machine</div>
    <h1>Skill Atlas</h1>
    <p class="sub">Every <code>SKILL.md</code> reachable from this machine, measured rather than described — scored on a published rubric, sorted by scope and category, and checked against what the upstream repositories actually ship today.</p>
    <div class="meta">
      <span>Generated <span id="gen" class="num"></span></span>
      <span>1,092 files scanned · <span class="num">951</span> distinct skills</span>
      <span>Roots: <span class="mono" style="background:none;border:0;color:#b39c7e">~/.claude/skills · skill-vault · plugins/cache</span></span>
    </div>
  </div>
</header>

<nav class="tabs" role="tablist" aria-label="Report sections">
  <div class="wrap">
    <button class="tab" role="tab" aria-selected="true" data-p="overview">Overview</button>
    <button class="tab" role="tab" aria-selected="false" data-p="categories">Category tree</button>
    <button class="tab" role="tab" aria-selected="false" data-p="skills">All skills</button>
    <button class="tab" role="tab" aria-selected="false" data-p="families">Family density</button>
    <button class="tab" role="tab" aria-selected="false" data-p="health">Health &amp; findings</button>
    <button class="tab" role="tab" aria-selected="false" data-p="cost">Token cost</button>
    <button class="tab" role="tab" aria-selected="false" data-p="config">Hooks &amp; config</button>
    <button class="tab" role="tab" aria-selected="false" data-p="upstream">Upstream</button>
    <button class="tab" role="tab" aria-selected="false" data-p="rubric">Scoring rubric</button>
  </div>
</nav>

<main class="wrap">

<!-- ======================= OVERVIEW ======================= -->
<section class="panel" id="p-overview" role="tabpanel">
<!--CONTENT:overview-->
</section>

<!-- ======================= CATEGORIES ======================= -->
<section class="panel" id="p-categories" role="tabpanel" hidden>
  <div class="sec-head"><h2>Category tree</h2><p>Every level. Click a row to expand; the deepest rows list their skills.</p></div>
  <p class="lede" style="margin-bottom:16px">Density verdicts are relative to the 27 project roots on this machine, not to some abstract ideal. A category is <span class="pill p-bad">over-served</span> when it carries many more skills than there are projects that could use them, and <span class="pill p-warn">under-served</span> when a real, recurring workload has almost nothing behind it.</p>
  <div class="filters">
    <div class="frow">
      <span class="lbl">Expand</span>
      <button class="chip" id="exp-all" aria-pressed="false">All levels</button>
      <button class="chip" id="exp-2" aria-pressed="true">Two levels</button>
      <button class="chip" id="exp-none" aria-pressed="false">Collapse</button>
      <span class="count" id="tree-count"></span>
    </div>
  </div>
  <div class="tree" id="tree"></div>

  <div style="margin-top:30px">
    <div class="sec-head"><h2>Density verdicts</h2><p>Where the library is out of proportion with the work.</p></div>
    <div class="tw"><table>
      <thead><tr><th>Category</th><th class="n">Skills</th><th>Projects it serves</th><th>Verdict</th><th>Reasoning</th></tr></thead>
      <tbody>
        <tr><td><b>Design aesthetics</b></td><td class="n">62</td><td class="num">~13 frontends</td><td><span class="pill p-warn">Over-served, cheaply</span></td><td>All 62 are hidden and tiny, so they cost nothing per session. The problem is not cost, it is that 62 named looks compete for one decision — the registry is the right entry point, the individual skills are noise.</td></tr>
        <tr><td><b>corporate + knowledge-work + financial-services + openaccountant</b></td><td class="n">377</td><td class="num">1 (bizflow)</td><td><span class="pill p-bad">Over-served</span></td><td>40% of the entire library serves the least-active workload. Keep it — it is free while vaulted — but stop growing it.</td></tr>
        <tr><td><b>ecc</b></td><td class="n">286</td><td class="num">all, indirectly</td><td><span class="pill p-info">Right-sized, unreachable</span></td><td>General engineering workflow skills that <i>should</i> apply everywhere, sitting behind a keyword guess. The reachability problem, not a density problem.</td></tr>
        <tr><td><b>Odoo</b></td><td class="n"><s style="opacity:.45">7</s> 8</td><td class="num">2</td><td><span class="pill p-warn">Improving</span></td><td>The largest and most-edited codebase on the machine. <span class="pill p-ok">2026-09-04</span> <code>odoo-deploy</code> added — the family could talk to Odoo seven ways and apply a change none. All seven existing descriptions rewritten, so the C-grade-on-description problem is gone too.</td></tr>
        <tr><td><b>Remotion / video</b></td><td class="n">14 + 4</td><td class="num">3</td><td><span class="pill p-ok">Proportionate</span></td><td>Three video projects, eighteen skills, plus two plugins. Correctly hidden.</td></tr>
        <tr><td><b>Mobile / Capacitor / Android</b></td><td class="n"><s style="opacity:.45">1</s> 2</td><td class="num">1 active</td><td><span class="pill p-warn">Improving</span></td><td>Was <code>mobile-screen</code> alone — no build, signing, release or Play Store skill despite an emulator-gated deploy rule in CLAUDE.md. <span class="pill p-ok">2026-09-04</span> <code>capacitor-mobile-build</code> covers all four, and writing it surfaced a live security defect — see below.</td></tr>
        <tr><td><b>Infrastructure — k8s, networking, routers</b></td><td class="n">1</td><td class="num">3</td><td><span class="pill p-bad">Under-served</span></td><td><code>homelab-catalog</code> is a software index, not an operations skill. Three infra projects with no skill support at all.</td></tr>
        <tr><td><b>Process &amp; meta</b></td><td class="n">12</td><td class="num">all</td><td><span class="pill p-ok">Proportionate</span></td><td>The layer that governs every other one. Well-used, and the only category where a listed cost is unambiguously earned.</td></tr>
      </tbody>
    </table></div>
  </div>
</section>

<!-- ======================= SKILLS ======================= -->
<section class="panel" id="p-skills" role="tabpanel" hidden>
  <div class="sec-head"><h2>Every skill</h2><p>Sortable and filterable. Token figures are estimates at chars ÷ 3.6.</p></div>
  <div class="filters">
    <div class="frow"><input type="search" id="q" placeholder="Search name, description or category…" aria-label="Search skills"><span class="count" id="cnt"></span></div>
    <div class="frow"><span class="lbl">Scope</span><span id="f-scope"></span></div>
    <div class="frow"><span class="lbl">Reach</span><span id="f-reach"></span></div>
    <div class="frow"><span class="lbl">Grade</span><span id="f-grade"></span></div>
    <div class="frow"><span class="lbl">Reachable</span><span id="f-sh"></span></div>
  </div>
  <div class="tw"><table id="tbl">
    <thead><tr>
      <th class="s" data-k="n">Skill</th>
      <th>Category path</th>
      <th class="s" data-k="rl">Reach</th>
      <th class="s n" data-k="sc" data-dir="d">Score</th>
      <th class="s n" data-k="lt">List tok</th>
      <th class="s n" data-k="ld">Load tok</th>
      <th class="s n" data-k="bf">Files</th>
      <th class="s n" data-k="ag">Age d</th>
      <th>Flags</th>
    </tr></thead>
    <tbody id="rows"></tbody>
  </table></div>
</section>

<!-- ======================= FAMILIES ======================= -->
<section class="panel" id="p-families" role="tabpanel" hidden>
<!--CONTENT:families-->
</section>

<!-- ======================= HEALTH ======================= -->
<section class="panel" id="p-health" role="tabpanel" hidden>
<!--CONTENT:health-->
</section>

<!-- ======================= COST ======================= -->
<section class="panel" id="p-cost" role="tabpanel" hidden>
<!--CONTENT:cost-->
</section>

<!-- ======================= CONFIG ======================= -->
<section class="panel" id="p-config" role="tabpanel" hidden>
<!--CONTENT:config-->
</section>

<!-- ======================= UPSTREAM ======================= -->
<section class="panel" id="p-upstream" role="tabpanel" hidden>
<!--CONTENT:upstream-->
</section>

<!-- ======================= RUBRIC ======================= -->
<section class="panel" id="p-rubric" role="tabpanel" hidden>
<!--CONTENT:rubric-->
</section>

<p class="foot">Computed from a filesystem scan of <code>~/.claude/skills</code>, <code>~/.claude/skill-vault</code> and <code>~/.claude/plugins/cache</code>, plus <code>settings.json</code> and the managed policy file. Counts, scores and token estimates are reproducible from that scan. Density verdicts and the findings above are judgement, grounded in the 25 project roots on this machine. Typography and palette follow the Mchuzi Suite design tokens.<br><br><b>Revision 2026-09-04 — all nine upgrade-queue rows applied.</b> Struck-through figures are the census state; the bold figure beside each is what is on disk now. Three rows turned out to be measured wrong and say so where they stand rather than being quietly rewritten: row 4 blamed 7 MB of hash directories for 767 MB that was elsewhere, row 5 counted four short descriptions where there were ten, and row 8 called <code>financial-services</code> drifted when it was already at upstream tip. One target was missed on purpose — row 3 asked for a ~6 KB <code>claude-router</code> and got ~26 KB, because the two sections that make it worth loading are 15 KB between them. The <b>per-skill list</b> below is the original census, unmodified. In the tables above, a struck-through figure is the census value and the bold figure beside it is what is on disk now.</p>
</main>

<script>
const DATA = /*__DATA__*/;
const $ = s => document.querySelector(s);
document.getElementById('gen').textContent = DATA.generated;

/* ---------- tabs ---------- */
const tabs = [...document.querySelectorAll('.tab')];
tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(x => x.setAttribute('aria-selected', String(x === t)));
  document.querySelectorAll('.panel').forEach(p => { p.hidden = p.id !== 'p' + '-' + t.dataset.p; });
  window.scrollTo({top: 0});
}));

/* ---------- category tree ---------- */
const nodes = Object.entries(DATA.nodes).map(([k, v]) => ({key: k, ...v}))
  .sort((a, b) => a.key < b.key ? -1 : 1);
const maxN = Math.max(...nodes.filter(n => n.depth === 1).map(n => n.n));
const open = new Set(nodes.filter(n => n.depth === 1).map(n => n.key));

function verdict(n) {
  if (n.depth === 1) return '';
  if (n.n >= 150) return '<span class="pill p-bad">dense</span>';
  if (n.n >= 40) return '<span class="pill p-warn">broad</span>';
  if (n.n <= 3) return '<span class="pill p-info">thin</span>';
  return '';
}
function renderTree() {
  const host = $('#tree'); host.innerHTML = '';
  let shown = 0;
  nodes.forEach(n => {
    const parent = n.path.slice(0, -1).join(' / ');
    if (n.depth > 1 && !open.has(parent)) return;
    shown++;
    const kids = nodes.some(m => m.depth === n.depth + 1 && m.key.startsWith(n.key + ' / '));
    const isOpen = open.has(n.key);
    const b = document.createElement('button');
    b.className = 'tnode d' + Math.min(n.depth, 4);
    b.setAttribute('aria-expanded', String(isOpen));
    b.innerHTML =
      '<span class="tname"><em>' + (kids || n.n <= 60 ? (isOpen ? '−' : '+') : ' ') + '</em>' +
      '<span>' + n.path[n.path.length - 1] + '</span> ' + verdict(n) + '</span>' +
      '<span class="n">' + n.n + '</span>' +
      '<span class="n">' + n.avg + '</span>' +
      '<span class="n hidesm">' + (n.lt ? n.lt.toLocaleString() : '—') + '</span>' +
      '<span class="tbar hidesm"><b style="width:' + Math.max(2, Math.round(n.n / maxN * 100)) + '%"></b></span>';
    b.addEventListener('click', () => {
      if (open.has(n.key)) open.delete(n.key); else open.add(n.key);
      renderTree();
    });
    host.appendChild(b);
    if (isOpen && !kids) {
      DATA.skills.filter(s => s.p.join(' / ') === n.key)
        .sort((a, b2) => b2.sc - a.sc).forEach(s => {
          const d = document.createElement('div');
          d.className = 'tleaf';
          d.innerHTML = '<span><span class="ln">' + s.n + '</span> <span class="ld">' +
            (s.d || '').replace(/[<>&]/g, c => ({'<': '&lt;', '>': '&gt;', '&': '&amp;'}[c])).slice(0, 130) + '</span></span>' +
            '<span class="n"><span class="pill g' + s.g + '">' + s.g + '</span></span>' +
            '<span class="n hidesm">' + s.sc + '</span>';
          host.appendChild(d);
        });
    }
  });
  $('#tree-count').textContent = shown + ' of ' + nodes.length + ' category nodes shown';
}
$('#exp-all').addEventListener('click', () => { nodes.forEach(n => open.add(n.key)); renderTree(); });
$('#exp-2').addEventListener('click', () => { open.clear(); nodes.filter(n => n.depth === 1).forEach(n => open.add(n.key)); renderTree(); });
$('#exp-none').addEventListener('click', () => { open.clear(); renderTree(); });
renderTree();

/* ---------- skills table ---------- */
const F = {scope: new Set(), reach: new Set(), grade: new Set(), sh: new Set(), q: ''};
let sortK = 'sc', sortDir = 'd';

function chips(host, key, opts) {
  const h = $(host);
  opts.forEach(([val, label]) => {
    const b = document.createElement('button');
    b.className = 'chip'; b.textContent = label; b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', () => {
      if (F[key].has(val)) F[key].delete(val); else F[key].add(val);
      b.setAttribute('aria-pressed', String(F[key].has(val)));
      renderRows();
    });
    h.appendChild(b);
  });
}
chips('#f-scope', 'scope', [['active', 'Active (149)'], ['vault', 'Vault (693)'], ['plugin', 'Plugin (109)']]);
chips('#f-reach', 'reach', [['listed', 'Listed'], ['hidden', 'Hidden'], ['vault', 'Vault'],
  ['plugin-on', 'Plugin on'], ['plugin-off', 'Plugin off'], ['plugin-unset', 'Unset']]);
chips('#f-grade', 'grade', [['A', 'A'], ['B', 'B'], ['C', 'C'], ['D', 'D']]);
chips('#f-sh', 'sh', [[1, 'Shadowed only (77)'], [0, 'Reachable only']]);
$('#q').addEventListener('input', e => { F.q = e.target.value.toLowerCase().trim(); renderRows(); });
document.querySelectorAll('th.s').forEach(th => th.addEventListener('click', () => {
  const k = th.dataset.k;
  sortDir = (sortK === k && sortDir === 'd') ? 'a' : 'd';
  sortK = k;
  document.querySelectorAll('th.s').forEach(x => x.removeAttribute('data-dir'));
  th.setAttribute('data-dir', sortDir);
  renderRows();
}));

const esc = t => String(t).replace(/[<>&]/g, c => ({'<': '&lt;', '>': '&gt;', '&': '&amp;'}[c]));
function flags(s) {
  const out = [];
  if (s.dm) out.push('<span class="pill p-mute">no auto-invoke</span>');
  if (s.sh) out.push('<span class="pill p-bad">shadowed — unreachable</span>');
  if (s.co) out.push('<span class="pill p-warn">name ×' + s.co + '</span>');
  if (s.dp > 1) out.push('<span class="pill p-bad">' + s.dp + ' copies</span>');
  if (s.ld > 9000) out.push('<span class="pill p-bad">heavy load</span>');
  if (s.dl && s.dl < 60) out.push('<span class="pill p-warn">thin desc</span>');
  if (s.sd.length) out.push('<span class="pill p-ok">' + s.sd.join(' + ') + '</span>');
  return out.join(' ');
}
function renderRows() {
  let r = DATA.skills.filter(s =>
    (!F.scope.size || F.scope.has(s.s)) &&
    (!F.reach.size || F.reach.has(s.r)) &&
    (!F.grade.size || F.grade.has(s.g)) &&
    (!F.sh.size || F.sh.has(s.sh ? 1 : 0)) &&
    (!F.q || (s.n + ' ' + s.d + ' ' + s.p.join(' ')).toLowerCase().includes(F.q)));
  const dir = sortDir === 'd' ? -1 : 1;
  r.sort((a, b) => {
    const x = a[sortK], y = b[sortK];
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * dir;
  });
  $('#cnt').textContent = r.length.toLocaleString() + ' of ' + DATA.skills.length.toLocaleString() + ' skills';
  $('#rows').innerHTML = r.map(s =>
    '<tr><td><b>' + esc(s.n) + '</b><div style="font-size:12px;color:var(--ink-3);max-width:46ch;line-height:1.4">' +
    esc(s.d).slice(0, 150) + '</div></td>' +
    '<td style="font-size:12px;color:var(--ink-2);white-space:nowrap">' + esc(s.p.join(' › ')) + '</td>' +
    '<td><span class="pill p-mute">' + s.rl + '</span></td>' +
    '<td class="n"><span class="sbar"><span class="pill g' + s.g + '">' + s.g + '</span>' +
      '<i><b style="width:' + s.sc + '%"></b></i><span>' + s.sc + '</span></span></td>' +
    '<td class="n">' + s.lt + '</td><td class="n">' + s.ld.toLocaleString() + '</td>' +
    '<td class="n">' + s.bf + '</td><td class="n">' + Math.round(s.ag) + '</td>' +
    '<td>' + flags(s) + '</td></tr>').join('');
}
renderRows();
</script>
