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

gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2025-26', league_id_nullable='00', 
                                              season_type_nullable='Regular Season')
games = gamefinder.get_data_frames()[0]
# Get a list of distinct game ids 
game_ids = games['GAME_ID'].unique().tolist()
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
for game_id in game_ids:
    game_data = get_data(game_id)
    pbpdata.append(game_data)
df = pd.concat(pbpdata, ignore_index=True)
gameids = df['gameid'].drop_duplicates()

#GET ALL ACTIVE PLAYERS, GET THEIR NAMES, IDS, AND ALL UNIQUE PLAYER ID AND GAME ID FROM CURRENT SEASON

player_df = pd.DataFrame(players.get_players())
player_id = player_df[['id', 'full_name']][player_df['is_active'] == True] .drop_duplicates() 
playernames = player_id['full_name'].to_list()
player_ids = player_id['id'].to_list()
games_df = df[['personId','gameid']].drop_duplicates()

# get data for all games
season_games = games_df['gameid'].unique()
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



