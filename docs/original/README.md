# Original generator (archived)

The scripts that produced the first published Skill Atlas artifact. They lived only in a
scratch directory and were rescued before it was lost. They are **not shipped here**:
each one hardcoded a single machine's paths and a single machine's skill inventory, which
is exactly the coupling the rewrite exists to remove. Shipping them would put that
inventory in the repository and invite someone to run code that reads from paths that
only ever existed on one host.

The defect list is kept because it is the audit trail for the rewrite, and because each
item is a design constraint visible in the current package.

## Defects, all fixed in the rewrite

- **Configuration duplicated in code.** Three copies of it: a hardcoded base path in the
  builder, a hardcoded home directory in the scanners, a private plugin-path dict in the
  measure script. Now one `config/roots.json` and one loader.
- **A classifier that misfiled by default.** `family()` fell through to a single
  catch-all family, so every skill added after it was written was silently sorted into
  that bucket. Now an explicit `Unclassified` bucket that `atlas doctor` reports on, so
  the failure surfaces instead of quietly corrupting the tree.
- **A verification step that only printed.** Nothing wrote the router index, so it went
  stale while the builder kept reading it and reported its numbers as fact. Now the
  router is invoked as a library and its index written by the same run that reads it.
- **The router's logic reimplemented in another language.** Shadowing was *simulated* in
  Python, replicating `buildIndex` — and the simulation broke ties on `os.walk` order,
  which is not the order the real implementation sees. Any divergence between simulation
  and reality is a wrong answer, not a rounding error. Now the router's own index is read.
- **Dead special-case code.** A `followlinks` branch existed to serve four skills that
  were later deleted. Nobody removed the branch, because nothing measured it.

## Two lessons worth carrying

1. **A stale input that is read but never written is worse than a missing one.** A missing
   file fails loudly. A file that is read on every run and written on none looks healthy
   forever while reporting stale numbers as fact.
2. **Never reimplement a component you also depend on.** The simulation was plausible,
   testable, and wrong in precisely the place that mattered &mdash; and nothing in the
   original setup could have told you.

## On the rendered artifact

The intermediate JSON and rendered HTML are deliberately not tracked. On the machine this
came from they embed skill descriptions from collections under redistribution
restrictions, and the report is a single file containing all of it. Generating your own is
one command, and yours will describe your library rather than someone else's.
