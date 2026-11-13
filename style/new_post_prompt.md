# New post prompt (copy, fill in the brackets, paste into Claude Code)

```
New story carousel. Read style/story_playbook.md and follow it, together with the design rules in
style/style_guide.md (Story carousels section) and carousels/README.md.

IDEA: [what you've noticed, or "pitch me 3 ideas" about a player/team/topic]
SUBJECT: [player / team / country]
ACCENT: [team or country code, e.g. MTL, or CAN]
TIMEFRAME: [e.g. 2026-27 so far, or all-time, regular season only]
TAKE: [optional: the argument you want to make, or "you choose"]
LENGTH: [you choose (usually 6-10), or a number]
MODE: mixed   (or light / dark)
MUST INCLUDE: [optional: a stat, chart or angle, or "none"]
IMAGES: [none / headshot / Commons photo / my photo file + which slide]
AVOID: [optional, or "none"]

Steps:
1. Investigate first. Query MotherDuck to test the idea and find the most surprising true angle. Bring me the best
   2 or 3 options, each with: the hook headline, the one-sentence take, the strongest number behind it, the strongest
   counterargument, and a guess at whether it is a send, save or comment post. Recommend one. If the idea doesn't hold
   up, say so and pitch better ones. Wait for my pick.
2. Outline the chosen story slide by slide, as a table: beat (hook, re-hook, reveal, proof, twist, verdict, question),
   the slide type, the headline, the hero number, and the chart. Explain any slide you'd cut. Wait for my OK.
3. Draft carousels/[short-name].yml. Every number comes from a query saved under facts: with dates pinned. Write
   the caption following the playbook (hook line, context, question, credit "Data: NHL.", 3 to 5 hashtags).
   Run the playbook's final checklist and tell me any item that fails.
4. Show me all slide text and the caption. Wait for my edits before rendering.
5. After I approve, render and show me the slides. Commit only the YAML, and show me the diff first.
```
