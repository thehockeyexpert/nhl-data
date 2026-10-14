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
- **Trimmed (2026-10-14):** each pair is one summary line (games, dates, venues). Per-game lists and scores were
  removed, so the public repo carries facts and figures only (see `docs/decisions.md`).
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

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1947-48 | 1 | 1947-10-13 | Maple Leaf Gardens |
| 1948-49 | 1 | 1948-11-03 | Chicago Stadium |
| 1949-50 | 1 | 1949-10-10 | Maple Leaf Gardens |
| 1950-51 | 1 | 1950-10-08 | Detroit Olympia |
| 1951-52 | 1 | 1951-10-09 | Maple Leaf Gardens |
| 1952-53 | 1 | 1952-10-05 | Detroit Olympia |
| 1953-54 | 1 | 1953-10-03 | Montreal Forum |
| 1954-55 | 1 | 1954-10-02 | Detroit Olympia |
| 1955-56 | 1 | 1955-10-02 | Detroit Olympia |
| 1956-57 | 1 | 1956-10-09 | Montreal Forum |
| 1957-58 | 1 | 1957-10-05 | Montreal Forum |
| 1958-59 | 1 | 1958-10-04 | Montreal Forum |
| 1959-60 | 1 | 1959-10-03 | Montreal Forum |
| 1960-61 | 1 | 1960-10-01 | Montreal Forum |
| 1961-62 | 1 | 1961-10-07 | Chicago Stadium |
| 1962-63 | 1 | 1962-10-06 | Maple Leaf Gardens |
| 1963-64 | 1 | 1963-10-05 | Maple Leaf Gardens |
| 1964-65 | 1 | 1964-10-10 | Maple Leaf Gardens |
| 1965-66 | 1 | 1965-10-20 | Montreal Forum |
| 1966-67 | 1 | 1967-01-18 | Montreal Forum |
| 1968-69 | 1 | 1969-01-21 | Montreal Forum |
| 1969-70 | 1 | 1970-01-20 | St. Louis Arena |
| 1970-71 | 1 | 1971-01-19 | Boston Garden |
| 1971-72 | 1 | 1972-01-25 | Metropolitan Sports Center |
| 1972-73 | 1 | 1973-01-30 | Madison Square Garden |
| 1973-74 | 1 | 1974-01-29 | Chicago Stadium |
| 1974-75 | 1 | 1975-01-21 | Montreal Forum |
| 1975-76 | 1 | 1976-01-20 | Spectrum |
| 1976-77 | 1 | 1977-01-25 | Pacific Coliseum |
| 1977-78 | 1 | 1978-01-24 | Buffalo Memorial Auditorium |
| 1979-80 | 1 | 1980-02-05 | Joe Louis Arena |
| 1980-81 | 1 | 1981-02-10 | The Forum |
| 1981-82 | 1 | 1982-02-09 | Capital Centre |
| 1982-83 | 1 | 1983-02-08 | Nassau Veterans Memorial Coliseum |
| 1983-84 | 1 | 1984-01-31 | Brendan Byrne Arena |
| 1984-85 | 1 | 1985-02-12 | Olympic Saddledome |
| 1985-86 | 1 | 1986-02-04 | Hartford Civic Center |
| 1987-88 | 1 | 1988-02-09 | St. Louis Arena |
| 1988-89 | 1 | 1989-02-07 | Northlands Coliseum |
| 1989-90 | 1 | 1990-01-21 | Civic Arena |
| 1990-91 | 1 | 1991-01-19 | Chicago Stadium |
| 1991-92 | 1 | 1992-01-18 | Spectrum |
| 1992-93 | 1 | 1993-02-06 | Montreal Forum |
| 1993-94 | 1 | 1994-01-22 | Madison Square Garden |
| 1995-96 | 1 | 1996-01-20 | FleetCenter |
| 1996-97 | 1 | 1997-01-18 | San Jose Arena |
| 1997-98 | 1 | 1998-01-18 | General Motors Place |
| 1998-99 | 1 | 1999-01-24 | Ice Palace |
| 1999-00 | 1 | 2000-02-06 | Air Canada Centre |
| 2000-01 | 1 | 2001-02-04 | Pepsi Center |
| 2001-02 | 1 | 2002-02-02 | STAPLES Center |
| 2002-03 | 1 | 2003-02-02 | Office Depot Center |
| 2003-04 | 1 | 2004-02-08 | Xcel Energy Center |
| 2006-07 | 1 | 2007-01-24 | American Airlines Center |
| 2007-08 | 1 | 2008-01-27 | Philips Arena |
| 2008-09 | 1 | 2009-01-25 | Centre Bell |
| 2010-11 | 1 | 2011-01-30 | RBC Center |
| 2011-12 | 1 | 2012-01-29 | Scotiabank Place |
| 2014-15 | 1 | 2015-01-25 | Nationwide Arena |
| 2015-16 | 3 | 2016-01-31 | Bridgestone Arena |
| 2016-17 | 3 | 2017-01-29 | STAPLES Center |
| 2017-18 | 3 | 2018-01-28 | Amalie Arena |
| 2018-19 | 3 | 2019-01-26 | SAP Center at San Jose |
| 2021-22 | 3 | 2022-02-05 | T-Mobile Arena |
| 2022-23 | 3 | 2023-02-04 | FLA Live Arena |
| 2023-24 | 3 | 2024-02-03 | Scotiabank Arena |

## Type 6: proposed `world_cup_group` (High (2016-17), Medium (1996-97, 2003-04))

- 12 games each time, between 8 national teams, in late August or September before the NHL season.
- 2016-17 includes Team Europe and Team North America, and every game is at the Air Canada Centre.
- 1996-97 and 2003-04 are spread over venues in Europe and North America.
- My reading: the group stage of the World Cup of Hockey (1996, 2004, 2016). The 2016-17 games are clearly
  that event from the team names alone. For the other two the label leans on general knowledge.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1996-97 | 12 | 1996-08-26 to 1996-09-03 | Centre Molson, CoreStates Center, Corel Centre, General Motors Place, Globe Arena, Madison Square Garden, Olympia-Eissport-Zentrum, Sportovn√≠ hala, Tampereen Jaahalli Arena |
| 2003-04 | 12 | 2004-08-30 to 2004-09-05 | Air Canada Centre, Centre Bell, Cologne Arena, Globe Arena, Hartwall Arena, Sazka Arena, Xcel Energy Center |
| 2016-17 | 12 | 2016-09-17 to 2016-09-22 | Air Canada Centre |

## Type 7: proposed `world_cup_knockout` (High (2016-17), Medium (1996-97, 2003-04))

- Games directly after the type 6 games, between the same teams.
- 2016-17: 4 games, ending with two Canada v Europe games. 2003-04: 7 games, ending with a single
  Finland at Canada game. 1996-97: 7 games, ending with three Canada v USA games.
- My reading: the knockout rounds of the same World Cups.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1996-97 | 7 | 1996-09-05 to 1996-09-14 | Centre Molson, CoreStates Center, Corel Centre |
| 2003-04 | 7 | 2004-09-06 to 2004-09-14 | Air Canada Centre, Globe Arena, Hartwall Arena, Xcel Energy Center |
| 2016-17 | 4 | 2016-09-24 to 2016-09-29 | Air Canada Centre |

## Type 8: proposed `world_cup_exhibition` (Medium)

- 12 games, 2016-09-08 to 2016-09-14, between the same 8 teams as the 2016-17 type 6 games, at club
  arenas in North America and Europe. Ends three days before the type 6 games start.
- My reading: pre-tournament games before the 2016 World Cup. `world_cup_pretournament` would be an
  equally good name; I kept the name from the plan.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2016-17 | 12 | 2016-09-08 to 2016-09-14 | CONSOL Energy Center, Canadian Tire Centre, Centre Bell, Centre Videotron, Hartwall Arena, Nationwide Arena, O2 Czech Republic, Scandinavium, Verizon Center, Yubileyny Arena |

## Type 9: proposed `olympics` (High)

- Already approved: (2025-26, 9) as `olympics`.
- February every time, 30 to 38 games between 12 to 14 national teams, all in one city per pair:
  Nagano ("The Big Hat", "Aqua Wing Arena") 1998, Salt Lake area ("E center", "Peaks Ice Arena") 2002,
  Turin ("Palasport", "Torino Esposizioni") 2006, Vancouver ("Canada Hockey Place") 2010,
  Sochi ("Bolshoy Ice Dome", "Shayba Arena") 2014.
- The seasons match the Winter Olympic years in which the NHL took part. The city names come from my
  reading of the venue names, not from the data.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1997-98 | 35 | 1998-02-07 to 1998-02-21 | Aqua Wing Arena, The Big Hat |
| 2001-02 | 35 | 2002-02-09 to 2002-02-24 | E center, Peaks Ice Arena |
| 2005-06 | 38 | 2006-02-15 to 2006-02-26 | Palasport, Torino Esposizioni |
| 2009-10 | 30 | 2010-02-16 to 2010-02-28 | Canada Hockey Place, Doug Mitchell Thunderbird Sports Centre |
| 2013-14 | 30 | 2014-02-12 to 2014-02-23 | Bolshoy Ice Dome, Shayba Arena |

## Type 10: proposed `all_star_youngstars` (High)

- One game each, between "Young Stars East" and "Young Stars West", the day before that season's type 4
  game and at the same venue.
- Only two seasons have this type. I have not looked for why other seasons have none.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2003-04 | 1 | 2004-02-07 | Xcel Energy Center |
| 2006-07 | 1 | 2007-01-23 | American Airlines Center |

## Type 12: proposed `all_star_womens_game` (Medium)

- Already approved: (2019-20, 12) as `all_star_womens_game`.
- 2023-24: one game, Team King at Team Kloss, at Scotiabank Arena on 2024-02-01, two days before that
  season's type 4 games at the same venue.
- Medium because nothing in the data says these are women's teams. The type number, timing and venue
  match the approved 2019-20 game, and the team names are captains' surnames.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2023-24 | 1 | 2024-02-01 | Scotiabank Arena |

## Type 13: proposed `cancelled` (High)

- 1,230 games, all in 2004-05, between the 30 NHL clubs. Every one is 0-0 with no period recorded. The
  weekly schedule has none of them.
- Sourced: the 2004-05 season was cancelled ([Wikipedia: 2004-05 NHL season](https://en.wikipedia.org/wiki/2004%E2%80%9305_NHL_season)), already cited in the approved
  `season_facts_present` exception.
- There are no venues or team names to show, because the weekly schedule has no games for these dates.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2004-05 | 1,230 | 2004-10-13 to 2005-04-10 (game list) | none listed |

## Type 14: proposed `canada_cup` (Medium)

- 17 to 20 games in late August to mid September, between 6 national teams (Canada, USA, Sweden,
  Finland, Czechoslovakia, Soviet Union; West Germany instead of Finland in 1984).
- Mostly Canadian venues, with some in the United States. Each ends with one to three games involving Canada.
- My reading: the Canada Cup (1976, 1981, 1984, 1987, 1991). Unlike the World Cup, round robin and
  knockout share one type here, so one label covers the whole tournament.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1976-77 | 17 | 1976-09-02 to 1976-09-15 | Le Colis√©e, Maple Leaf Gardens, Montreal Forum, Ottawa Civic Centre, Spectrum, Winnipeg Arena |
| 1981-82 | 18 | 1981-09-01 to 1981-09-13 | Montreal Forum, Northlands Coliseum, Ottawa Civic Centre, Winnipeg Arena |
| 1984-85 | 19 | 1984-09-01 to 1984-09-18 | Buffalo Memorial Auditorium, Halifax Metro Centre, London Gardens, Montreal Forum, Northlands Coliseum, Olympic Saddledome, Pacific Coliseum |
| 1987-88 | 20 | 1987-08-28 to 1987-09-15 | Centre 200, Copps Coliseum, Halifax Metro Centre, Hartford Civic Center, Montreal Forum, Olympic Saddledome, Regina Agridome |
| 1991-92 | 19 | 1991-08-31 to 1991-09-16 | Chicago Stadium, Civic Arena, Copps Coliseum, Joe Louis Arena, Le Colis√©e, Maple Leaf Gardens, Montreal Forum, SaskPlace |

## Type 18: proposed `exhibition_tour` (Medium)

- Two NHL clubs playing only each other, after that season's playoffs, at venues outside North America.
- 1937-38: Montréal Canadiens and Detroit Red Wings, 9 games, Empress Hall Earls Court, Palais des Sports
  and Sports Stadium.
- 1958-59: Boston Bruins and New York Rangers, 23 games, across Europe (Wembley Arena, Hallenstadion,
  Wiener Stadthalle and others).
- 1975-76: Washington Capitals and Kansas City Scouts, 4 games, Yoyogi Arena and Makomanai Ice Arena.
- Medium because the name is mine. The data shows post-season games abroad, nothing more.
- These games involve NHL clubs but are not in `fct_games`, which holds types 1, 2 and 3 only.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 1937-38 | 9 | 1938-04-21 to 1938-05-14 | Empress Hall, Earls Court, Palais des Sports, Sports Stadium |
| 1958-59 | 23 | 1959-04-29 to 1959-05-24 | Antwerp Sports Hall, Federal Ice Stadium, Grugahalle, Hallenstadion, Patinoire Des Vernets, Rheinlandhalle, Sportpalast, Wembley Arena, Westfalenhalle, Wiener Stadthalle |
| 1975-76 | 4 | 1976-04-14 to 1976-04-18 | Makomanai Ice Arena, Yoyogi Arena |

## Type 19: proposed `four_nations_round_robin` (High)

- 6 games, 2025-02-12 to 2025-02-17, between Canada, USA, Sweden and Finland, at Centre Bell and TD
  Garden. Each team plays the other three once.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2024-25 | 6 | 2025-02-12 to 2025-02-17 | Centre Bell, TD Garden |

## Type 20: proposed `four_nations_final` (High)

- 1 game, 2025-02-20, Canada at USA, at TD Garden, three days after the type 19 games.

| Season | Games | Dates | Venues |
|---|---|---|---|
| 2024-25 | 1 | 2025-02-20 | TD Garden |
