# New post prompt (copy, fill in the brackets, paste into Claude Code)

```
New story carousel. Follow style/style_guide.md (Story carousels section) exactly.

STORY: [one sentence: what's surprising, e.g. "Lane Hutson is scoring like a forward"]
SUBJECT: [player / team / country]
ACCENT: [team or country code, e.g. MTL, or CAN]
SEASON / TIMEFRAME: [e.g. 2026-27 so far, or all-time, regular season only]
COMPARE AGAINST: [optional: who or what to measure them against, or "you choose"]
MODE: mixed   (or light / dark)
MUST INCLUDE: [optional: a stat or angle you want, or "none"]
AVOID: [optional, or "none"]

Steps:
1. Query MotherDuck to test whether the story holds up. If it doesn't, tell me before drafting and suggest a better angle.
2. Draft carousels/[short-name].yml with the six slides (hook, reveal, comparison, trend, turning point, conclusion). Every number comes from a query saved under facts:. If a slide has no honest data, say so and propose skipping it.
3. Show me the draft text for all six slides and a caption that credits "Data: NHL". Wait for my edits before rendering.
4. After I approve, render the slides and show them to me. Commit only the YAML, and show me the diff first.
```
