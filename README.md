# skills

Claude Code agent skills, packaged as a plugin.

## Install

```
/plugin marketplace add troglodyte/skills
/plugin install skills@trog-skills
```

## What's in it

| Skill | Fires when |
|---|---|
| `design-patterns` | You're about to write code with a structural choice — a new module, another variant of something that exists, one more branch in a type dispatch, a config object that keeps growing. Runs a short dialog to name the axis of change and settle the shape, starting from the direct version. |
| `run-script-handoff` | You're about to hand a human a command to run in their own terminal and paste back. Covers the task slug, `run/<slug>.sh`, colored output helpers, and the `tee` + clipboard invocation line. |
