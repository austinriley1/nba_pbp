import requests
import pandas as pd
import numpy as np
import io
import time
from datetime import timedelta
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import players
import matplotlib.pyplot as plt
from nba_api.stats.endpoints import boxscoretraditionalv3
from zoneinfo import ZoneInfo
from dateutil.tz import tzutc
from datetime import datetime
import warnings
import isodate
import math
headers  = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}
warnings.filterwarnings('ignore')

#PULL IN GAMES WE ALREADY HAVE
game_ids_yesterday = pd.read_csv('current_season_gameids.csv')
game_ids_yesterday['gameid'] = game_ids_yesterday['0']
game_ids_yesterday = pd.DataFrame(game_ids_yesterday['gameid'])
game_ids_yesterday['gameid'] = game_ids_yesterday['gameid'].astype(int)


#GET ALL GAMES 2025-26
gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2025-26', league_id_nullable='00', 
                                              season_type_nullable='Regular Season')
games = gamefinder.get_data_frames()[0]
# Get a list of distinct game ids 
game_ids = games['GAME_ID'].unique().tolist()

game_ids_today = pd.DataFrame(game_ids)
game_ids_today.columns = game_ids_today.columns.astype(str)
game_ids_today['gameid'] = game_ids_today['0']
game_ids_today = pd.DataFrame(game_ids_today['gameid'])
game_ids_today['gameid'] = game_ids_today['gameid'].astype(int)

#GET GAMES WE NEED TO GET FROM TODAY
game_ids_compare = game_ids_today.merge(game_ids_yesterday.drop_duplicates(), on='gameid', 
                   how='left', indicator=True)
game_ids_diff = game_ids_compare[game_ids_compare['_merge'] == 'left_only']['gameid']
game_ids_diff


# create function that gets pbp logs from the 2020-21 season
def get_data(game_id):
    play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_"+game_id+".json"
    response = requests.get(url=play_by_play_url, headers=headers).json()
    play_by_play = response['game']['actions']
    df = pd.DataFrame(play_by_play)
    df['gameid'] = game_id
    return df
# get data from all ids (takes awhile)
pbpdata = []
for game_id in game_ids_diff.to_list():
    game_data = get_data(game_id)
    pbpdata.append(game_data)
df = pd.concat(pbpdata, ignore_index=True)



#GET ALL ACTIVE PLAYERS, GET THEIR NAMES, IDS, AND ALL UNIQUE PLAYER ID AND GAME ID FROM CURRENT SEASON

# get data for all games
season_games = game_ids_diff.unique()
all_box_scores = []

for i, gameid in enumerate(season_games, 1):
    print(f"\rFetching game {i}/{len(season_games)}: {gameid}", end="", flush=True)
    time.sleep(2.5)
    
    try:
        box_score_trad = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=gameid) 
        box_score_df = box_score_trad.get_data_frames()[0]
        all_box_scores.append(box_score_df)
    except Exception as e:
        print(f"\n⚠️ Skipping game {gameid} - {type(e).__name__}: {e}")
    
    # Cooldown every 50 games
    if i % 50 == 0:
        print(f"\n⏸️ Processed 50 games, cooling down for 3 minutes...", end='\r',flush=True)
        time.sleep(180)

box_score_full_df = pd.concat(all_box_scores,ignore_index=True)



