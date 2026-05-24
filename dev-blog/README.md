# Dev Blog Folder

This folder contains a simple beta-facing development blog/roadmap page for the UK AQ website.

- Expected URL: `/dev-blog/`
- Valid statuses for posts: `Planned`, `In progress`, `Completed`
- Live exclusion/inclusion is handled separately in `sync_to_live.sh` and should not be changed as part of this task.

## Contents

- `index.html` renders grouped roadmap cards from markdown posts in `posts/`.
- `posts/` stores one markdown file per roadmap entry with minimal front matter.
