# Contributing

Thanks for looking. This is a small project with a high documentation bar, so most
contributions are about clarity as much as code.

## Before you start

- For anything larger than a bug fix, open an issue first. It is cheaper to agree an
  approach than to rewrite a finished pull request.
- Read `docs/ARCHITECTURE.md` first. If your change crosses a layer boundary, that
  document needs to change with it — the decisions and their rejected alternatives
  are the part a future reader actually needs.

## Making a change

1. Branch from `main`.
2. Keep the change focused. One concern per pull request.
3. Add or update tests for behaviour changes:

   ```bash
   python3 -m unittest discover -s tests -v
   ```

4. Update the README if you changed how the project is used, configured, or operated.
   The README is the product as far as a new reader is concerned.
5. Run the full pipeline against a synthetic `HOME` before you push. This is the
   check that matters most, and it is the one CI cannot do for you because it needs
   a tree to scan:

   ```bash
   HOME=/tmp/atlas-synthetic python3 atlas.py all
   python3 atlas.py doctor
   ```

## The rule that shapes most of this codebase

**A number in prose is a liability.** If a figure can come from the scan, it is
interpolated; if a table can be generated, it is generated. Hand-typed figures were
the original project's defining flaw — a table whose row *set* went stale is worse
than one whose cells do, because a wrong number invites a second look and a missing
row does not.

So when you add prose:

- Put measurements in `{{ metrics.x }}` or a generated table, never in the sentence.
- If you must assert something in words, declare it in the fragment's frontmatter as
  `assert:` so the tooling can tell you when it stops being true. Prefer removing the
  claim instead.
- If you add a table, add it to `atlas/tables.py` as a builder. Do not paste rows.

Never commit real skill inventories, credentials, or paths from your own machine.
`config/taxonomy.json` ships as a starter with empty member lists precisely because a
populated one describes one person's library and discloses it; keep it that way, and
put your own classification in your own copy of the config.

## Commit messages

Conventional-ish, imperative, and about *why*:

```
fix(taxonomy): accept a family spec with a description

A family written as {"_about": ..., "members": [...]} iterated as a list
filed every skill named "members" into that family, which is the kind of
bug that only shows up on someone else's data.
```

## Review

Reviews are about correctness, clarity and safety, not style preference. Expect to be
asked for a test. Expect to be told when something is undocumented.

## Code of conduct

Be civil. Assume good faith. Critique the code, not the person.
