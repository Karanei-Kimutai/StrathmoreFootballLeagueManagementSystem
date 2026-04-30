from collections import defaultdict


def generate_single_round_robin(team_ids):
    """Return rounds of (home_team_id, away_team_id) using the circle method."""
    teams = list(team_ids)
    if len(teams) < 2:
        return []

    if len(teams) % 2:
        teams.append(None)

    rounds = []
    team_count = len(teams)
    for round_index in range(team_count - 1):
        pairings = []
        for index in range(team_count // 2):
            home = teams[index]
            away = teams[team_count - 1 - index]
            if home is None or away is None:
                continue
            if round_index % 2:
                home, away = away, home
            pairings.append((home, away))
        rounds.append(pairings)
        teams = [teams[0], teams[-1], *teams[1:-1]]

    return rounds


def calculate_league_standings(teams, matches, league):
    table = {
        team[0]: {
            "team_id": team[0],
            "team_name": team[1],
            "crest_url": team[2],
            "played": 0,
            "won": 0,
            "draw": 0,
            "lost": 0,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
            "form_results": [],
        }
        for team in teams
    }
    head_to_head = defaultdict(lambda: defaultdict(lambda: {"points": 0, "gf": 0, "ga": 0, "gd": 0}))

    for match in matches:
        match_id, utc_date, home_id, away_id, home_goals, away_goals = match
        if home_id not in table or away_id not in table or home_goals is None or away_goals is None:
            continue

        home = table[home_id]
        away = table[away_id]
        home["played"] += 1
        away["played"] += 1
        home["gf"] += home_goals
        home["ga"] += away_goals
        away["gf"] += away_goals
        away["ga"] += home_goals

        h2h_home = head_to_head[home_id][away_id]
        h2h_away = head_to_head[away_id][home_id]
        h2h_home["gf"] += home_goals
        h2h_home["ga"] += away_goals
        h2h_away["gf"] += away_goals
        h2h_away["ga"] += home_goals

        if home_goals > away_goals:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
            h2h_home["points"] += 3
            result = ("W", "L")
        elif home_goals < away_goals:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
            h2h_away["points"] += 3
            result = ("L", "W")
        else:
            home["draw"] += 1
            away["draw"] += 1
            home["points"] += 1
            away["points"] += 1
            h2h_home["points"] += 1
            h2h_away["points"] += 1
            result = ("D", "D")

        home["form_results"].append((utc_date, match_id, result[0]))
        away["form_results"].append((utc_date, match_id, result[1]))

    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
        row["form"] = [
            item[2]
            for item in sorted(row["form_results"], key=lambda item: (item[0], item[1]), reverse=True)[:5]
        ]

    ordered = sorted(
        table.values(),
        key=lambda row: (-row["points"], -row["gd"], -row["gf"], row["team_name"].lower()),
    )

    final_order = []
    index = 0
    while index < len(ordered):
        row = ordered[index]
        tied_group = [row]
        index += 1
        while index < len(ordered):
            next_row = ordered[index]
            if (
                next_row["points"] == row["points"]
                and next_row["gd"] == row["gd"]
                and next_row["gf"] == row["gf"]
            ):
                tied_group.append(next_row)
                index += 1
            else:
                break

        if len(tied_group) > 1:
            tied_ids = {team["team_id"] for team in tied_group}

            def h2h_key(team):
                stats = {"points": 0, "gf": 0, "ga": 0}
                for opponent_id in tied_ids - {team["team_id"]}:
                    opponent_stats = head_to_head[team["team_id"]][opponent_id]
                    stats["points"] += opponent_stats["points"]
                    stats["gf"] += opponent_stats["gf"]
                    stats["ga"] += opponent_stats["ga"]
                return (-stats["points"], -(stats["gf"] - stats["ga"]), -stats["gf"], team["team_name"].lower())

            tied_group = sorted(tied_group, key=h2h_key)

        final_order.extend(tied_group)

    cl_spot = league[4] or 0
    uel_spot = league[5] or 0
    relegation_spot = league[6] or len(final_order) + 1
    standings = []
    for position, row in enumerate(final_order, start=1):
        standings.append(
            (
                position,
                row["team_id"],
                row["team_name"],
                row["played"],
                row["won"],
                row["draw"],
                row["lost"],
                row["points"],
                row["gf"],
                row["ga"],
                row["gd"],
                row["form"],
                row["crest_url"],
                position <= cl_spot,
                cl_spot < position <= uel_spot,
                position >= relegation_spot,
            )
        )

    return standings
