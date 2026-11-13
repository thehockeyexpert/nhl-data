# Golden questions: reference answers

Reference answers for `analyst/golden_questions.yml`, worked out by direct SQL against MotherDuck on 2026-11-13
(data through 2026-11-11), to check the conversational query layer against. Facts and figures only.

Rules applied unless a question says otherwise: regular season (D11); teams grouped by `lineage_id` (D03); "most
goals/assists/points" include goalies (D15); single seasons are finished seasons (to 2025-26); careers and
"right now" answers run to 2026-11-11, so they move. Records are W-L-T-OTL. A blind run should match the figures;
for the moving ones, the method and the leader matter more than the exact number.

## Team
- **T01** Toronto 2025-26: 32 W, 36 L, 14 OTL (78 points, 82 games).
- **T02** Edmonton 1983-84, 446 goals in 80 games (5.58 a game); Edmonton holds the next three too (426, 424, 417).
- **T03** Boston 2025-26: home 29 W, 11 L, 1 OTL; road 16 W, 16 L, 9 OTL.
- **T04** One-goal games since 2005-06 (D07: overtime wins in, shootout games out), by win %: New Jersey .549 (306 W,
  168 L, 83 OTL in 557), Nashville .546, Vegas .544, Washington .532.
- **T05** Shots per game 2025-26: Colorado 33.7, Carolina 32.2, Anaheim 30.8.
- **T06** Not answerable: team power-play percentage needs team game statistics, which are not loaded.
- **T07** Bench minors since 1990-91: Colorado lineage (with Quebec) 334 in 2,783 games (0.120 a game), Chicago 307,
  Vancouver 306. Per game Colorado also leads (Utah 0.115 in 183 games). From the play-by-play penalties (code BEN).
- **T08** Partly answerable: by regulation minutes (60 a game, regular season and playoffs) Montreal 481,200 (8,020
  games), Toronto 469,020, Boston 465,720. Overtime minutes (D19) need overtime rules by era, not built yet.
- **T09** Travel (D20, regular season): most in one season Vancouver 1975-76, 116,152 km (then Vancouver 1971-72 and
  California 1974-75). 2025-26: Dallas 81,671 km most, NY Islanders 46,603 least. 3 games (Atlantic City, 1929-30)
  have no arena coordinates.
- **T10** Travel in history (finished seasons): Chicago 5,135,341 km in 99 seasons, Los Angeles 4,753,491 in 58,
  Detroit 4,724,587. Per season (10 seasons or more): Cleveland Barons lineage (California Golden Seals) 92,740 km,
  Vancouver 82,503, Los Angeles 81,957.
- **T11** Most playoff games: Montreal 805, Boston 708, Detroit 622.

## Season
- **SE01** 1995-96: Detroit 131 points (62 W, 13 L, 7 T); Colorado 104.
- **SE02** On 2026-01-01 Montreal was 3rd in the Atlantic: 50 points in 40 games, behind Detroit 52 (42) and Tampa Bay
  51 (40). Standings by points through that date; tie-breakers not applied.
- **SE03** Biggest points lead: Detroit 1995-96, 27 points (end of season, 1996-04-14); Boston 1929-30, 26.
- **SE04** Last-place points, 1967-68 to 2025-26: lowest Washington 21 (1974-75, 80 games); highest Los Angeles 71
  (2007-08); 2025-26 Vancouver 58.
- **SE05** Most games decided in overtime or a shootout (ties excluded): by count 2025-26, 326 of 1,312; by share
  2013-14, 25.0% (307 of 1,230).

## History
- **H01** Goals per game (both teams): highest 1919-20, 9.58; lowest 1928-29, 2.92; 2025-26 6.25.
- **H02** Most ties: 2003-04, 170.
- **H03** 21 goals: Montreal 14, Toronto St. Patricks 7 (1920-01-10) and Edmonton 12, Chicago 9 (1985-12-11).
  Playoffs: Los Angeles 10, Edmonton 8 (1982-04-07), 18.
- **H04** Shootouts per season since 2005-06: most 184 (2009-10); fewest 65 (2020-21, a 56-game season), 77 in an
  82-game season (2024-25); 2025-26 119; 2,626 in all to date.

## Franchise
- **F01** Montreal v every opponent (lineage): most played Toronto 778 games, 372 W, 304 L, 88 T, 14 OTL; Boston 768,
  367-286-103-12. Montreal has more wins than losses against every lineage except St. Louis Eagles (52 W, 55 L),
  Minnesota (10 W, 21 L) and San Jose (20 W, 25 L), and is level with Anaheim (20 W, 20 L).
- **F02** Most playoff series won: Montreal 98, Detroit 68, Boston 64, Toronto 60 (same by franchise_id).
- **F03** Longest playoff drought: Buffalo 14 seasons (2011-12 to 2024-25); Detroit 10 and current (2016-17 to
  2025-26); Florida and Edmonton 10.
- **F04** Coyotes lineage: Winnipeg 1979-80 to 1995-96, 506 W, 660 L, 172 T (.442 points %), playoffs in 11 of 17
  seasons, 2 series won; Phoenix/Arizona 1996-97 to 2023-24, 918 W, 939 L, 94 T, 191 OTL (.495), playoffs in 9 of
  27, 3 series won.

## Player
- **P01** 2025-26 goals: Nathan MacKinnon 53, Cole Caufield 51, Connor McDavid 48.
- **P02** Most points in a game: Darryl Sittler 10 (6 G, 4 A, 1976-02-07). Playoffs: 8, Patrik Sundstrom (1988) and
  Mario Lemieux (1989).
- **P03** Most career points against Boston: Gordie Howe 349 (148 goals, 317 games).
- **P04** Connor McDavid: 814 games, 1,269 points, 1.559 a game (3rd all time at 400 games or more, after Gretzky
  1.921 and Lemieux 1.883).
- **P05** Defencemen ice time 2025-26 (41 games or more): Quinn Hughes 27:44, Zach Werenski 26:37, Moritz Seider
  25:40.
- **P06** Swedish-born goals: Mats Sundin 564, Daniel Alfredsson 444, Markus Naslund 395, Daniel Sedin 393.
- **P07** Rookie seasons (D09, NHL games only): Gretzky 137 (1979-80) and Mike Rogers 105 (1979-80) qualify on NHL
  games but came from the WHA, so not rookies under the NHL rule. Then Teemu Selanne 132 (1992-93), Peter Stastny
  109 (1980-81), Alex Ovechkin 106 (2005-06), Dale Hawerchuk 103 (1981-82).
- **P08** First-overall picks, career points: Sidney Crosby 1,774, Mario Lemieux 1,723, Alex Ovechkin 1,692.
- **P09** 5 or more assists in a game: 218 times by 154 players; Gretzky 17, Lemieux 8, Pat LaFontaine 4.
- **P10** 3 or more goals in a game: 5,398 times by 1,551 players; Gretzky 50, Lemieux 40, Mike Bossy 39.
- **P11** Minnesota-born: Phil Housley 1,232 points, Blake Wheeler 943, Neal Broten 923.
- **P12** Birth city: Toronto 452 NHL players, Montréal 273, Edmonton 213, Winnipeg 204.
- **P13** Ontario-born players 317,666 points, Quebec 116,340, Alberta 67,945.
- **P14** Boston College alumni, NHL fighting majors (D17): Bill Guerin 83, Bob Sweeney 37, Brian Boyle 30.
- **P15** Best CHL season v best NHL season (D18; each player's best single page entry, since a page can list a
  traded player's season twice): CHL higher, Jacques Cossette 214 (QMJHL 1973-74) v 9 (NHL), gap 205; NHL higher,
  Troy Murray 99 v 2, gap 97 (then Glenn Anderson 105 v 10, Nikita Kucherov 144 v 53).
- **P16** Most recent with more playoff than regular-season goals (20 games or more): Jordan Greenway 2025-26 (1 and
  2) and Brett Howden 2025-26 (12 and 14).
- **P17** Skater regular-season goals by shooting side: left 61.7%, right 37.9%; assists 63.7% and 35.8%; points
  62.9% and 36.6% (0.4% unknown side).
- **P18** 1 to 10 games, all since 1997-98: Jeff Libby, 43 seconds in 1 game.
- **P19** Fighting majors plus points: Gretzky 2,860 (3 + 2,857), Mark Messier 1,937 (50 + 1,887); points dominate.
- **P20** Most goals in a game: Joe Malone 7 (1920-01-31). Playoffs: Newsy Lalonde 5 (1919-03-01).
- **P21** Gretzky 1995-96: Los Angeles 62 games, 15 G, 66 A, 81 points; St. Louis 18 games, 8 G, 13 A, 21 points.

## Goalie
- **G01** (draft table) Top half, 50 decisions or more: Ilya Samsonov .653 (47 W, 19 L, 0 T, 6 OTL); 100 or more:
  Braden Holtby .600 (126-63-0-21). Literal above .500: Pyotr Kochetkov .631 (84 decisions).
- **G02** Shutouts in a season: George Hainsworth 22 (1928-29).
- **G03** Save % 2025-26 (28 games or more): Scott Wedgewood .921, Jesper Wallstedt .916, Andrei Vasilevskiy .912.
- **G04** Second night of a back-to-back (D08), 2010-11 to 2025-26: win % .447 and save % .909 in 6,387
  decisions, against .511 and .911 otherwise. Best (50 decisions or more): Corey Crawford .618, Marc-Andre Fleury .574.
- **G05** Playoff wins: Patrick Roy 151, Martin Brodeur 113, Marc-Andre Fleury 92.
- **G06** Winning record (D13), 50 games or more, highest GAA: Jiri Crha 3.98 (28 W, 27 L or OTL), Doug Soetaert 3.97.
- **G07** Goalies by birth country: Canada 567, USA 126, Finland 43, Sweden 43; by NHL nationality Canada 567, USA 126,
  Sweden 43, Finland 42.
- **G08** Goalie goals: Martin Brodeur 3 (2 regular season, 1 playoffs), Ron Hextall 2.

## Head to head
- **X01** Rangers v Islanders: regular season 302 games, Rangers 143 W, 130 L, 19 T, 10 OTL; playoffs 39 games,
  Islanders 20-19.
- **X02** Goals in Montreal v Toronto games: Maurice Richard 108, Jean Beliveau 74, Henri Richard 68.
- **X03** Most overtime or shootout games since 2005-06: Anaheim v Los Angeles 34.

## Streaks
- **K01** Longest winning streak (within a season): Pittsburgh 17 (1992-93), Columbus 16 (2016-17), Edmonton 16
  (2023-24).
- **K02** Home unbeaten (W or T; no regulation loss gives the same): Montreal 34 within 1976-77 (1976-11-01 to
  1977-04-02), 37 counting into 1977-78 (to 1977-10-24); then Boston 27 (1970-71).
- **K03** Point streak: Gretzky 51 (1983-84), Lemieux 46 (1989-90).

## Current (as of 2026-11-11)
- **C01** Points: Connor McDavid 49 in 20 games, Leon Draisaitl 37, Evan Bouchard 33.
- **C02** Toronto's last 10: 4 W, 6 L, 0 OTL.
- **C03** Last 14 days, 4 games or more, save %: Juuse Saros .947, Jesper Wallstedt .931.
- **C04** Wild cards (points, ties by points %; NHL tie-breakers not applied): East Ottawa 24 and Florida 22 (then
  Washington 20); West Dallas 22 and Utah 21 (then Seattle 19).

## Awards
- **A01** Hart Trophy: Wayne Gretzky 9, Gordie Howe 6, Eddie Shore 4.
- **A02** Vezina winners whose team won the Cup that season: 34 of 113 Vezina wins (shared before 1982), most
  recently Tim Thomas 2011 and Martin Brodeur 2003.
