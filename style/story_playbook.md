# Story playbook: how every carousel is written

Read this before drafting any carousel. You are four people at once:

- **Social media lead.** You write for reach. On Instagram the signals that matter most are time spent on the post (people swiping), **sends** (shared in DMs), **saves** and comments. Every choice below serves one of those.
- **Behavioural psychologist.** You know why a thumb stops: curiosity gaps, surprise, identity, and the urge to argue.
- **Data storyteller.** One idea per slide, one chart per idea, and the chart title states the finding, not the topic.
- **Storyteller.** A hook that opens a question, slides that each answer a little and open a bigger one, a twist, and an ending people want to respond to.

The rule above all: **the hook can provoke, but the data must pay it off.** A hook the slides don't deliver kills saves, sends and trust. Never mislead.

---

## 1. Find the story before writing anything

A post needs all three:

1. **A surprise.** Something a regular fan would get wrong if asked. Test it: "Would my friend at the bar guess this?" If yes, it isn't a story.
2. **A stake.** Someone to root for or against: a team, a star, a rivalry, a country, "your team".
3. **A take.** One sentence you could argue about, backed by numbers: "Draisaitl is the best goal scorer alive, not McDavid." If the data only supports a softer version, use the softer version.

Story types that travel well:

| Type | Example take |
|---|---|
| **Overrated / underrated** | "The Leafs' power play is the reason they lose, not their goalie." |
| **Hidden giant** | "A defenceman is outscoring 700 forwards." |
| **History is being made** | "Nobody has started like this in 30 years." |
| **It's luck, and it ends** | "Seattle's hot start is built on a save % that never lasts." (PDO) |
| **Myth buster** | "Fighting doesn't win games. Here's 20 years of proof." |
| **Head-to-head** | "Matthews vs Draisaitl: who's the better shooter?" |
| **Your team in context** | "Where every team ranks on shots allowed." (high save and send value) |
| **Then vs now** | "Goals per game is back to 1990s levels." |

## 2. The arc (length follows the story, usually 6 to 10 slides)

Instagram allows up to 20 slides. More slides only help if every one earns its swipe. Cut any slide that doesn't surprise, prove or move the argument.

| Beat | Slides | Job | Psychology |
|---|---|---|---|
| **Hook** | 1 | Stop the scroll and open a question | Curiosity gap, pattern interrupt |
| **Re-hook** | 1 (often the 2nd slide) | Raise the stakes: why this matters, or a "guess first" | Commitment: a guess makes people swipe to check |
| **Reveal** | 1 | Answer the first question with one huge number | Surprise rewards the swipe |
| **Proof** | 1 to 4 | Show it's real: comparison, ranking, trend, shot map | Specific numbers build trust |
| **Twist** | 0 to 1 | The counterpoint or the catch, then why the take still stands | Fairness makes a hot take credible and arguable |
| **Verdict** | 1 | The take, said plainly | Peak-end rule: the last strong feeling is what's remembered |
| **Question** | 1 | An easy-to-answer prompt | Low effort to reply = more comments |

Every slide except the last must leave something unanswered, so the next swipe is the payoff.

## 3. Hooks (slide 1)

At most 8 words of headline, plus a small kicker. Specific beats vague, and numbers beat adjectives.

Formulas:
- **Unbelievable number:** "1 player. 49 points. 20 games."
- **Contradiction:** "The NHL's best team can't shoot."
- **Rank shock:** "The 3rd best goalie in the league plays in Chicago."
- **History:** "Nobody has done this since Gretzky."
- **Callout:** "Your team is lying to you about its goalie."
- **Guess:** "Guess how many goals Ovechkin has this year."
- **Debate starter:** "The most overrated player in the NHL. By the numbers."

Hook rules:
- The hook must be true, and the reveal must come by slide 3.
- Name a star, team or rivalry people already have feelings about.
- No questions the reader can answer without swiping ("Is McDavid good?").
- A face (headshot or Commons photo) on the hook usually stops more thumbs than text alone.

## 4. One slide, one idea

- **At most about 20 words on a slide**, excluding chart labels. Big type, read in 2 seconds.
- **One number is the hero** on any slide. Everything else supports it or goes.
- **The title tells the finding:** "Edmonton takes more shots than anyone", not "Shots by team".
- **Human scale:** turn rates into something felt: "a point every 24 minutes", "more than every other night", "1 in 9 shots goes in".
- **Round for the slide, keep the exact number in the facts.** "49 points" is exact; "nearly 2.5 a game" is fine.
- **End on an open loop:** a line or a visual that leaves the next question hanging ("But that's not the strange part.").

## 5. Picking the chart

Pick the chart from the question the slide answers.

| The question | Show it as | Notes |
|---|---|---|
| How big is it? | **Hero number** | One huge number, two-line label |
| Them vs them? | **Head-to-head split** | Two big numbers, subject in the accent |
| Where do they rank? | **Leaderboard** (top 5, subject highlighted) | If the subject isn't top 5, show top 3 + the subject with a gap marker |
| How unusual is it? | **Dot strip / distribution** | Every player or team as a grey dot, the subject in the accent: outliers jump out |
| How has it changed? | **Line chart** | Subject line in the accent, 1 to 2 comparison lines, labels at line ends, no legend |
| Where on the ice? | **Rink shot map** | Real shot locations from `fct_shots` (2009-10 on), goals in the accent |
| Guess first | **Quiz slide** | The question and 3 or 4 options. The next slide reveals |
| What's the take? | **Statement slide** | Just the sentence, huge, no chart |

Honesty rules for charts:
- Bars start at zero. Lines may zoom in, but say so in the axis.
- Same scale when comparing.
- Respect sample sizes (`docs/motherduck_guide.md` minimums). Never rank someone with 3 games played.
- One accent per slide, on the subject only.

## 6. The controversial take, done right

- Aim the heat at performance, contracts, reputations and decisions, never at people's character.
- Back it with at least two independent numbers (e.g. goals and shot share), not one cherry-picked stat.
- Give the other side one slide (the twist): "Yes, he's scored 11 goals. But..." This makes the post fairer, and it gives commenters something to grab.
- Use confident words ("is", "the best", "overrated") only where the numbers clearly back them. Otherwise "might be", "so far" or "by this measure".
- Luck stats (shooting %, save %, PDO) are perfect for "it won't last" takes. Say "so far" and give the sample size.

## 7. The ending

- **Verdict slide:** the take in 6 to 10 words. The second line is in the accent.
- **Question slide:** one question people can answer in a word or a name:
  - Choice: "Draisaitl or McDavid: who'd you take for one goal?"
  - Prediction: "Will Seattle still be top 5 by Christmas? Yes or no."
  - Ranking: "Who's #1 on your list?"
  - Tribal: "Which fan base is about to be furious?"
- Never "Thoughts?" or "Agree?".
- Add one share prompt only where it fits naturally: "Send this to the Leafs fan in your life."

## 8. The caption

1. **First line (shows before "more"):** a second hook, different from the slide 1 headline. Under about 125 characters.
2. **2 to 4 short lines:** the context that didn't fit on the slides, such as the timeframe, method or minimums.
3. **The question again**, worded differently from the last slide.
4. **Save/send prompt** when the post is a ranking or reference: "Save this for the trade deadline."
5. **Credit line:** "Data: NHL." (or "Data, logos and headshots: NHL." when any NHL image is used), plus any photo credit.
6. **3 to 5 hashtags:** the team(s), the player, plus #NHL and one niche tag (#hockeystats or #hockeyanalytics).

## 9. Final checklist before showing the draft

- [ ] Would a casual fan stop on slide 1? Is the reveal by slide 3?
- [ ] Does every slide leave a reason to swipe?
- [ ] One idea and one hero number per slide, about 20 words maximum?
- [ ] Is every number backed by a saved fact with a pinned date?
- [ ] Does the take survive the counterpoint slide?
- [ ] Can the question be answered in one word or a name?
- [ ] Does the caption's first line work as a hook on its own?
- [ ] Would someone send this to a friend, or save it? If neither, sharpen the take or add a ranking.
