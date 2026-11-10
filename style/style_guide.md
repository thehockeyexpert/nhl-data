# Instagram post style: Fresh Ice with team accents

Hand this folder to Claude Code. `style.json` has every value below in machine-readable form.
Visual reference: https://claude.ai/artifact/VZMyeGCYTzSYfj4SVykEQU (team mockups) and https://claude.ai/artifact/3gyPGiDVF6aXFy2LvYtFNN (chart types).

## Canvas
- 1080 x 1350 px PNG (Instagram portrait, 4:5).
- Layout, top to bottom: small uppercase label (season and topic), big title, optional one-line subtitle, the chart, then a footer line with "Data: NHL" on the left and the handle on the right.

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
