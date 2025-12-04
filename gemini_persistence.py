import operator
import time
import timeit
from functools import lru_cache, reduce
import matplotlib.pyplot as plt

import pandas as pd
from loguru import logger
from nba_api.stats.endpoints import CommonAllPlayers, CommonPlayerInfo


def get_active_player_roster():
    """
    Fetches the full roster of active NBA players, including their jersey numbers.

    This function first gets a list of all current season players and then loops
    through each player ID to fetch detailed player info (including the jersey number).
    A small delay is included to prevent hitting API rate limits.
    """
    print("--- Fetching List of All Players in Current Season... ---")

    # Use CommonAllPlayers to get a current list of players who have played this season.
    # Setting is_only_current_season=1 is a good way to filter for active players.
    all_players = CommonAllPlayers(
        is_only_current_season=1,
        league_id='00' # '00' is for NBA
    ).get_data_frames()[0]

    # Filter for players who are currently on an active roster (RosterStatus = 1).
    active_player_ids = all_players[all_players['ROSTERSTATUS'] == 1]['PERSON_ID'].tolist()

    print(f"Found {len(active_player_ids)} active players. Starting individual data fetch...")

    roster_data = []

    # Fetch detailed info for each active player
    for i, player_id in enumerate(active_player_ids):
        try:
            # CommonPlayerInfo contains the 'JERSEY' field
            player_info = CommonPlayerInfo(player_id=player_id)

            # The player info is in the first result set of the response
            info_df = player_info.get_data_frames()[0]

            if not info_df.empty:
                # Extract the required fields
                data = {
                    'PlayerName': info_df.iloc[0]['DISPLAY_FIRST_LAST'],
                    'TeamAbbr': info_df.iloc[0]['TEAM_ABBREVIATION'],
                    'JerseyNumber': info_df.iloc[0]['JERSEY'],
                    'Position': info_df.iloc[0]['POSITION']
                }
                roster_data.append(data)

            # Print progress
            if (i + 1) % 50 == 0 or (i + 1) == len(active_player_ids):
                print(f"Progress: Fetched data for {i + 1}/{len(active_player_ids)} players.")

            # IMPORTANT: Wait to avoid hitting rate limits.
            # 0.6 seconds is a safe minimum.
            time.sleep(0.6)

        except Exception as e:
            print(f"Error fetching data for player ID {player_id}: {e}")
            # Wait a little longer on error and continue
            time.sleep(2)
            continue

    # Convert the list of dictionaries into a DataFrame
    final_roster_df = pd.DataFrame(roster_data)

    # Sort the list by Team and then by Jersey Number
    final_roster_df['JerseyNumber'] = pd.to_numeric(final_roster_df['JerseyNumber'], errors='coerce')
    final_roster_df = final_roster_df.sort_values(by=['TeamAbbr', 'JerseyNumber'], ascending=[True, True])

    return final_roster_df


def multiply_digits(num: int) -> int:
    """Multiply the digits of an integer.

    >>> multiply_digits(36)
    18
    """
    digits = [int(d) for d in str(num)]
    return reduce(operator.mul, digits, 1)

@lru_cache(maxsize=1028)  # Plenty for all 3 digit numbers
def persistence_recursive(num: int) -> int:
    """Calculate the persistence of a number recursively."""
    if num < 10:
        return 0
    num = multiply_digits(num)
    return 1 + persistence_recursive(num)

@lru_cache(maxsize=1028)  # Plenty for all 3 digit numbers
def persistence_brute(num: int) -> int:
    """Calculate the persistence of a number iteratively."""
    persistence = 0
    while num >= 10:
        persistence += 1
        num = multiply_digits(num)
    return persistence

def calculate_persistence_both(num: int) -> int:
    persistence_one = persistence_brute(num)
    persistence_two = persistence_recursive(num)
    if persistence_one != persistence_two:
        logger.error(f"{num=} {persistence_one=} != {persistence_two=}")
        raise ValueError

    logger.info(f"{num=} {persistence_one=}")
    return persistence_two

def persistence_list_resursive(num: int) -> list[int]:
    """Get the intermediate numbers in the persistence calculation. Using recursive approach."""
    if num < 10:
        return [num]
    return [num] + persistence_list_resursive(multiply_digits(num))

def persistence_list_brute(num: int) -> list[int]:
    """Get the intermediate numbers in the persistence calculation. Using brute force approach."""
    num_list = [num]
    if num < 10:
        return num_list
    while num >= 10:
        num = multiply_digits(num)
        num_list.append(num)
    return num_list

def calculate_persistence_list_both(num: int) -> int:
    """Calculate the persistence list using both approaches."""
    persistence_list_one = persistence_list_resursive(num)
    persistence_list_two = persistence_list_brute(num)
    if persistence_list_one != persistence_list_two:
        logger.error(f"{num=} {persistence_list_one=} != {persistence_list_two=}")
        raise ValueError
    return persistence_list_one

# plotting the distribution of the last digit of the persistence list
def plot_persistence_list_distribution(last_digit_of_persistence_list: list[int], output_file = "persistence_list_distribution.png"):
    from pathlib import Path
    list_of_last_digits = [digit for digit in last_digit_of_persistence_list if digit is not None]
    logger.info(f"{list_of_last_digits=}")
    plt.hist(list_of_last_digits, bins=range(0, 11), edgecolor='black')
    plt.xlabel('Last Digit of Persistence List')
    plt.ylabel('Frequency')
    plt.title('Distribution of Last Digit of Persistence List')
    plt.xticks([i + 0.5 for i in range(10)], [str(i) for i in range(10)])
    output_path = Path(__file__).parent / output_file
    plt.savefig(output_path)
    plt.close()

if __name__ == "__main__":
    from pathlib import Path
    output_csv = Path(__file__).parent / 'nba_active_roster.csv'

    if not output_csv.exists():
        logger.info("Querying active player roster data")
        roster_df = get_active_player_roster()
        roster_df.to_csv(output_csv, index=False)
        logger.info(f"Data saved to {output_csv}")
    else:
        logger.info(f"Reading data from {output_csv}")
        roster_df = pd.read_csv(output_csv)

    roster_df = roster_df[roster_df["JerseyNumber"].notna()]
    logger.info(f"{roster_df['JerseyNumber'].isna().sum()}")
    roster_df["JerseyNumber"] = roster_df["JerseyNumber"].astype(int)
    roster_df["persistence_steps"] = roster_df.apply(lambda row: calculate_persistence_list_both(row["JerseyNumber"]), axis="columns")
    roster_df["persistence"] = roster_df.apply(lambda row: len(row["persistence_steps"])-1, axis="columns")
    roster_df["last_digit_of_persistence_list"] = roster_df.apply(lambda row: list(row["persistence_steps"])[-1], axis="columns")
    roster_df.sort_values(by="persistence", ascending=False, inplace=True)
    roster_df.to_csv(output_csv, index=False)
    logger.info(f"Persistence data saved to {output_csv}")

    plot_persistence_list_distribution(roster_df["last_digit_of_persistence_list"].tolist())
    logger.info("Persistence list distribution saved to persistence_list_distribution.png")

    if not roster_df.empty:
        print("\n" + "="*50)
        print("     Active NBA Player Roster & Jersey Numbers")
        print("="*50)

        #Display the result
        print(roster_df[['TeamAbbr', 'JerseyNumber', 'PlayerName', 'Position', "persistence"]].to_string(index=False))

    # Tangent: What's the max persistence of a two-digit number?
    twodigit_to_p: list[tuple[int, list[int]]] = [(n, persistence_list_resursive(n)) for n in range(100)]
    twodigit_to_p.sort(key=lambda item: item[1], reverse=True)
    logger.info(f"{twodigit_to_p[:10]=}")
    plot_persistence_list_distribution([persistence_list[-1] for num, persistence_list in twodigit_to_p], output_file="two_digit_persistence_distribution.png")

    # Tangent: What's the max persistence of a three-digit number?
    threedigit_to_p: list[tuple[int, list[int]]] = [(n, persistence_list_resursive(n)) for n in range(1000)]
    threedigit_to_p.sort(key=lambda item: item[1], reverse=True)
    logger.info(f"{threedigit_to_p[:10]=}")
    plot_persistence_list_distribution([persistence_list[-1] for num, persistence_list in threedigit_to_p], output_file="three_digit_persistence_distribution.png")

    # Tangent: Which of our persistence methods is faster??
    test_numbers = list(range(10, 1000))  # All 2- and 3-digit numbers

    def time_function(func, numbers):
        return timeit.timeit(lambda: [func(n) for n in numbers], number=10)

    brute_time = time_function(persistence_brute, test_numbers)
    recursive_time = time_function(persistence_recursive, test_numbers)

    print(f"Brute: {brute_time:.4f}s, Recursive: {recursive_time:.4f}s")
