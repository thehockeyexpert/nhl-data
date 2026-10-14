# Game type evidence: unlabelled (season, game type) pairs

Generated 2026-10-14 from the loaded data in MotherDuck (`staging.stg_nhl_web__schedule_games` for names, dates
and venues; `staging.stg_nhl_stats__games` for counts and team IDs). Each pair goes into
`dbt/seeds/game_type_labels.csv` only after the owner approves it.

**Decision (2026-10-14).** The owner approved the High-confidence types (4, 9, 10, 13, 19, 20) for every season
that meets an explicit rule. 75 pairs were added to the seed. Their evidence says "No external source checked",
except 2004-05, which cites its source.

- The one pair that broke its rule stays `unknown type 4`: **1948-49, type 4**. It was played on 1948-11-03,
  after that season's regular season began (1948-10-13), and it is listed as a Toronto home game at Chicago Stadium.
- The Medium-confidence types (6, 7, 8, 12 for 2023-24, 14 and 18) were held back at first.

**Decision (2026-10-14, later).** Sources were found for all 16 Medium-confidence pairs, and the owner approved them:

| Type | Label |
|---|---|
| 6 | `world_cup_group` |
| 7 | `world_cup_knockout` |
| 8 | `world_cup_pretournament` |
| 12 | `all_star_womens_game` |
| 14 | `canada_cup` |
| 18 | `exhibition_tour` |

Each seed row names its sources (Wikipedia, NHL.com, Canadian Press), what they confirm, and where they differ. The differences are listed in `docs/data_coverage.md`. The only unlabelled pair left is (1948-49, 4).

The rules applied:

| Type | Label | Rule |
|---|---|---|
| 4 | `all_star` | One game a season, or three on one date from 2015-16. Every game has at least one team that is not an NHL club, and at most one NHL club takes part. Before 1966-67 the game is before the first regular-season game; from 1966-67 it falls between the first and last regular-season games. One venue. |
| 9 | `olympics` | Every game in February, only national teams (no NHL club), at least 12 teams |
| 10 | `all_star_youngstars` | One game between Young Stars East and West, the day before that season's type 4 game, at the same venue |
| 13 | `cancelled` | 2004-05 only. Every game 0-0 with no period and game state 6, only NHL clubs, none in the weekly schedule, no season facts |
| 19 | `four_nations_round_robin` | Only national teams. Four teams, each playing the other three exactly once, within one week |
| 20 | `four_nations_final` | One game between two of that season's type 19 teams, after the last type 19 game |

Every rule also requires the game list and the weekly schedule to hold the same number of games, all of them finished. Type 13 is the exception, since the weekly schedule has none of its games.

How to read this:

- **Pairs:** 92 (season, game type) pairs across 12 game types are unlabelled. 66 of them are type 4.
- **Proposed label:** my reading of the data. It is not a fact until you approve it.
- **Confidence:** how strongly the data alone supports the label. *High*: the teams, dates and venues
  leave little doubt. *Medium*: the data fits, but the label leans on my general knowledge, or something
  in the data is odd. I have **not** checked any external source for these labels. Where I name an
  event (for example "Canada Cup"), that comes from general knowledge, not from a source I checked.
- **Home and away:** these are as the NHL lists them. For neutral-site events the "home" team is
  nominal; the venue is the better guide.
- **Counts:** in every pair below, the weekly schedule and the game list have the same number of games,
  except type 13 (2004-05), where the schedule has none.
- **Garbled names:** a few venue names are garbled in the NHL's own data, for example `Sportovn√≠ hala`
  (Sportovní hala) and `Le Colis√©e` (Le Colisée). They are shown as received.

## Summary

| Type | Pairs | Games | Proposed label | Confidence |
|---|---|---|---|---|
| 4 | 66 | 80 | `all_star` | High |
| 6 | 3 | 36 | `world_cup_group` | High (2016-17), Medium (1996-97, 2003-04) |
| 7 | 3 | 18 | `world_cup_knockout` | High (2016-17), Medium (1996-97, 2003-04) |
| 8 | 1 | 12 | `world_cup_exhibition` | Medium |
| 9 | 5 | 168 | `olympics` | High |
| 10 | 2 | 2 | `all_star_youngstars` | High |
| 12 | 1 | 1 | `all_star_womens_game` | Medium |
| 13 | 1 | 1,230 | `cancelled` | High |
| 14 | 5 | 93 | `canada_cup` | Medium |
| 18 | 3 | 36 | `exhibition_tour` | Medium |
| 19 | 1 | 6 | `four_nations_round_robin` | High |
| 20 | 1 | 1 | `four_nations_final` | High |

To approve, tell me which pairs (or which whole types) to add. Each becomes one row in the seed with its
evidence line.

## Type 4: proposed `all_star` (High)

Already approved: (1967-68, 4) and (2019-20, 4) as `all_star`. The 66 pairs below have the same shape:

- One game a season, three a season from 2015-16. No pair has more than four teams.
- Before 1966-67 the game is in October, before the regular season, and usually pits one NHL club against
  a team called "All-Stars" (team 7428). Exceptions: 1951-52 and 1952-53 are First Team All-Stars against
  Second Team All-Stars.
- From 1966-67 the game is mid-season (January or February). From 1968-69 neither side is an NHL club: the
  teams are East/West, Wales/Campbell conference, North America/World, captains' teams ("Team Lidstrom") or,
  from 2015-16, the four divisions in a three-game format.

Observed oddities, all unexplained:

- 1948-49: listed as All-Stars at Toronto Maple Leafs, but the venue is Chicago Stadium.
- 2002-03 and 2008-09 ended in a shootout; 2023-24 has one game ending in a shootout.
- Seasons between 1947-48 and 2023-24 with **no** type 4 game: 1978-79, 1986-87, 1994-95, 2004-05, 2005-06, 2009-10, 2012-13, 2013-14, 2020-21. I have not looked for the reason.

| Season | Date | Game(s) | Venue |
|---|---|---|---|
| 1947-48 | 1947-10-13 | All-Stars (ALL) 4 at Toronto Maple Leafs (TOR) 3 | Maple Leaf Gardens |
| 1948-49 | 1948-11-03 | All-Stars (ALL) 3 at Toronto Maple Leafs (TOR) 1 | Chicago Stadium |
| 1949-50 | 1949-10-10 | All-Stars (ALL) 3 at Toronto Maple Leafs (TOR) 1 | Maple Leaf Gardens |
| 1950-51 | 1950-10-08 | Detroit Red Wings (DET) 7 at All-Stars (ALL) 1 | Detroit Olympia |
| 1951-52 | 1951-10-09 | First Team All-Stars (1ST) 2 at Second Team All-Stars (2ND) 2 | Maple Leaf Gardens |
| 1952-53 | 1952-10-05 | First Team All-Stars (1ST) 1 at Second Team All-Stars (2ND) 1 | Detroit Olympia |
| 1953-54 | 1953-10-03 | All-Stars (ALL) 3 at Montréal Canadiens (MTL) 1 | Montreal Forum |
| 1954-55 | 1954-10-02 | All-Stars (ALL) 2 at Detroit Red Wings (DET) 2 | Detroit Olympia |
| 1955-56 | 1955-10-02 | All-Stars (ALL) 1 at Detroit Red Wings (DET) 3 | Detroit Olympia |
| 1956-57 | 1956-10-09 | All-Stars (ALL) 1 at Montréal Canadiens (MTL) 1 | Montreal Forum |
| 1957-58 | 1957-10-05 | All-Stars (ALL) 5 at Montréal Canadiens (MTL) 3 | Montreal Forum |
| 1958-59 | 1958-10-04 | Montréal Canadiens (MTL) 6 at All-Stars (ALL) 3 | Montreal Forum |
| 1959-60 | 1959-10-03 | Montréal Canadiens (MTL) 6 at All-Stars (ALL) 1 | Montreal Forum |
| 1960-61 | 1960-10-01 | All-Stars (ALL) 2 at Montréal Canadiens (MTL) 1 | Montreal Forum |
| 1961-62 | 1961-10-07 | All-Stars (ALL) 3 at Chicago Blackhawks (CHI) 1 | Chicago Stadium |
| 1962-63 | 1962-10-06 | Toronto Maple Leafs (TOR) 4 at All-Stars (ALL) 1 | Maple Leaf Gardens |
| 1963-64 | 1963-10-05 | All-Stars (ALL) 3 at Toronto Maple Leafs (TOR) 3 | Maple Leaf Gardens |
| 1964-65 | 1964-10-10 | All-Stars (ALL) 3 at Toronto Maple Leafs (TOR) 2 | Maple Leaf Gardens |
| 1965-66 | 1965-10-20 | All-Stars (ALL) 5 at Montréal Canadiens (MTL) 2 | Montreal Forum |
| 1966-67 | 1967-01-18 | Montréal Canadiens (MTL) 3 at All-Stars (ALL) 0 | Montreal Forum |
| 1968-69 | 1969-01-21 | All-Stars East (ASE) 3 at All-Stars West (ASW) 3 | Montreal Forum |
| 1969-70 | 1970-01-20 | All-Stars East (ASE) 4 at All-Stars West (ASW) 1 | St. Louis Arena |
| 1970-71 | 1971-01-19 | All-Stars West (ASW) 2 at All-Stars East (ASE) 1 | Boston Garden |
| 1971-72 | 1972-01-25 | All-Stars East (ASE) 3 at All-Stars West (ASW) 2 | Metropolitan Sports Center |
| 1972-73 | 1973-01-30 | All-Stars East (ASE) 5 at All-Stars West (ASW) 4 | Madison Square Garden |
| 1973-74 | 1974-01-29 | All-Stars West (ASW) 6 at All-Stars East (ASE) 4 | Chicago Stadium |
| 1974-75 | 1975-01-21 | Wales Conference All-Stars (WLS) 7 at Campbell Conference All-Stars (CMP) 1 | Montreal Forum |
| 1975-76 | 1976-01-20 | Wales Conference All-Stars (WLS) 7 at Campbell Conference All-Stars (CMP) 5 | Spectrum |
| 1976-77 | 1977-01-25 | Wales Conference All-Stars (WLS) 4 at Campbell Conference All-Stars (CMP) 3 | Pacific Coliseum |
| 1977-78 | 1978-01-24 | Wales Conference All-Stars (WLS) 3 at Campbell Conference All-Stars (CMP) 2 | Buffalo Memorial Auditorium |
| 1979-80 | 1980-02-05 | Wales Conference All-Stars (WLS) 6 at Campbell Conference All-Stars (CMP) 3 | Joe Louis Arena |
| 1980-81 | 1981-02-10 | Campbell Conference All-Stars (CMP) 4 at Wales Conference All-Stars (WLS) 1 | The Forum |
| 1981-82 | 1982-02-09 | Wales Conference All-Stars (WLS) 4 at Campbell Conference All-Stars (CMP) 2 | Capital Centre |
| 1982-83 | 1983-02-08 | Campbell Conference All-Stars (CMP) 9 at Wales Conference All-Stars (WLS) 3 | Nassau Veterans Memorial Coliseum |
| 1983-84 | 1984-01-31 | Wales Conference All-Stars (WLS) 7 at Campbell Conference All-Stars (CMP) 6 | Brendan Byrne Arena |
| 1984-85 | 1985-02-12 | Wales Conference All-Stars (WLS) 6 at Campbell Conference All-Stars (CMP) 4 | Olympic Saddledome |
| 1985-86 | 1986-02-04 | Wales Conference All-Stars (WLS) 4 at Campbell Conference All-Stars (CMP) 3 | Hartford Civic Center |
| 1987-88 | 1988-02-09 | Wales Conference All-Stars (WLS) 6 at Campbell Conference All-Stars (CMP) 5 | St. Louis Arena |
| 1988-89 | 1989-02-07 | Campbell Conference All-Stars (CMP) 9 at Wales Conference All-Stars (WLS) 5 | Northlands Coliseum |
| 1989-90 | 1990-01-21 | Wales Conference All-Stars (WLS) 12 at Campbell Conference All-Stars (CMP) 7 | Civic Arena |
| 1990-91 | 1991-01-19 | Campbell Conference All-Stars (CMP) 11 at Wales Conference All-Stars (WLS) 5 | Chicago Stadium |
| 1991-92 | 1992-01-18 | Campbell Conference All-Stars (CMP) 10 at Wales Conference All-Stars (WLS) 6 | Spectrum |
| 1992-93 | 1993-02-06 | Wales Conference All-Stars (WLS) 16 at Campbell Conference All-Stars (CMP) 6 | Montreal Forum |
| 1993-94 | 1994-01-22 | All-Stars East (ASE) 9 at All-Stars West (ASW) 8 | Madison Square Garden |
| 1995-96 | 1996-01-20 | All-Stars East (ASE) 5 at All-Stars West (ASW) 4 | FleetCenter |
| 1996-97 | 1997-01-18 | All-Stars East (ASE) 11 at All-Stars West (ASW) 7 | San Jose Arena |
| 1997-98 | 1998-01-18 | North America All-Stars (N.A) 8 at World All-Stars (WRL) 7 | General Motors Place |
| 1998-99 | 1999-01-24 | North America All-Stars (N.A) 8 at World All-Stars (WRL) 6 | Ice Palace |
| 1999-00 | 2000-02-06 | World All-Stars (WRL) 9 at North America All-Stars (N.A) 4 | Air Canada Centre |
| 2000-01 | 2001-02-04 | North America All-Stars (N.A) 14 at World All-Stars (WRL) 12 | Pepsi Center |
| 2001-02 | 2002-02-02 | World All-Stars (WRL) 8 at North America All-Stars (N.A) 5 | STAPLES Center |
| 2002-03 | 2003-02-02 | All-Stars West (ASW) 6 at All-Stars East (ASE) 5 | Office Depot Center |
| 2003-04 | 2004-02-08 | All-Stars East (ASE) 6 at All-Stars West (ASW) 4 | Xcel Energy Center |
| 2006-07 | 2007-01-24 | All-Stars East (ASE) 9 at All-Stars West (ASW) 12 | American Airlines Center |
| 2007-08 | 2008-01-27 | All-Stars West (ASW) 7 at All-Stars East (ASE) 8 | Philips Arena |
| 2008-09 | 2009-01-25 | All-Stars West (ASW) 11 at All-Stars East (ASE) 12 | Centre Bell |
| 2010-11 | 2011-01-30 | Team Lidstrom (ASB) 11 at Team Staal (ASR) 10 | RBC Center |
| 2011-12 | 2012-01-29 | Tm. Chara Team Chara (BLU) 12 at Tm. Alfredsson Team Alfredsson (RED) 9 | Scotiabank Place |
| 2014-15 | 2015-01-25 | Team Toews (WHT) 17 at Team Foligno (BLK) 12 | Nationwide Arena |
| 2015-16 | 2016-01-31 | Metropolitan (MET) 3 at Atlantic (ATL) 4<br>Pacific (PAC) 9 at Central (CEN) 6<br>Atlantic (ATL) 0 at Pacific (PAC) 1 | Bridgestone Arena |
| 2016-17 | 2017-01-29 | Central (CEN) 3 at Pacific (PAC) 10<br>Metropolitan (MET) 10 at Atlantic (ATL) 6<br>Metropolitan (MET) 4 at Pacific (PAC) 3 | STAPLES Center |
| 2017-18 | 2018-01-28 | Metropolitan (MET) 4 at Atlantic (ATL) 7<br>Central (CEN) 2 at Pacific (PAC) 5<br>Pacific (PAC) 5 at Atlantic (ATL) 2 | Amalie Arena |
| 2018-19 | 2019-01-26 | Central (CEN) 10 at Pacific (PAC) 4<br>Metropolitan (MET) 7 at Atlantic (ATL) 4<br>Metropolitan (MET) 10 at Central (CEN) 5 | SAP Center at San Jose |
| 2021-22 | 2022-02-05 | Metropolitan (MET) 6 at Pacific (PAC) 4<br>Atlantic (ATL) 5 at Central (CEN) 8<br>Central (CEN) 3 at Metropolitan (MET) 5 | T-Mobile Arena |
| 2022-23 | 2023-02-04 | Pacific (PAC) 4 at Central (CEN) 6<br>Metropolitan (MET) 6 at Atlantic (ATL) 10<br>Central (CEN) 5 at Atlantic (ATL) 7 | FLA Live Arena |
| 2023-24 | 2024-02-03 | Team MacKinnon (MKN) 3 at Team McDavid (MCD) 4<br>Team Hughes (HGS) 5 at Team Matthews (MAT) 6<br>Team McDavid (MCD) 4 at Team Matthews (MAT) 7 | Scotiabank Arena |

## Type 6: proposed `world_cup_group` (High (2016-17), Medium (1996-97, 2003-04))

- 12 games each time, between 8 national teams, in late August or September before the NHL season.
- 2016-17 includes Team Europe and Team North America, and every game is at the Air Canada Centre.
- 1996-97 and 2003-04 are spread over venues in Europe and North America.
- My reading: the group stage of the World Cup of Hockey (1996, 2004, 2016). The 2016-17 games are clearly
  that event from the team names alone. For the other two the label leans on general knowledge.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 1996-97 | 12 | 1996-08-26 to 1996-09-03 | Team Canada, Team Czech Republic, Team Finland, Team Germany, Team Russia, Team Slovakia, Team Sweden, Team USA | Centre Molson, CoreStates Center, Corel Centre, General Motors Place, Globe Arena, Madison Square Garden, Olympia-Eissport-Zentrum, Sportovn√≠ hala, Tampereen Jaahalli Arena |
| 2003-04 | 12 | 2004-08-30 to 2004-09-05 | Team Canada, Team Czech Republic, Team Finland, Team Germany, Team Russia, Team Slovakia, Team Sweden, Team USA | Air Canada Centre, Centre Bell, Cologne Arena, Globe Arena, Hartwall Arena, Sazka Arena, Xcel Energy Center |
| 2016-17 | 12 | 2016-09-17 to 2016-09-22 | Team Canada, Team Czech Republic, Team Europe, Team Finland, Team North America, Team Russia, Team Sweden, Team USA | Air Canada Centre |

<details><summary>1996-97: all games</summary>

- 1996-08-26: Team Germany (DEU) 1 at Team Sweden (SWE) 6
- 1996-08-27: Team Finland (FIN) 7 at Team Czech Republic (CZE) 3
- 1996-08-28: Team Germany (DEU) 3 at Team Finland (FIN) 8
- 1996-08-29: Team Sweden (SWE) 3 at Team Czech Republic (CZE) 0
- 1996-08-29: Team Russia (RUS) 3 at Team Canada (CAN) 5
- 1996-08-31: Team Czech Republic (CZE) 1 at Team Germany (DEU) 7
- 1996-08-31: Team Slovakia (SVK) 4 at Team Russia (RUS) 7
- 1996-08-31: Team Canada (CAN) 3 at Team USA (USA) 5
- 1996-09-01: Team Finland (FIN) 2 at Team Sweden (SWE) 5
- 1996-09-01: Team Canada (CAN) 3 at Team Slovakia (SVK) 2
- 1996-09-02: Team Russia (RUS) 2 at Team USA (USA) 5
- 1996-09-03: Team USA (USA) 9 at Team Slovakia (SVK) 3

</details>

<details><summary>2003-04: all games</summary>

- 2004-08-30: Team Czech Republic (CZE) 0 at Team Finland (FIN) 4
- 2004-08-31: Team Germany (DEU) 2 at Team Sweden (SWE) 5
- 2004-08-31: Team USA (USA) 1 at Team Canada (CAN) 2
- 2004-09-01: Team Czech Republic (CZE) 3 at Team Sweden (SWE) 4
- 2004-09-01: Team Canada (CAN) 5 at Team Slovakia (SVK) 1
- 2004-09-02: Team Finland (FIN) 3 at Team Germany (DEU) 0
- 2004-09-02: Team Russia (RUS) 3 at Team USA (USA) 1
- 2004-09-03: Team Germany (DEU) 2 at Team Czech Republic (CZE) 7
- 2004-09-03: Team Slovakia (SVK) 1 at Team USA (USA) 3
- 2004-09-04: Team Sweden (SWE) 4 at Team Finland (FIN) 4
- 2004-09-04: Team Russia (RUS) 1 at Team Canada (CAN) 3
- 2004-09-05: Team Slovakia (SVK) 2 at Team Russia (RUS) 5

</details>

<details><summary>2016-17: all games</summary>

- 2016-09-17: Team USA (USA) 0 at Team Europe (EUR) 3
- 2016-09-17: Team Czech Republic (CZE) 0 at Team Canada (CAN) 6
- 2016-09-18: Team Sweden (SWE) 2 at Team Russia (RUS) 1
- 2016-09-18: Team North America (NAT) 4 at Team Finland (FIN) 1
- 2016-09-19: Team Europe (EUR) 3 at Team Czech Republic (CZE) 2
- 2016-09-19: Team Russia (RUS) 4 at Team North America (NAT) 3
- 2016-09-20: Team Finland (FIN) 0 at Team Sweden (SWE) 2
- 2016-09-20: Team Canada (CAN) 4 at Team USA (USA) 2
- 2016-09-21: Team North America (NAT) 4 at Team Sweden (SWE) 3
- 2016-09-21: Team Europe (EUR) 1 at Team Canada (CAN) 4
- 2016-09-22: Team Finland (FIN) 0 at Team Russia (RUS) 3
- 2016-09-22: Team USA (USA) 3 at Team Czech Republic (CZE) 4

</details>

## Type 7: proposed `world_cup_knockout` (High (2016-17), Medium (1996-97, 2003-04))

- Games directly after the type 6 games, between the same teams.
- 2016-17: 4 games, ending with two Canada v Europe games. 2003-04: 7 games, ending with a single
  Finland at Canada game. 1996-97: 7 games, ending with three Canada v USA games.
- My reading: the knockout rounds of the same World Cups.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 1996-97 | 7 | 1996-09-05 to 1996-09-14 | Team Canada, Team Finland, Team Germany, Team Russia, Team Sweden, Team USA | Centre Molson, CoreStates Center, Corel Centre |
| 2003-04 | 7 | 2004-09-06 to 2004-09-14 | Team Canada, Team Czech Republic, Team Finland, Team Germany, Team Russia, Team Slovakia, Team Sweden, Team USA | Air Canada Centre, Globe Arena, Hartwall Arena, Xcel Energy Center |
| 2016-17 | 4 | 2016-09-24 to 2016-09-29 | Team Canada, Team Europe, Team Russia, Team Sweden | Air Canada Centre |

<details><summary>1996-97: all games</summary>

- 1996-09-05: Team Germany (DEU) 1 at Team Canada (CAN) 4
- 1996-09-06: Team Russia (RUS) 5 at Team Finland (FIN) 0
- 1996-09-07: Team Canada (CAN) 3 at Team Sweden (SWE) 2
- 1996-09-08: Team Russia (RUS) 2 at Team USA (USA) 5
- 1996-09-10: Team Canada (CAN) 4 at Team USA (USA) 3
- 1996-09-12: Team USA (USA) 5 at Team Canada (CAN) 2
- 1996-09-14: Team Canada (CAN) 2 at Team USA (USA) 5

</details>

<details><summary>2003-04: all games</summary>

- 2004-09-06: Team Germany (DEU) 1 at Team Finland (FIN) 2
- 2004-09-07: Team Czech Republic (CZE) 6 at Team Sweden (SWE) 1
- 2004-09-07: Team USA (USA) 5 at Team Russia (RUS) 3
- 2004-09-08: Team Slovakia (SVK) 0 at Team Canada (CAN) 5
- 2004-09-10: Team USA (USA) 1 at Team Finland (FIN) 2
- 2004-09-11: Team Czech Republic (CZE) 3 at Team Canada (CAN) 4
- 2004-09-14: Team Finland (FIN) 2 at Team Canada (CAN) 3

</details>

<details><summary>2016-17: all games</summary>

- 2016-09-24: Team Russia (RUS) 3 at Team Canada (CAN) 5
- 2016-09-25: Team Europe (EUR) 3 at Team Sweden (SWE) 2
- 2016-09-27: Team Europe (EUR) 1 at Team Canada (CAN) 3
- 2016-09-29: Team Canada (CAN) 2 at Team Europe (EUR) 1

</details>

## Type 8: proposed `world_cup_exhibition` (Medium)

- 12 games, 2016-09-08 to 2016-09-14, between the same 8 teams as the 2016-17 type 6 games, at club
  arenas in North America and Europe. Ends three days before the type 6 games start.
- My reading: pre-tournament games before the 2016 World Cup. `world_cup_pretournament` would be an
  equally good name; I kept the name from the plan.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2016-17 | 12 | 2016-09-08 to 2016-09-14 | Team Canada, Team Czech Republic, Team Europe, Team Finland, Team North America, Team Russia, Team Sweden, Team USA | CONSOL Energy Center, Canadian Tire Centre, Centre Bell, Centre Videotron, Hartwall Arena, Nationwide Arena, O2 Czech Republic, Scandinavium, Verizon Center, Yubileyny Arena |

<details><summary>2016-17: all games</summary>

- 2016-09-08: Team Czech Republic (CZE) 3 at Team Russia (RUS) 4
- 2016-09-08: Team Sweden (SWE) 2 at Team Finland (FIN) 3
- 2016-09-08: Team North America (NAT) 4 at Team Europe (EUR) 0
- 2016-09-09: Team Canada (CAN) 2 at Team USA (USA) 4
- 2016-09-10: Team Russia (RUS) 1 at Team Czech Republic (CZE) 2
- 2016-09-10: Team Finland (FIN) 3 at Team Sweden (SWE) 6
- 2016-09-10: Team USA (USA) 2 at Team Canada (CAN) 5
- 2016-09-11: Team Europe (EUR) 4 at Team North America (NAT) 7
- 2016-09-13: Team Finland (FIN) 2 at Team USA (USA) 3
- 2016-09-14: Team Czech Republic (CZE) 3 at Team North America (NAT) 2
- 2016-09-14: Team Russia (RUS) 2 at Team Canada (CAN) 3
- 2016-09-14: Team Sweden (SWE) 2 at Team Europe (EUR) 6

</details>

## Type 9: proposed `olympics` (High)

- Already approved: (2025-26, 9) as `olympics`.
- February every time, 30 to 38 games between 12 to 14 national teams, all in one city per pair:
  Nagano ("The Big Hat", "Aqua Wing Arena") 1998, Salt Lake area ("E center", "Peaks Ice Arena") 2002,
  Turin ("Palasport", "Torino Esposizioni") 2006, Vancouver ("Canada Hockey Place") 2010,
  Sochi ("Bolshoy Ice Dome", "Shayba Arena") 2014.
- The seasons match the Winter Olympic years in which the NHL took part. The city names come from my
  reading of the venue names, not from the data.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 1997-98 | 35 | 1998-02-07 to 1998-02-21 | Austria, Belarus, Canada, Czechia, Finland, France, Germany, Italy, Japan, Kazakhstan, Russia, Slovakia, Sweden, USA | Aqua Wing Arena, The Big Hat |
| 2001-02 | 35 | 2002-02-09 to 2002-02-24 | Austria, Belarus, Canada, Czechia, Finland, France, Germany, Latvia, Russia, Slovakia, Sweden, Switzerland, USA, Ukraine | E center, Peaks Ice Arena |
| 2005-06 | 38 | 2006-02-15 to 2006-02-26 | Canada, Czechia, Finland, Germany, Italy, Kazakhstan, Latvia, Russia, Slovakia, Sweden, Switzerland, USA | Palasport, Torino Esposizioni |
| 2009-10 | 30 | 2010-02-16 to 2010-02-28 | Belarus, Canada, Czechia, Finland, Germany, Latvia, Norway, Russia, Slovakia, Sweden, Switzerland, USA | Canada Hockey Place, Doug Mitchell Thunderbird Sports Centre |
| 2013-14 | 30 | 2014-02-12 to 2014-02-23 | Austria, Canada, Czechia, Finland, Latvia, Norway, Russia, Slovakia, Slovenia, Sweden, Switzerland, USA | Bolshoy Ice Dome, Shayba Arena |

<details><summary>1997-98: all games</summary>

- 1998-02-07: Italy (ITA) 3 at Kazakhstan (KAZ) 5
- 1998-02-07: Austria (AUT) 2 at Slovakia (SVK) 2
- 1998-02-07: Germany (GER) 3 at Japan (JPN) 1
- 1998-02-07: France (FRA) 0 at Belarus (BLR) 4
- 1998-02-08: Austria (AUT) 5 at Kazakhstan (KAZ) 5
- 1998-02-08: Slovakia (SVK) 4 at Italy (ITA) 3
- 1998-02-09: Germany (GER) 2 at Belarus (BLR) 8
- 1998-02-09: Japan (JPN) 2 at France (FRA) 5
- 1998-02-10: Belarus (BLR) 2 at Japan (JPN) 2
- 1998-02-10: Kazakhstan (KAZ) 4 at Slovakia (SVK) 3
- 1998-02-10: Italy (ITA) 5 at Austria (AUT) 2
- 1998-02-10: France (FRA) 0 at Germany (GER) 2
- 1998-02-12: Japan (JPN) 4 at Austria (AUT) 3
- 1998-02-12: France (FRA) 5 at Italy (ITA) 1
- 1998-02-12: Germany (GER) 4 at Slovakia (SVK) 2
- 1998-02-13: USA (USA) 2 at Sweden (SWE) 4
- 1998-02-13: Finland (FIN) 0 at Czechia (CZE) 3
- 1998-02-13: Canada (CAN) 5 at Belarus (BLR) 0
- 1998-02-13: Kazakhstan (KAZ) 2 at Russia (RUS) 9
- 1998-02-14: Belarus (BLR) 2 at USA (USA) 5
- 1998-02-14: Sweden (SWE) 2 at Canada (CAN) 3
- 1998-02-15: Russia (RUS) 4 at Finland (FIN) 3
- 1998-02-15: Czechia (CZE) 8 at Kazakhstan (KAZ) 2
- 1998-02-16: Canada (CAN) 4 at USA (USA) 1
- 1998-02-16: Czechia (CZE) 1 at Russia (RUS) 2
- 1998-02-16: Finland (FIN) 8 at Kazakhstan (KAZ) 2
- 1998-02-16: Sweden (SWE) 5 at Belarus (BLR) 2
- 1998-02-18: Russia (RUS) 4 at Belarus (BLR) 1
- 1998-02-18: Czechia (CZE) 4 at USA (USA) 1
- 1998-02-18: Canada (CAN) 4 at Kazakhstan (KAZ) 1
- 1998-02-18: Sweden (SWE) 1 at Finland (FIN) 2
- 1998-02-20: Canada (CAN) 1 at Czechia (CZE) 2
- 1998-02-20: Russia (RUS) 7 at Finland (FIN) 4
- 1998-02-21: Canada (CAN) 2 at Finland (FIN) 3
- 1998-02-21: Russia (RUS) 0 at Czechia (CZE) 1

</details>

<details><summary>2001-02: all games</summary>

- 2002-02-09: Belarus (BLR) 1 at Ukraine (UKR) 0
- 2002-02-09: Slovakia (SVK) 0 at Germany (GER) 3
- 2002-02-09: Latvia (LAT) 4 at Austria (AUT) 2
- 2002-02-09: France (FRA) 3 at Switzerland (SUI) 3
- 2002-02-10: Germany (GER) 3 at Austria (AUT) 2
- 2002-02-10: Slovakia (SVK) 6 at Latvia (LAT) 6
- 2002-02-11: Switzerland (SUI) 2 at Ukraine (UKR) 5
- 2002-02-11: France (FRA) 1 at Belarus (BLR) 3
- 2002-02-12: Austria (AUT) 3 at Slovakia (SVK) 2
- 2002-02-12: Latvia (LAT) 1 at Germany (GER) 4
- 2002-02-13: Belarus (BLR) 1 at Switzerland (SUI) 2
- 2002-02-13: Ukraine (UKR) 4 at France (FRA) 2
- 2002-02-14: Austria (AUT) 1 at Switzerland (SUI) 4
- 2002-02-14: Latvia (LAT) 9 at Ukraine (UKR) 2
- 2002-02-14: France (FRA) 1 at Slovakia (SVK) 7
- 2002-02-15: Belarus (BLR) 4 at Russia (RUS) 6
- 2002-02-15: Sweden (SWE) 5 at Canada (CAN) 2
- 2002-02-15: Germany (GER) 2 at Czechia (CZE) 8
- 2002-02-15: USA (USA) 6 at Finland (FIN) 0
- 2002-02-16: Belarus (BLR) 1 at Finland (FIN) 8
- 2002-02-16: Russia (RUS) 2 at USA (USA) 2
- 2002-02-17: Czechia (CZE) 1 at Sweden (SWE) 2
- 2002-02-17: Germany (GER) 2 at Canada (CAN) 3
- 2002-02-18: USA (USA) 8 at Belarus (BLR) 1
- 2002-02-18: Finland (FIN) 3 at Russia (RUS) 1
- 2002-02-18: Canada (CAN) 3 at Czechia (CZE) 3
- 2002-02-18: Sweden (SWE) 7 at Germany (GER) 1
- 2002-02-20: Belarus (BLR) 4 at Sweden (SWE) 3
- 2002-02-20: Russia (RUS) 1 at Czechia (CZE) 0
- 2002-02-20: Germany (GER) 0 at USA (USA) 5
- 2002-02-20: Canada (CAN) 2 at Finland (FIN) 1
- 2002-02-22: Belarus (BLR) 1 at Canada (CAN) 7
- 2002-02-22: Russia (RUS) 2 at USA (USA) 3
- 2002-02-23: Russia (RUS) 7 at Belarus (BLR) 2
- 2002-02-24: Canada (CAN) 5 at USA (USA) 2

</details>

<details><summary>2005-06: all games</summary>

- 2006-02-15: Kazakhstan (KAZ) 2 at Sweden (SWE) 7
- 2006-02-15: Canada (CAN) 7 at Italy (ITA) 2
- 2006-02-15: Finland (FIN) 5 at Switzerland (SUI) 0
- 2006-02-15: Czechia (CZE) 4 at Germany (GER) 1
- 2006-02-15: Slovakia (SVK) 5 at Russia (RUS) 3
- 2006-02-15: USA (USA) 3 at Latvia (LAT) 3
- 2006-02-16: Italy (ITA) 0 at Finland (FIN) 6
- 2006-02-16: Switzerland (SUI) 3 at Czechia (CZE) 2
- 2006-02-16: Russia (RUS) 5 at Sweden (SWE) 0
- 2006-02-16: Latvia (LAT) 3 at Slovakia (SVK) 6
- 2006-02-16: Germany (GER) 1 at Canada (CAN) 5
- 2006-02-16: Kazakhstan (KAZ) 1 at USA (USA) 4
- 2006-02-18: Russia (RUS) 1 at Kazakhstan (KAZ) 0
- 2006-02-18: Germany (GER) 3 at Italy (ITA) 3
- 2006-02-18: Switzerland (SUI) 2 at Canada (CAN) 0
- 2006-02-18: Latvia (LAT) 1 at Sweden (SWE) 6
- 2006-02-18: USA (USA) 1 at Slovakia (SVK) 2
- 2006-02-18: Finland (FIN) 4 at Czechia (CZE) 2
- 2006-02-19: Switzerland (SUI) 2 at Germany (GER) 2
- 2006-02-19: Latvia (LAT) 2 at Russia (RUS) 9
- 2006-02-19: Kazakhstan (KAZ) 1 at Slovakia (SVK) 2
- 2006-02-19: Sweden (SWE) 2 at USA (USA) 1
- 2006-02-19: Italy (ITA) 1 at Czechia (CZE) 4
- 2006-02-19: Canada (CAN) 0 at Finland (FIN) 2
- 2006-02-21: Kazakhstan (KAZ) 5 at Latvia (LAT) 2
- 2006-02-21: Italy (ITA) 3 at Switzerland (SUI) 3
- 2006-02-21: Germany (GER) 0 at Finland (FIN) 2
- 2006-02-21: Czechia (CZE) 2 at Canada (CAN) 3
- 2006-02-21: Slovakia (SVK) 3 at Sweden (SWE) 0
- 2006-02-21: Russia (RUS) 5 at USA (USA) 4
- 2006-02-22: Sweden (SWE) 6 at Switzerland (SUI) 2
- 2006-02-22: USA (USA) 3 at Finland (FIN) 4
- 2006-02-22: Canada (CAN) 0 at Russia (RUS) 2
- 2006-02-22: Czechia (CZE) 3 at Slovakia (SVK) 1
- 2006-02-24: Czechia (CZE) 3 at Sweden (SWE) 7
- 2006-02-24: Finland (FIN) 4 at Russia (RUS) 0
- 2006-02-25: Czechia (CZE) 3 at Russia (RUS) 0
- 2006-02-26: Sweden (SWE) 3 at Finland (FIN) 2

</details>

<details><summary>2009-10: all games</summary>

- 2010-02-16: USA (USA) 3 at Switzerland (SUI) 1
- 2010-02-16: Canada (CAN) 8 at Norway (NOR) 0
- 2010-02-16: Russia (RUS) 8 at Latvia (LAT) 2
- 2010-02-17: Finland (FIN) 5 at Belarus (BLR) 1
- 2010-02-17: Sweden (SWE) 2 at Germany (GER) 0
- 2010-02-17: Czechia (CZE) 3 at Slovakia (SVK) 1
- 2010-02-18: USA (USA) 6 at Norway (NOR) 1
- 2010-02-18: Switzerland (SUI) 2 at Canada (CAN) 3
- 2010-02-18: Slovakia (SVK) 2 at Russia (RUS) 1
- 2010-02-19: Belarus (BLR) 2 at Sweden (SWE) 4
- 2010-02-19: Czechia (CZE) 5 at Latvia (LAT) 2
- 2010-02-19: Finland (FIN) 5 at Germany (GER) 0
- 2010-02-20: Norway (NOR) 4 at Switzerland (SUI) 5
- 2010-02-20: Latvia (LAT) 0 at Slovakia (SVK) 6
- 2010-02-20: Germany (GER) 3 at Belarus (BLR) 5
- 2010-02-21: Russia (RUS) 4 at Czechia (CZE) 2
- 2010-02-21: Canada (CAN) 3 at USA (USA) 5
- 2010-02-21: Sweden (SWE) 3 at Finland (FIN) 0
- 2010-02-23: Belarus (BLR) 2 at Switzerland (SUI) 3
- 2010-02-23: Germany (GER) 2 at Canada (CAN) 8
- 2010-02-23: Latvia (LAT) 2 at Czechia (CZE) 3
- 2010-02-23: Norway (NOR) 3 at Slovakia (SVK) 4
- 2010-02-24: Switzerland (SUI) 0 at USA (USA) 2
- 2010-02-24: Canada (CAN) 7 at Russia (RUS) 3
- 2010-02-24: Czechia (CZE) 0 at Finland (FIN) 2
- 2010-02-24: Slovakia (SVK) 4 at Sweden (SWE) 3
- 2010-02-26: Finland (FIN) 1 at USA (USA) 6
- 2010-02-26: Slovakia (SVK) 2 at Canada (CAN) 3
- 2010-02-27: Slovakia (SVK) 3 at Finland (FIN) 5
- 2010-02-28: Canada (CAN) 3 at USA (USA) 2

</details>

<details><summary>2013-14: all games</summary>

- 2014-02-12: Czechia (CZE) 2 at Sweden (SWE) 4
- 2014-02-12: Latvia (LAT) 0 at Switzerland (SUI) 1
- 2014-02-13: Finland (FIN) 8 at Austria (AUT) 4
- 2014-02-13: Russia (RUS) 5 at Slovenia (SLO) 2
- 2014-02-13: Slovakia (SVK) 1 at USA (USA) 7
- 2014-02-13: Canada (CAN) 3 at Norway (NOR) 1
- 2014-02-14: Czechia (CZE) 4 at Latvia (LAT) 2
- 2014-02-14: Sweden (SWE) 1 at Switzerland (SUI) 0
- 2014-02-14: Canada (CAN) 6 at Austria (AUT) 0
- 2014-02-14: Norway (NOR) 1 at Finland (FIN) 6
- 2014-02-15: Slovakia (SVK) 1 at Slovenia (SLO) 3
- 2014-02-15: USA (USA) 3 at Russia (RUS) 2
- 2014-02-15: Switzerland (SUI) 1 at Czechia (CZE) 0
- 2014-02-15: Sweden (SWE) 5 at Latvia (LAT) 3
- 2014-02-16: Austria (AUT) 3 at Norway (NOR) 1
- 2014-02-16: Russia (RUS) 1 at Slovakia (SVK) 0
- 2014-02-16: Slovenia (SLO) 1 at USA (USA) 5
- 2014-02-16: Finland (FIN) 1 at Canada (CAN) 2
- 2014-02-18: Slovenia (SLO) 4 at Austria (AUT) 0
- 2014-02-18: Russia (RUS) 4 at Norway (NOR) 0
- 2014-02-18: Switzerland (SUI) 1 at Latvia (LAT) 3
- 2014-02-18: Czechia (CZE) 5 at Slovakia (SVK) 3
- 2014-02-19: Sweden (SWE) 5 at Slovenia (SLO) 0
- 2014-02-19: Finland (FIN) 3 at Russia (RUS) 1
- 2014-02-19: Canada (CAN) 2 at Latvia (LAT) 1
- 2014-02-19: USA (USA) 5 at Czechia (CZE) 2
- 2014-02-21: Sweden (SWE) 2 at Finland (FIN) 1
- 2014-02-21: USA (USA) 0 at Canada (CAN) 1
- 2014-02-22: USA (USA) 0 at Finland (FIN) 5
- 2014-02-23: Sweden (SWE) 0 at Canada (CAN) 3

</details>

## Type 10: proposed `all_star_youngstars` (High)

- One game each, between "Young Stars East" and "Young Stars West", the day before that season's type 4
  game and at the same venue.
- Only two seasons have this type. I have not looked for why other seasons have none.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2003-04 | 1 | 2004-02-07 to 2004-02-07 | Young Stars East, Young Stars West | Xcel Energy Center |
| 2006-07 | 1 | 2007-01-23 to 2007-01-23 | Young Stars East, Young Stars West | American Airlines Center |

<details><summary>2003-04: all games</summary>

- 2004-02-07: Young Stars East (YSE) 3 at Young Stars West (YSW) 7

</details>

<details><summary>2006-07: all games</summary>

- 2007-01-23: Young Stars East (YSE) 9 at Young Stars West (YSW) 8

</details>

## Type 12: proposed `all_star_womens_game` (Medium)

- Already approved: (2019-20, 12) as `all_star_womens_game`.
- 2023-24: one game, Team King at Team Kloss, at Scotiabank Arena on 2024-02-01, two days before that
  season's type 4 games at the same venue.
- Medium because nothing in the data says these are women's teams. The type number, timing and venue
  match the approved 2019-20 game, and the team names are captains' surnames.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2023-24 | 1 | 2024-02-01 to 2024-02-01 | Team King, Team Kloss | Scotiabank Arena |

<details><summary>2023-24: all games</summary>

- 2024-02-01: Team King (KNG) 5 at Team Kloss (KLS) 3

</details>

## Type 13: proposed `cancelled` (High)

- 1,230 games, all in 2004-05, between the 30 NHL clubs. Every one is 0-0 with no period recorded. The
  weekly schedule has none of them.
- Sourced: the 2004-05 season was cancelled ([Wikipedia: 2004-05 NHL season](https://en.wikipedia.org/wiki/2004%E2%80%9305_NHL_season)), already cited in the approved
  `season_facts_present` exception.
- There are no venues or team names to show, because the weekly schedule has no games for these dates.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2004-05 | 1230 | 2004-10-13 to 2005-04-10 (game list) | 30 NHL clubs (team IDs 1 to 30) | none listed |

## Type 14: proposed `canada_cup` (Medium)

- 17 to 20 games in late August to mid September, between 6 national teams (Canada, USA, Sweden,
  Finland, Czechoslovakia, Soviet Union; West Germany instead of Finland in 1984).
- Mostly Canadian venues, with some in the United States. Each ends with one to three games involving Canada.
- My reading: the Canada Cup (1976, 1981, 1984, 1987, 1991). Unlike the World Cup, round robin and
  knockout share one type here, so one label covers the whole tournament.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 1976-77 | 17 | 1976-09-02 to 1976-09-15 | Canada, Czechoslovakia, Finland, Soviet Union, Sweden, USA | Le Colis√©e, Maple Leaf Gardens, Montreal Forum, Ottawa Civic Centre, Spectrum, Winnipeg Arena |
| 1981-82 | 18 | 1981-09-01 to 1981-09-13 | Canada, Czechoslovakia, Finland, Soviet Union, Sweden, USA | Montreal Forum, Northlands Coliseum, Ottawa Civic Centre, Winnipeg Arena |
| 1984-85 | 19 | 1984-09-01 to 1984-09-18 | Canada, Czechoslovakia, Soviet Union, Sweden, USA, West Germany | Buffalo Memorial Auditorium, Halifax Metro Centre, London Gardens, Montreal Forum, Northlands Coliseum, Olympic Saddledome, Pacific Coliseum |
| 1987-88 | 20 | 1987-08-28 to 1987-09-15 | Canada, Czechoslovakia, Finland, Soviet Union, Sweden, USA | Centre 200, Copps Coliseum, Halifax Metro Centre, Hartford Civic Center, Montreal Forum, Olympic Saddledome, Regina Agridome |
| 1991-92 | 19 | 1991-08-31 to 1991-09-16 | Canada, Czechoslovakia, Finland, Soviet Union, Sweden, USA | Chicago Stadium, Civic Arena, Copps Coliseum, Joe Louis Arena, Le Colis√©e, Maple Leaf Gardens, Montreal Forum, SaskPlace |

<details><summary>1976-77: all games</summary>

- 1976-09-02: Canada (CAN) 11 at Finland (FIN) 2
- 1976-09-03: Sweden (SWE) 5 at USA (USA) 2
- 1976-09-03: Czechoslovakia (TCH) 5 at Soviet Union (URS) 3
- 1976-09-05: Sweden (SWE) 3 at Soviet Union (URS) 3
- 1976-09-05: Czechoslovakia (TCH) 8 at Finland (FIN) 0
- 1976-09-05: Canada (CAN) 4 at USA (USA) 2
- 1976-09-07: Soviet Union (URS) 11 at Finland (FIN) 3
- 1976-09-07: Czechoslovakia (TCH) 4 at USA (USA) 4
- 1976-09-07: Canada (CAN) 4 at Sweden (SWE) 0
- 1976-09-09: Finland (FIN) 8 at Sweden (SWE) 6
- 1976-09-09: Soviet Union (URS) 5 at USA (USA) 0
- 1976-09-09: Czechoslovakia (TCH) 1 at Canada (CAN) 0
- 1976-09-11: USA (USA) 6 at Finland (FIN) 3
- 1976-09-11: Sweden (SWE) 2 at Czechoslovakia (TCH) 1
- 1976-09-11: Canada (CAN) 3 at Soviet Union (URS) 1
- 1976-09-13: Canada (CAN) 6 at Czechoslovakia (TCH) 0
- 1976-09-15: Canada (CAN) 5 at Czechoslovakia (TCH) 4

</details>

<details><summary>1981-82: all games</summary>

- 1981-09-01: Sweden (SWE) 1 at USA (USA) 3
- 1981-09-01: Soviet Union (URS) 1 at Czechoslovakia (TCH) 1
- 1981-09-01: Canada (CAN) 9 at Finland (FIN) 0
- 1981-09-03: Czechoslovakia (TCH) 7 at Finland (FIN) 1
- 1981-09-03: Sweden (SWE) 3 at Soviet Union (URS) 6
- 1981-09-03: Canada (CAN) 8 at USA (USA) 3
- 1981-09-05: Sweden (SWE) 5 at Finland (FIN) 0
- 1981-09-05: Soviet Union (URS) 4 at USA (USA) 1
- 1981-09-05: Canada (CAN) 4 at Czechoslovakia (TCH) 4
- 1981-09-07: Canada (CAN) 4 at Sweden (SWE) 3
- 1981-09-07: Czechoslovakia (TCH) 2 at USA (USA) 6
- 1981-09-07: Soviet Union (URS) 6 at Finland (FIN) 1
- 1981-09-09: Sweden (SWE) 1 at Czechoslovakia (TCH) 7
- 1981-09-09: Finland (FIN) 4 at USA (USA) 4
- 1981-09-09: Canada (CAN) 7 at Soviet Union (URS) 3
- 1981-09-11: Soviet Union (URS) 4 at Czechoslovakia (TCH) 1
- 1981-09-11: USA (USA) 1 at Canada (CAN) 4
- 1981-09-13: Soviet Union (URS) 8 at Canada (CAN) 1

</details>

<details><summary>1984-85: all games</summary>

- 1984-09-01: Canada (CAN) 7 at West Germany (FRG) 2
- 1984-09-01: Sweden (SWE) 1 at USA (USA) 7
- 1984-09-02: Soviet Union (URS) 3 at Czechoslovakia (TCH) 0
- 1984-09-03: Canada (CAN) 4 at USA (USA) 4
- 1984-09-04: Soviet Union (URS) 3 at Sweden (SWE) 2
- 1984-09-04: Czechoslovakia (TCH) 4 at West Germany (FRG) 4
- 1984-09-06: Canada (CAN) 2 at Sweden (SWE) 4
- 1984-09-06: Soviet Union (URS) 8 at West Germany (FRG) 1
- 1984-09-06: Czechoslovakia (TCH) 2 at USA (USA) 3
- 1984-09-08: Canada (CAN) 7 at Czechoslovakia (TCH) 2
- 1984-09-08: Soviet Union (URS) 2 at USA (USA) 1
- 1984-09-08: Sweden (SWE) 4 at West Germany (FRG) 2
- 1984-09-10: Canada (CAN) 3 at Soviet Union (URS) 6
- 1984-09-10: Czechoslovakia (TCH) 2 at Sweden (SWE) 4
- 1984-09-10: West Germany (FRG) 4 at USA (USA) 6
- 1984-09-12: USA (USA) 2 at Sweden (SWE) 9
- 1984-09-13: Soviet Union (URS) 2 at Canada (CAN) 3
- 1984-09-16: Canada (CAN) 5 at Sweden (SWE) 2
- 1984-09-18: Sweden (SWE) 5 at Canada (CAN) 6

</details>

<details><summary>1987-88: all games</summary>

- 1987-08-28: Czechoslovakia (TCH) 4 at Canada (CAN) 4
- 1987-08-28: Finland (FIN) 1 at USA (USA) 4
- 1987-08-29: Sweden (SWE) 5 at Soviet Union (URS) 3
- 1987-08-30: Canada (CAN) 4 at Finland (FIN) 1
- 1987-08-31: Soviet Union (URS) 4 at Czechoslovakia (TCH) 0
- 1987-08-31: USA (USA) 5 at Sweden (SWE) 2
- 1987-09-02: Soviet Union (URS) 7 at Finland (FIN) 4
- 1987-09-02: USA (USA) 2 at Canada (CAN) 3
- 1987-09-02: Sweden (SWE) 4 at Czechoslovakia (TCH) 0
- 1987-09-04: Soviet Union (URS) 5 at USA (USA) 1
- 1987-09-04: Czechoslovakia (TCH) 5 at Finland (FIN) 2
- 1987-09-04: Canada (CAN) 5 at Sweden (SWE) 3
- 1987-09-06: Sweden (SWE) 3 at Finland (FIN) 1
- 1987-09-06: Czechoslovakia (TCH) 3 at USA (USA) 1
- 1987-09-06: Soviet Union (URS) 3 at Canada (CAN) 3
- 1987-09-08: Soviet Union (URS) 4 at Sweden (SWE) 2
- 1987-09-09: Czechoslovakia (TCH) 3 at Canada (CAN) 5
- 1987-09-11: Soviet Union (URS) 6 at Canada (CAN) 5
- 1987-09-13: Canada (CAN) 6 at Soviet Union (URS) 5
- 1987-09-15: Soviet Union (URS) 5 at Canada (CAN) 6

</details>

<details><summary>1991-92: all games</summary>

- 1991-08-31: Czechoslovakia (TCH) 5 at Soviet Union (URS) 2
- 1991-08-31: Sweden (SWE) 3 at USA (USA) 6
- 1991-08-31: Finland (FIN) 2 at Canada (CAN) 2
- 1991-09-02: Finland (FIN) 1 at Czechoslovakia (TCH) 0
- 1991-09-02: Soviet Union (URS) 2 at Sweden (SWE) 3
- 1991-09-02: USA (USA) 3 at Canada (CAN) 6
- 1991-09-05: Soviet Union (URS) 6 at Finland (FIN) 1
- 1991-09-05: Czechoslovakia (TCH) 2 at USA (USA) 4
- 1991-09-05: Sweden (SWE) 1 at Canada (CAN) 4
- 1991-09-07: Sweden (SWE) 1 at Finland (FIN) 3
- 1991-09-07: Soviet Union (URS) 1 at USA (USA) 2
- 1991-09-07: Canada (CAN) 6 at Czechoslovakia (TCH) 2
- 1991-09-09: Czechoslovakia (TCH) 2 at Sweden (SWE) 5
- 1991-09-09: Finland (FIN) 3 at USA (USA) 4
- 1991-09-09: Soviet Union (URS) 3 at Canada (CAN) 3
- 1991-09-11: USA (USA) 7 at Finland (FIN) 3
- 1991-09-12: Sweden (SWE) 0 at Canada (CAN) 4
- 1991-09-14: USA (USA) 1 at Canada (CAN) 4
- 1991-09-16: Canada (CAN) 4 at USA (USA) 2

</details>

## Type 18: proposed `exhibition_tour` (Medium)

- Two NHL clubs playing only each other, after that season's playoffs, at venues outside North America.
- 1937-38: Montréal Canadiens and Detroit Red Wings, 9 games, Empress Hall Earls Court, Palais des Sports
  and Sports Stadium.
- 1958-59: Boston Bruins and New York Rangers, 23 games, across Europe (Wembley Arena, Hallenstadion,
  Wiener Stadthalle and others).
- 1975-76: Washington Capitals and Kansas City Scouts, 4 games, Yoyogi Arena and Makomanai Ice Arena.
- Medium because the name is mine. The data shows post-season games abroad, nothing more.
- These games involve NHL clubs but are not in `fct_games`, which holds types 1, 2 and 3 only.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 1937-38 | 9 | 1938-04-21 to 1938-05-14 | Detroit Red Wings, Montréal Canadiens | Empress Hall, Earls Court, Palais des Sports, Sports Stadium |
| 1958-59 | 23 | 1959-04-29 to 1959-05-24 | Boston Bruins, New York Rangers | Antwerp Sports Hall, Federal Ice Stadium, Grugahalle, Hallenstadion, Patinoire Des Vernets, Rheinlandhalle, Sportpalast, Wembley Arena, Westfalenhalle, Wiener Stadthalle |
| 1975-76 | 4 | 1976-04-14 to 1976-04-18 | Kansas City Scouts, Washington Capitals | Makomanai Ice Arena, Yoyogi Arena |

<details><summary>1937-38: all games</summary>

- 1938-04-21: Detroit Red Wings (DET) 4 at Montréal Canadiens (MTL) 5
- 1938-04-23: Detroit Red Wings (DET) 5 at Montréal Canadiens (MTL) 5
- 1938-04-25: Detroit Red Wings (DET) 8 at Montréal Canadiens (MTL) 10
- 1938-04-27: Montréal Canadiens (MTL) 3 at Detroit Red Wings (DET) 4
- 1938-04-29: Detroit Red Wings (DET) 5 at Montréal Canadiens (MTL) 7
- 1938-05-05: Detroit Red Wings (DET) 3 at Montréal Canadiens (MTL) 6
- 1938-05-07: Montréal Canadiens (MTL) 5 at Detroit Red Wings (DET) 10
- 1938-05-10: Detroit Red Wings (DET) 4 at Montréal Canadiens (MTL) 5
- 1938-05-14: Montréal Canadiens (MTL) 2 at Detroit Red Wings (DET) 5

</details>

<details><summary>1958-59: all games</summary>

- 1959-04-29: New York Rangers (NYR) 5 at Boston Bruins (BOS) 7
- 1959-04-30: Boston Bruins (BOS) 3 at New York Rangers (NYR) 4
- 1959-05-02: Boston Bruins (BOS) 3 at New York Rangers (NYR) 4
- 1959-05-03: New York Rangers (NYR) 4 at Boston Bruins (BOS) 12
- 1959-05-04: Boston Bruins (BOS) 2 at New York Rangers (NYR) 6
- 1959-05-05: New York Rangers (NYR) 4 at Boston Bruins (BOS) 6
- 1959-05-06: New York Rangers (NYR) 3 at Boston Bruins (BOS) 6
- 1959-05-07: Boston Bruins (BOS) 3 at New York Rangers (NYR) 6
- 1959-05-08: Boston Bruins (BOS) 4 at New York Rangers (NYR) 8
- 1959-05-09: Boston Bruins (BOS) 6 at New York Rangers (NYR) 7
- 1959-05-10: New York Rangers (NYR) 2 at Boston Bruins (BOS) 4
- 1959-05-12: Boston Bruins (BOS) 2 at New York Rangers (NYR) 4
- 1959-05-13: New York Rangers (NYR) 4 at Boston Bruins (BOS) 6
- 1959-05-14: New York Rangers (NYR) 4 at Boston Bruins (BOS) 6
- 1959-05-15: Boston Bruins (BOS) 3 at New York Rangers (NYR) 4
- 1959-05-16: Boston Bruins (BOS) 0 at New York Rangers (NYR) 8
- 1959-05-17: Boston Bruins (BOS) 2 at New York Rangers (NYR) 7
- 1959-05-19: Boston Bruins (BOS) 6 at New York Rangers (NYR) 6
- 1959-05-20: Boston Bruins (BOS) 2 at New York Rangers (NYR) 3
- 1959-05-21: New York Rangers (NYR) 2 at Boston Bruins (BOS) 8
- 1959-05-22: New York Rangers (NYR) 2 at Boston Bruins (BOS) 2
- 1959-05-23: New York Rangers (NYR) 3 at Boston Bruins (BOS) 5
- 1959-05-24: New York Rangers (NYR) 4 at Boston Bruins (BOS) 4

</details>

<details><summary>1975-76: all games</summary>

- 1976-04-14: Kansas City Scouts (KCS) 2 at Washington Capitals (WSH) 5
- 1976-04-15: Kansas City Scouts (KCS) 2 at Washington Capitals (WSH) 6
- 1976-04-17: Kansas City Scouts (KCS) 2 at Washington Capitals (WSH) 6
- 1976-04-18: Washington Capitals (WSH) 2 at Kansas City Scouts (KCS) 4

</details>

## Type 19: proposed `four_nations_round_robin` (High)

- 6 games, 2025-02-12 to 2025-02-17, between Canada, USA, Sweden and Finland, at Centre Bell and TD
  Garden. Each team plays the other three once.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2024-25 | 6 | 2025-02-12 to 2025-02-17 | Canada, Finland, Sweden, USA | Centre Bell, TD Garden |

<details><summary>2024-25: all games</summary>

- 2025-02-12: Canada (CAN) 4 at Sweden (SWE) 3
- 2025-02-13: USA (USA) 6 at Finland (FIN) 1
- 2025-02-15: Finland (FIN) 4 at Sweden (SWE) 3
- 2025-02-15: USA (USA) 3 at Canada (CAN) 1
- 2025-02-17: Canada (CAN) 5 at Finland (FIN) 3
- 2025-02-17: Sweden (SWE) 2 at USA (USA) 1

</details>

## Type 20: proposed `four_nations_final` (High)

- 1 game, 2025-02-20, Canada at USA (won by Canada in overtime), at TD Garden, three days after the type 19 games.

| Season | Games | Dates | Teams | Venues |
|---|---|---|---|---|
| 2024-25 | 1 | 2025-02-20 to 2025-02-20 | Canada, USA | TD Garden |

<details><summary>2024-25: all games</summary>

- 2025-02-20: Canada (CAN) 3 at USA (USA) 2

</details>
