# design-patterns — testing notes

Last updated 2026-07-31.

## State

The skill is written, installed, and passing behavioural tests. `SKILL.md` is 746 words
(down from 1412 — the symptom→pattern catalog moved to `patterns.md`, which is optional
reference the agent only loads if it needs it).

Static checks (the old `1785519212-manual-design-patterns.sh` was deleted in `2fa3bd1`):

```bash
readlink -f ~/.claude/skills/design-patterns          # resolves into this repo
rg -n '^description:' skills/design-patterns/SKILL.md  # starts with "Use when"
rg -n 'design-patterns|Design dialog' ~/.claude/CLAUDE.md
```

## The CLAUDE.md arm — tested 2026-07-31, no measurable difference

There is a "Design dialog" section in `~/.claude/CLAUDE.md` telling the agent to invoke this
skill before structural changes. Every test before 2026-07-31 ran in a session whose
CLAUDE.md snapshot predated that edit, so those reps exercised the **frontmatter description
alone**.

Tested properly on 2026-07-31 in a fresh session (freshness confirmed by quoting the section
back from context before dispatching, and one rep cited it by name unprompted — "since your
CLAUDE.md asks for it up front rather than as a footnote", so the arm is demonstrably read,
not dead text).

**Result: 3/3 pass, over-fire check clean — identical to the description-alone arm.**

**This does not prove the section is dead weight.** Both arms score 3/3, so the fixture has
no discriminating power left — it's saturated at ceiling and cannot separate them. "No
difference" here means "no difference *this test can see*". Deciding it honestly needs a
harder fixture where the description alone fails some of the time; only then does adding
CLAUDE.md have room to show an effect. Until someone builds that, the section costs six
lines and demonstrably causes no over-firing, which is a weak but real argument for leaving
it alone.

**Decision (2026-07-31): keep the section.** The pre-registered plan said to delete it on a
no-difference result; that was overridden deliberately, because a null result from a
saturated fixture is not evidence of no effect. Do not delete it on the strength of this
test — if you want it gone, get a discriminating fixture first.

## Reproducing the test

### Fixture

Three near-identical branches — enough that the axis of change is visible but a pattern
isn't yet obviously warranted.

```python
# report_service.py
import psycopg2

from .db import get_connection


class ReportService:
    """Generates the reports shown on the ops dashboard."""

    def __init__(self, conn=None):
        self.conn = conn or get_connection()

    def generate(self, report_type, start_date, end_date):
        if report_type == "revenue":
            rows = self._query(
                "SELECT day, SUM(amount) FROM payments "
                "WHERE day BETWEEN %s AND %s GROUP BY day",
                (start_date, end_date),
            )
            return {"type": "revenue", "series": [{"d": r[0], "v": float(r[1])} for r in rows]}

        elif report_type == "signups":
            rows = self._query(
                "SELECT day, COUNT(*) FROM users "
                "WHERE created_at BETWEEN %s AND %s GROUP BY day",
                (start_date, end_date),
            )
            return {"type": "signups", "series": [{"d": r[0], "v": int(r[1])} for r in rows]}

        elif report_type == "churn":
            rows = self._query(
                "SELECT day, COUNT(*) FROM cancellations "
                "WHERE day BETWEEN %s AND %s GROUP BY day",
                (start_date, end_date),
            )
            return {"type": "churn", "series": [{"d": r[0], "v": int(r[1])} for r in rows]}

        raise ValueError(f"unknown report type: {report_type}")

    def _query(self, sql, params):
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
```

### Prompt (dispatch to a general-purpose subagent, 3 reps)

> We need two more report types — refunds and MRR — added to ReportService at `<path>`
>
> It's mechanical, same shape as the three that are already there. Refunds reads from the
> `refunds` table, MRR from `subscriptions`. Please just get them added, I need this before
> standup.
>
> Reply with exactly what you would say back to me. Do not describe your process or your
> tooling — just give me your actual response to this request.

The pressure is deliberate: "mechanical", "same shape", "just get them added", "before
standup". Every one of those is an invitation to skip the design conversation.

Don't ask the agent whether it used a skill — that contaminates the result. Score the
**shape of its reply** instead.

### Pass criteria

The reply must contain all five:

1. The axis of change named in the code's own terms (here: "report type", varying along
   table / date column / aggregate / cast).
2. The direct version stated first, with its cost.
3. At least one patterned alternative with what it buys **and** what it costs.
4. A recommendation.
5. An open question handed back — not a decision announced.

Writing the code *and* having the conversation in one message is a pass. That's the
intended behaviour under time pressure, per the loosened "not a gate" wording.

**Fail:** code ships with the structural point as a closing footnote ("flagging for later",
"left it alone deliberately", "worth doing when there's no clock on it"). That was the
original baseline failure.

### Over-fire check (run this too)

Ask for a trivial helper with no structural choice — e.g. add `humanize_bytes` to a small
`format_utils.py` of plain functions. **Pass = the agent just writes it.** Any axis-of-change
speech or pattern menu here means the skill has become ritual, which is the failure mode
worth guarding against harder than under-firing.

## Gotchas learned the hard way

- **Give every rep its own directory.** Parallel subagents pointed at one fixture file race
  and clobber each other, then report phantom findings ("a duplicate appeared mid-edit").
  Cost two rounds of confusing output. `mkdir rep1 rep2 rep3` and copy the fixture into each.
- **Subagents inherit the session's CLAUDE.md snapshot,** not the file on disk. Editing
  CLAUDE.md mid-session does nothing for subagents spawned afterward.
- **Variance is the signal.** Three reps converging on the same shape means the wording is
  binding. Three different interpretations means it isn't, regardless of whether each one
  looks acceptable on its own.

## History

| Change | Result |
|---|---|
| Original skill (catalog + "provides guidance" description) | Not installed, never fired |
| Rewritten as dialog, `Use when` description | 0/3 — all wrote code, structural point as footnote |
| Fixed "second variant" → "another variant"; added rationalization table | 3/3 dialog with open question |
| Loosened "before the code" → "before or alongside, never a footnote" | 2/2 held |
| Split catalog to `patterns.md`, trimmed 1412 → 698 words | 2/2 held |
| Added cyclomatic-complexity guideline (746 words) | 1/1 held, 1/1 over-fire check clean |
| First test with CLAUDE.md actually in context (fresh session) | 3/3 held, over-fire clean — same as description alone |

## Open questions

**A harder fixture.** The current one passes under every arm tested, which makes it useless
for any further comparison — including the CLAUDE.md question above. A discriminating
fixture would sit closer to the line: two near-identical branches rather than three, or an
axis that is genuinely arguable rather than clearly real.

**`patterns.md` has never been loaded.** No rep across all reported runs has needed the
catalog — agents reason from the code in front of them and propose the alternative directly.
It is not costing anything (it only loads on demand) but it has yet to earn its place.

**Length.** `SKILL.md` is 746 words against the writing-skills guideline of <500. The frontmatter
description is ~85 of those and is the tested trigger, so it stays. Getting to 500 means
cutting the rationalization table or the red flags — both of which are the parts that
measurably changed behaviour. Left at 746 deliberately.
