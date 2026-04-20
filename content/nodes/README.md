# Lesson Content (Nodes)

Each lesson is a **Node** in the Galaxy Path DAG. Authored as MDX + a FEN/PGN bundle.

Schema (arrives in PR #3):
```
content/nodes/<domain>/<slug>/
  index.mdx       # concept text (<400 words)
  drills.yaml     # list of FEN/PGN + solution UCI + theme
  meta.yaml       # slug, domain, rating_min, rating_max, prereqs, branch_group
```

PR #3 ships the first ten hand-authored nodes targeting 1000–1800 Elo weaknesses:
board vision, fork vision, pin absolute/relative, back-rank, Lucena, Philidor,
opposition, CCT heuristic, time-management drill, blunder-check routine.
