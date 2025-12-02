import time

import pandas as pd
import requests

# Required NBA Stats API headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
}

def get_active_players(season="2024-25"):
    url = "https://stats.nba.com/stats/commonallplayers"
    params = {
        "LeagueID": "00",
        "Season": season,
        "IsOnlyCurrentSeason": "1"
    }

    res = requests.get(url, headers=HEADERS, params=params)
    res.raise_for_status()

    data = res.json()["resultSets"][0]
    headers = data["headers"]
    rows = data["rowSet"]

    df = pd.DataFrame(rows, columns=headers)
    return df


def get_player_jersey(player_id: int):
    url = "https://stats.nba.com/stats/commonplayerinfo"
    params = {"PlayerID": player_id}

    res = requests.get(url, headers=HEADERS, params=params)
    res.raise_for_status()

    info = res.json()["resultSets"][0]["rowSet"][0]
    headers = res.json()["resultSets"][0]["headers"]
    row = dict(zip(headers, info))

    return row.get("JERSEY", None)


def get_all_players_with_jerseys():
    players = get_active_players()

    results = []
    for _, row in players.iterrows():
        player_id = int(row["PERSON_ID"])
        player_name = row["DISPLAY_LAST_COMMA_FIRST"]

        jersey = get_player_jersey(player_id)
        results.append({
            "player_id": player_id,
            "player_name": player_name,
            "jersey": jersey
        })

        time.sleep(0.15)  # polite delay to avoid rate-limits

    return pd.DataFrame(results)


# Run it
df = get_all_players_with_jerseys()
print(df)
