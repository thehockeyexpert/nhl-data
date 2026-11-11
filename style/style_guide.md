# Instagram post style: Fresh Ice Studio Edition, six-part story carousels

Hand this folder to Claude Code. `style.json` has every value below in machine-readable form.
Visual reference: https://claude.ai/artifact/VZMyeGCYTzSYfj4SVykEQU (team mockups) and https://claude.ai/artifact/3gyPGiDVF6aXFy2LvYtFNN (chart types).

## Canvas
- 1080 x 1350 px PNG (Instagram portrait, 4:5).

## Layout: Studio Edition (current)
Reference: https://claude.ai/artifact/PLNc8Lx581KfYjdGZunhxw, and `studio_reference.html` in this folder, which has every coordinate and size.
All positions are in pixels on the 1080 x 1350 canvas.

**Frame (every slide)**
- Margins are 72 px left and right, and everything aligns to the left margin. Numbers are right-aligned to the right margin.
- Header: the label at y=104 (Barlow Condensed Bold 26 px, uppercase, letter-spacing 3.5, muted colour). The slide counter "01 / 06" is right-aligned on the same line, and there is no counter on single posts. A hairline at y=132 is 2 px, in ink at 14% opacity (16% on dark).
- Footer: a hairline at y=1248. "DATA: NHL · THROUGH <date>" sits at the left at y=1290 and "@handle" at the right, both Barlow Condensed SemiBold 22 px, uppercase, letter-spaced and muted.
- Nothing inside the post has rounded corners, shadows or chart frames. Hairlines separate things.

**Slide types**
- **Cover (hero number):** one huge number in the accent colour (Barlow Condensed ExtraBold, about 600 px, tight letter-spacing) with a small two-line uppercase label beside its baseline. Below it come the name (Barlow Condensed Bold 104 px) and a one-line subtitle (Barlow Medium 36 px, muted). At the bottom, a hairline and up to four supporting stats (value 64 px, label 22 px uppercase).
- **Leaderboard:** the title (Barlow Condensed Bold 112 px) and subtitle (Barlow 36 px, muted), then up to five rows 128 px apart. Each row has a rank "01" (30 px, muted, accent for the leader), the name (Barlow Semi Condensed SemiBold 44 px) followed by the team code (24 px, muted), the value right-aligned (Barlow Condensed Bold 64 px), and a flat 8 px bar under the name with square ends. Only the leader's bar and value use the accent. Hairlines run between rows.
- **Table:** the title and subtitle, then column headers (22 px uppercase, muted) and a 2 px rule. Rows are 84 px apart with hairlines. Ties show as "T6". The highlighted row gets a soft tint background and an 8 px accent bar at the left edge, with its rank and value in the accent.
- **Team post:** a full-width block in the team colour from y=133 to y=553. It holds the code line ("MTL · TOP SCORERS", 30 px) and the team name on two lines (Barlow Condensed Bold 128 px). Text in the block is white if contrast is at least 4.5:1, otherwise ink. Below it, three columns divided by hairlines each hold a rank, a big value (260 px, with the leader in the team colour), the player's first and last name on two lines (40 px), and "POINTS".
- **Chart slides** (line, donut, histogram) use the same frame, title and subtitle. Use 2 px lines, flat square-ended bars, hairline gridlines and no chart border, with the accent on one thing only.


## Story carousels (the default format for every post)
Reference: https://claude.ai/artifact/9EWfk3pyxgcp4YMmzZXwLR, and `story_reference.html` in this folder, which has every coordinate and size. It overrides the Studio Edition section wherever the two differ.

**Frame (overrides the Studio Edition frame):** margins are 80 px left and right. There is NO header label, NO slide counter, NO hairlines at the top or bottom, and NO source line. The only fixed element is the handle, at the bottom right (x = 1000, right-aligned, y = 1290, Barlow Condensed SemiBold 24 px, uppercase, muted). The NHL data credit goes in the post caption or comments, not on the image. Panels and full-bleed backgrounds run to the edges of the canvas.

**Six slides, always in this order.** Every post tells one story. Skip a slide only if there's no honest data for it.
| # | Role | Treatment | Purpose |
|---|---|---|---|
| A | Hook | Full-bleed navy, a large faint half-rink drawing, a small accent kicker, and a three-line headline (150 px) whose last line is in the accent | Create intrigue |
| B | Reveal | The Studio Edition hero number (about 600 px) with a two-line label, the name, a one-line subtitle and up to four stats | Deliver the surprise |
| C | Comparison | Split top and bottom. The top half is a panel from the top edge down to y = 690 (#E4EAF0 light, #202A35 dark) with the subject's number in the accent; the bottom half has the comparison number in ink. Each half has a kicker, a 400 px number, and one short line beside it that adds what the kicker doesn't say | Challenge expectations |
| D | Trend | A clean line chart: the subject's line in the accent (8 px), others in ink at 85% and 40% opacity (4 px), a label at the end of each line instead of a legend, hairline gridlines and an axis title | Context over time |
| E | Turning point | The "how" slide. A stat column on the left (big numbers with two-line labels and hairlines, one number in the accent) and a half-rink diagram on the right, with no closing paragraph. Arrows or markers on the rink are labelled "ILLUSTRATION, NOT TRACKED PASSES" unless they come from real shot data | Explain why |
| F | Conclusion | A small kicker, a decisive headline (190 px, second line in the accent), one line of context, a hairline, then a question (96 px) and "Tell us in the comments." | Encourage discussion |

**Light and dark:** "mixed" is the default. A, B and F are dark, and C, D and E are light. Also support all-light and all-dark.

**Rink drawing:** a half rink drawn to real proportions (85 x 100 ft): boards, red centre and goal lines, blue line, centre circle, two end-zone faceoff circles and the crease. On the hook it is faint (14 to 16% opacity) and sits behind the headline, clear of the handle.

**Writing rules**
- Every number comes from a query, saved under `facts:` in the carousel YAML and re-checked on render.
- No claims that aren't in the data, such as tactics or who plays on which unit.
- Headlines are short and declarative, and the question on slide F has to be something people can answer in the comments.
- No photos or logos. The rink drawing and the typography are the visuals.
- **As clean as possible.** Every piece of text has to add something new. Never repeat a fact already on the slide: a label and a sentence must not say the same thing, a question isn't repeated as a graphic, and a closing paragraph doesn't restate the stat column. When in doubt, cut it.

## Palettes
Alternate between light and dark.

| Role | Fresh Ice light | Fresh Ice dark |
|---|---|---|
| Background | #F4F7F9 | #0E1A26 |
| Ink (text, normal bars and lines) | #0E1A26 | #F4F7F9 |
| Muted text (subtitle, axes, footer) | #5B6977 | #9AA8B6 |
| Bar track | #E1E7EC | #1E2D3C |
| Gridlines | #DCE3E9 | #22313F |
| Default accent (no team or country) | #FF5A36 | #FF5A36 |

## Fonts (free Google Fonts)
- Title: Barlow Condensed Bold.
- Label: Barlow Condensed Bold, uppercase, letter-spaced.
- Names and numbers: Barlow SemiBold and Bold.

## The accent rule
- **The accent belongs to the subject.** Anthony names the team or country for each post, and its colour comes from `team_accents` or `country_accents`.
- **Only one thing gets the accent:** the leader's bar, the highlighted slice, or the latest point on a line. Everything else is ink.
- **Readability:** bars and shapes need contrast of at least 3:1 against the background, and text needs at least 4.5:1. If a colour falls short, shade it toward white on dark backgrounds, or toward black on light ones, until it passes, keeping the hue. Examples are Bruins gold on light and Kings black on dark.

## Rules for anything posted
- Facts and figures from the NHL data only, with no NHL or team logos or photos.
- Birthplace maps credit GeoNames: "Place data: GeoNames.org (CC BY 4.0)".
- No MoneyPuck data.

## Team colours
Taken from each team's primary or signature colour, from memory, except the Canucks blue #07346F, which Anthony chose. Check any colour against the team's brand page before relying on it.

| Team | Accent |
|---|---|
| Anaheim Ducks | #FC4C02 (Orange) |
| Boston Bruins | #FFB81C (Gold) |
| Buffalo Sabres | #003087 (Royal blue) |
| Calgary Flames | #C8102E (Red) |
| Carolina Hurricanes | #CE1126 (Red) |
| Chicago Blackhawks | #CF0A2C (Red) |
| Colorado Avalanche | #6F263D (Burgundy) |
| Columbus Blue Jackets | #002654 (Union blue) |
| Dallas Stars | #006847 (Victory green) |
| Detroit Red Wings | #CE1126 (Red) |
| Edmonton Oilers | #FF4C00 (Orange) |
| Florida Panthers | #C8102E (Red) |
| Los Angeles Kings | #111111 (Black) |
| Minnesota Wild | #154734 (Forest green) |
| Montréal Canadiens | #AF1E2D (Red) |
| Nashville Predators | #FFB81C (Gold) |
| New Jersey Devils | #CE1126 (Red) |
| New York Islanders | #00539B (Royal blue) |
| New York Rangers | #0038A8 (Blue) |
| Ottawa Senators | #DA1A32 (Red) |
| Philadelphia Flyers | #F74902 (Orange) |
| Pittsburgh Penguins | #FCB514 (Gold) |
| San Jose Sharks | #006D75 (Teal) |
| Seattle Kraken | #99D9D9 (Ice blue) |
| St. Louis Blues | #002F87 (Blue) |
| Tampa Bay Lightning | #002868 (Blue) |
| Toronto Maple Leafs | #00205B (Blue) |
| Utah Mammoth | #69B3E7 (Mountain blue) |
| Vancouver Canucks | #07346F (Blue) |
| Vegas Golden Knights | #B4975A (Gold) |
| Washington Capitals | #C8102E (Red) |
| Winnipeg Jets | #004C97 (Aviator blue) |

Country: Canada #D52B1E (Canada red). Add other countries the same way when needed.
