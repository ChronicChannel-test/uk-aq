# Dev Blog Folder

This folder contains a simple beta-facing development blog/roadmap page for the UK AQ website.

- Expected URL: `/dev-blog/`
- Valid statuses for posts: `Planned`, `In progress`, `Completed`
- Live exclusion/inclusion is handled separately in `sync_to_live.sh` and should not be changed as part of this task.

## Contents

- `index.html` renders grouped roadmap cards from markdown posts in `posts/`.
- `posts/` stores one markdown file per roadmap entry with minimal front matter.

- `scripts/generate-posts-json.mjs` regenerates `posts/posts.json` from `.md` files.

## Pre-commit hook

This repo uses `.githooks/pre-commit` to automatically regenerate `posts/posts.json`
before every commit (including commits made from GitHub Desktop).

To enable the hook, run:

```bash
git config core.hooksPath .githooks
```
