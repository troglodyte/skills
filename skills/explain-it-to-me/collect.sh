#!/usr/bin/env bash
# Collect git evidence for a work summary.
#
# Usage:
#   collect.sh <base-ref> <head-ref>        e.g. collect.sh origin/main HEAD
#   collect.sh <base-ref>                    head defaults to HEAD
#   collect.sh --since "2 weeks ago"         time-window mode
#
# Writes evidence files to a temp dir and prints the path.

set -uo pipefail

DIFF_LINE_CAP=${DIFF_LINE_CAP:-4000}

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

MODE=range
if [ "${1:-}" = "--since" ]; then
  MODE=since
  SINCE="${2:?--since requires a date, e.g. \"2 weeks ago\"}"
  RANGE_ARGS=(--since="$SINCE")
  LABEL="since $SINCE"
  DIFF_BASE=$(git rev-list -1 --before="$SINCE" HEAD 2>/dev/null)
  DIFF_ARGS=("${DIFF_BASE:-HEAD}" HEAD)
else
  BASE="${1:?usage: collect.sh <base-ref> [head-ref]  |  collect.sh --since <date>}"
  HEAD_REF="${2:-HEAD}"
  if ! git rev-parse --verify --quiet "$BASE" >/dev/null; then
    echo "error: base ref '$BASE' not found" >&2
    exit 1
  fi
  MB=$(git merge-base "$BASE" "$HEAD_REF")
  RANGE_ARGS=("$MB..$HEAD_REF")
  DIFF_ARGS=("$MB" "$HEAD_REF")
  LABEL="$BASE...$HEAD_REF (merge-base ${MB:0:9})"
fi

OUT=$(mktemp -d -t reposummary.XXXXXX)

{
  echo "scope: $LABEL"
  echo "repo: $(basename "$(git rev-parse --show-toplevel)")"
  echo "generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "commits: $(git rev-list --count "${RANGE_ARGS[@]}" 2>/dev/null || echo '?')"
  echo "mode: $MODE"
} > "$OUT/scope.txt"

git log "${RANGE_ARGS[@]}" --stat --date=short \
  --pretty=format:'--- %h | %ad | %an | %s%n%b' > "$OUT/log.txt" 2>/dev/null

git log "${RANGE_ARGS[@]}" --pretty=format:'%h %ad %an %s' --date=short \
  > "$OUT/log-oneline.txt" 2>/dev/null

git log "${RANGE_ARGS[@]}" --pretty=format:'%an' 2>/dev/null \
  | sort | uniq -c | sort -rn > "$OUT/contributors.txt"

git log "${RANGE_ARGS[@]}" --merges --pretty=format:'%h %s' \
  > "$OUT/merges.txt" 2>/dev/null

git diff --stat "${DIFF_ARGS[@]}" > "$OUT/diffstat.txt" 2>/dev/null
git diff --name-status "${DIFF_ARGS[@]}" > "$OUT/files.txt" 2>/dev/null

# Churn per top-level directory: which areas of the codebase absorbed the work.
git diff --numstat "${DIFF_ARGS[@]}" 2>/dev/null \
  | awk '{split($3,p,"/"); a=(p[2]==""?".":p[1]); add[a]+=$1; del[a]+=$2; n[a]++}
         END{for(k in add) printf "%-30s +%-7d -%-7d %d files\n", k, add[k], del[k], n[k]}' \
  | sort -k2 -r > "$OUT/churn-by-area.txt"

# Files most likely to matter operationally.
grep -Ei '(migration|schema|\.sql$|docker|compose|Makefile|\.ya?ml$|\.toml$|\.env|requirements|package\.json|go\.mod|Cargo\.toml|Gemfile|\.github/)' \
  "$OUT/files.txt" > "$OUT/notable-files.txt" 2>/dev/null

# New loose-end markers introduced by this work.
git diff "${DIFF_ARGS[@]}" 2>/dev/null \
  | grep -E '^\+' | grep -Ei '(TODO|FIXME|XXX|HACK|skip\(|xit\(|@Ignore|pytest.mark.skip)' \
  | head -100 > "$OUT/loose-ends.txt"

git diff "${DIFF_ARGS[@]}" -- . ':(exclude)*lock*' ':(exclude)*.lock' \
  ':(exclude)*-lock.json' ':(exclude)vendor/*' ':(exclude)*.min.*' \
  ':(exclude)*.snap' 2>/dev/null | head -n "$DIFF_LINE_CAP" > "$OUT/diff.txt"

TOTAL=$(git diff "${DIFF_ARGS[@]}" 2>/dev/null | wc -l | tr -d ' ')
if [ "${TOTAL:-0}" -gt "$DIFF_LINE_CAP" ]; then
  echo "NOTE: diff.txt truncated at $DIFF_LINE_CAP of $TOTAL lines." >> "$OUT/scope.txt"
  echo "Read specific files with: git diff ${DIFF_ARGS[*]} -- <path>" >> "$OUT/scope.txt"
fi

echo "$OUT"
echo "--- files written ---" >&2
ls -la "$OUT" >&2
