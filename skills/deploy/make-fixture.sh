#!/usr/bin/env bash
set -e
ROOT="$1"
rm -rf "$ROOT" && mkdir -p "$ROOT"
cd "$ROOT"
git init -q --bare origin.git
git init -q -b main work
cd work
git config user.email t@example.com && git config user.name Tester
git remote add origin ../origin.git
cat > package.json <<'EOF'
{
  "name": "widgetkit",
  "version": "1.4.2",
  "description": "Widget layout helpers",
  "main": "src/index.js"
}
EOF
cat > CHANGELOG.md <<'EOF'
# Changelog

Versions follow semantic versioning.

## 1.4.2

- Fix widget padding on narrow viewports.

## 1.4.1

- Initial changelog.
EOF
mkdir -p src
echo "export const gap = 8;" > src/index.js
echo "node_modules/" > .gitignore
git add -A && git commit -qm "release: 1.4.2"
git tag -a v1.4.2 -m "v1.4.2"
git push -q origin main --follow-tags
git checkout -qb feat/widget-sizes
echo "export const sizes = { sm: 4, md: 8, lg: 16 };" > src/sizes.js
git add -A && git commit -qm "feat(sizes): add the size scale"
echo "export const gap = sizes.md;" >> src/index.js
git add -A && git commit -qm "feat(sizes): drive gap off the scale"
echo "// TODO: document the scale" >> src/sizes.js
git branch -q chore/old-cleanup main
git worktree add -q ../wt-old chore/old-cleanup
