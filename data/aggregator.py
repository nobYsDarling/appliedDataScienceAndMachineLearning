import pandas as pd
import numpy as np
import math
import os

import sqlite3
import time
import datetime

GAME_DATA_TABLES_2016_2018 = [
    "bundesliga20162017gamedata",
    "bundesliga20172018gamedata",
    "premierleague20162017gamedata",
    "premierleague20172018gamedata",
    "primeradivision20162017gamedata",
    "primeradivision20172018gamedata",
    "ligue120162017gamedata",
    "ligue120172018gamedata",
    "seriea20162017gamedata",
    "seriea20172018gamedata",
    "sueperlig20162017gamedata",
    "sueperlig20172018gamedata",
    "eredivisie20162017gamedata",
    "eredivisie20172018gamedata",
    "premierliga20162017gamedata",
    "premierliga20172018gamedata",
    "primeiraliga20162017gamedata",
    "primeiraliga20172018gamedata",
    "superleague20162017gamedata",
    "superleague20172018gamedata",
    "autbundesliga20162017gamedata",
    "autbundesliga20172018gamedata",
    "suisuperleague20162017gamedata",
    "suisuperleague20172018gamedata",
    "braseriea20162017gamedata",
    "braseriea20172018gamedata",
    "argprimeradivision20162017gamedata",
    "argprimeradivision20172018gamedata",
    "z2bundesliga20162017gamedata",
    "z2bundesliga20172018gamedata",
    "dfbpokal2017gamedata",
    "dfbpokal2018gamedata",
    "facup2017gamedata",
    "facup2018gamedata",
    "leaguecup2017gamedata",
    "leaguecup2018gamedata",
    "coppaitalia2017gamedata",
    "coppaitalia2018gamedata",
    "copadelrey2017gamedata",
    "copadelrey2018gamedata",
    "wm2014gamedata",
    "europameisterschaft2016gamedata",
    "afrikacup2017gamedata",
    "confedcup2017gamedata",
    "championsleague2017gamedata",
    "championsleague2018gamedata",
    "europaleague2017gamedata",
    "europaleague2018gamedata",
    "copalibertadores2017gamedata",
    "copalibertadores2018gamedata"
]
GAME_DATA_TABLES_2014_2016 = [
    "bundesliga20142015gamedata",
    "bundesliga20152016gamedata",
    "premierleague20142015gamedata",
    "premierleague20152016gamedata",
    "primeradivision20142015gamedata",
    "primeradivision20152016gamedata",
    "ligue120142015gamedata",
    "ligue120152016gamedata",
    "seriea20142015gamedata",
    "seriea20152016gamedata",
    "sueperlig20142015gamedata",
    "sueperlig20152016gamedata",
    "eredivisie20142015gamedata",
    "eredivisie20152016gamedata",
    "premierliga20142015gamedata",
    "premierliga20152016gamedata",
    "primeiraliga20142015gamedata",
    "primeiraliga20152016gamedata",
    "superleague20152016gamedata",
    "autbundesliga20142015gamedata",
    "autbundesliga20152016gamedata",
    "suisuperleague20142015gamedata",
    "suisuperleague20152016gamedata",
    "braseriea20142015gamedata",
    "braseriea20152016gamedata",
    "argprimeradivision20142015gamedata",
    "argprimeradivision20152016gamedata",
    "z2bundesliga20142015gamedata",
    "z2bundesliga20152016gamedata",
    "dfbpokal2014gamedata",
    "dfbpokal2015gamedata",
    "dfbpokal2016gamedata",
    "facup2014gamedata",
    "facup2015gamedata",
    "facup2016gamedata",
    "leaguecup2014gamedata",
    "leaguecup2015gamedata",
    "leaguecup2016gamedata",
    "coppaitalia2014gamedata",
    "coppaitalia2015gamedata",
    "coppaitalia2016gamedata",
    "copadelrey2014gamedata",
    "copadelrey2015gamedata",
    "copadelrey2016gamedata",
    "afrikacup2015gamedata",
    "copaamerica2015gamedata",
    "copaamerica2016gamedata",
    "klubwm2014gamedata",
    "klubwm2015gamedata",
    "klubwm2016gamedata",
    "klubwm2017gamedata",
    "championsleague2014gamedata",
    "championsleague2015gamedata",
    "championsleague2016gamedata",
    "europaleague2014gamedata",
    "europaleague2015gamedata",
    "europaleague2016gamedata",
    "copalibertadores2014gamedata",
    "copalibertadores2015gamedata",
    "copalibertadores2016gamedata",
]
__GAME_DATA_TABLES = [
    # "bundesliga20122013gamedata",
    # "bundesliga20132014gamedata",
    # "bundesliga20142015gamedata",
    # "bundesliga20152016gamedata",
    "bundesliga20162017gamedata",
    "bundesliga20172018gamedata",
    # "premierleague20122013gamedata",
    # "premierleague20132014gamedata",
    # "premierleague20142015gamedata",
    # "premierleague20152016gamedata",
    "premierleague20162017gamedata",
    "premierleague20172018gamedata",
    # "primeradivision20122013gamedata",
    # "primeradivision20132014gamedata",
    # "primeradivision20142015gamedata",
    # "primeradivision20152016gamedata",
    "primeradivision20162017gamedata",
    "primeradivision20172018gamedata",
    # "ligue120122013gamedata",
    # "ligue120132014gamedata",
    # "ligue120142015gamedata",
    # "ligue120152016gamedata",
    "ligue120162017gamedata",
    "ligue120172018gamedata",
    # "seriea20122013gamedata",
    # "seriea20132014gamedata",
    # "seriea20142015gamedata",
    # "seriea20152016gamedata",
    "seriea20162017gamedata",
    "seriea20172018gamedata",
    # "sueperlig20122013gamedata",
    # "sueperlig20132014gamedata",
    # "sueperlig20142015gamedata",
    # "sueperlig20152016gamedata",
    "sueperlig20162017gamedata",
    "sueperlig20172018gamedata",
    # "eredivisie20122013gamedata",
    # "eredivisie20132014gamedata",
    # "eredivisie20142015gamedata",
    # "eredivisie20152016gamedata",
    "eredivisie20162017gamedata",
    "eredivisie20172018gamedata",
    # "premierliga20122013gamedata",
    # "premierliga20132014gamedata",
    # "premierliga20142015gamedata",
    # "premierliga20152016gamedata",
    "premierliga20162017gamedata",
    "premierliga20172018gamedata",
    # "primeiraliga20122013gamedata",
    # "primeiraliga20132014gamedata",
    # "primeiraliga20142015gamedata",
    # "primeiraliga20152016gamedata",
    "primeiraliga20162017gamedata",
    "primeiraliga20172018gamedata",
    # "superleague20152016gamedata",
    "superleague20162017gamedata",
    "superleague20172018gamedata",
    # "autbundesliga20122013gamedata",
    # "autbundesliga20132014gamedata",
    # "autbundesliga20142015gamedata",
    # "autbundesliga20152016gamedata",
    "autbundesliga20162017gamedata",
    "autbundesliga20172018gamedata",
    # "superleague20122013gamedata",
    # "superleague20132014gamedata",
    # "superleague20142015gamedata",
    # "suisuperleague20122013gamedata",
    # "suisuperleague20132014gamedata",
    # "suisuperleague20142015gamedata",
    # "suisuperleague20152016gamedata",
    "suisuperleague20162017gamedata",
    "suisuperleague20172018gamedata",
    # "braseriea20122013gamedata",
    # "braseriea20132014gamedata",
    # "braseriea20142015gamedata",
    # "braseriea20152016gamedata",
    "braseriea20162017gamedata",
    "braseriea20172018gamedata",
    # "argprimeradivision20122013gamedata",
    # "argprimeradivision20132014gamedata",
    # "argprimeradivision20142015gamedata",
    # "argprimeradivision20152016gamedata",
    "argprimeradivision20162017gamedata",
    "argprimeradivision20172018gamedata",
    # "z2bundesliga20122013gamedata",
    # "z2bundesliga20132014gamedata",
    # "z2bundesliga20142015gamedata",
    # "z2bundesliga20152016gamedata",
    "z2bundesliga20162017gamedata",
    "z2bundesliga20172018gamedata",
    # "dfbpokal2014gamedata",
    # "dfbpokal2013gamedata",
    # "dfbpokal2015gamedata",
    # "dfbpokal2016gamedata",
    "dfbpokal2017gamedata",
    "dfbpokal2018gamedata",
    # "facup2013gamedata",
    # "facup2014gamedata",
    # "facup2015gamedata",
    # "facup2016gamedata",
    "facup2017gamedata",
    "facup2018gamedata",
    # "leaguecup2013gamedata",
    # "leaguecup2014gamedata",
    # "leaguecup2015gamedata",
    # "leaguecup2016gamedata",
    "leaguecup2017gamedata",
    "leaguecup2018gamedata",
    # "coppaitalia2013gamedata",
    # "coppaitalia2014gamedata",
    # "coppaitalia2015gamedata",
    # "coppaitalia2016gamedata",
    "coppaitalia2017gamedata",
    "coppaitalia2018gamedata",
    # "copadelrey2013gamedata",
    # "copadelrey2014gamedata",
    # "copadelrey2015gamedata",
    # "copadelrey2016gamedata",
    "copadelrey2017gamedata",
    "copadelrey2018gamedata",
    "wm2014gamedata",
    # "europameisterschaft2012gamedata",
    "europameisterschaft2016gamedata",
    # "afrikacup2015gamedata",
    "afrikacup2017gamedata",
    # "copaamerica2015gamedata",
    # "copaamerica2016gamedata",
    "confedcup2017gamedata",
    # "klubwm2012gamedata",
    # "klubwm2013gamedata",
    # "klubwm2014gamedata",
    # "klubwm2015gamedata",
    # "klubwm2016gamedata",
    # "klubwm2017gamedata",
    # "championsleague2013gamedata",
    # "championsleague2014gamedata",
    # "championsleague2015gamedata",
    # "championsleague2016gamedata",
    "championsleague2017gamedata",
    "championsleague2018gamedata",
    # "europaleague2013gamedata",
    # "europaleague2014gamedata",
    # "europaleague2015gamedata",
    # "europaleague2016gamedata",
    "europaleague2017gamedata",
    "europaleague2018gamedata",
    # "copalibertadores2013gamedata",
    # "copalibertadores2014gamedata",
    # "copalibertadores2015gamedata",
    # "copalibertadores2016gamedata",
    "copalibertadores2017gamedata",
    "copalibertadores2018gamedata"
]
GAME_DATA_TABLES = GAME_DATA_TABLES_2014_2016 + GAME_DATA_TABLES_2016_2018

result_file = './__data_set.csv'


def get_data(table):
    table_game_data = table
    table_line_up = table.replace('gamedata', 'lineup')

    conn = sqlite3.connect('fifaComplete.db')
    cur = conn.cursor()

    select = ['gd.GameID', 'League', 'Season', 'Date']
    select = select + ['Player%d%s' % (i, state) for i in range(1, 12) for state in ['Home', 'Away']]
    select.append('AwayTeam')
    select.append('HomeTeam')
    select.append('result')
    data = cur.execute(
        'SELECT %s FROM %s as gd INNER JOIN %s lu ON gd.GameID = lu.GameID;'
        % (
            ','.join(select),
            table_game_data,
            table_line_up
        )
    ).fetchall()

    cur.close()
    conn.close()

    _data = []
    for row in data:
        if any([e == 'None' for e in row[4:-1]]):
            print(row)
        else:
            tmp = list(row)
            tmp[3] = time.mktime(datetime.datetime.strptime(tmp[3], "%d.%m.%Y").timetuple())
            _data.append(tmp)
    data = _data

    return data


def chunks(l, n):
    cs = []

    i = 0
    for j in range(0, len(l), int(math.ceil(len(l) / n))):
        cs.append(l[i:j])
        i = j

    return cs


result = []
for table in GAME_DATA_TABLES:
    result = result + get_data(table)

player_map = list(set([player for row in result for player in row[4:-3]]))
player_map = {k: v for v, k in enumerate(player_map)}

team_map = list(set([team for row in result for team in row[-3:-1]]))
team_map = {k: v for v, k in enumerate(team_map)}

inc = 0
os.remove(result_file)
for chunk in [result]:
    for i, row in enumerate(chunk):
        # set result
        game_chunk = [int(s) for s in chunk[i][28].split(':')]
        chunk[i][28] = 1 if game_chunk[0] > game_chunk[1] else 2 if game_chunk[0] < game_chunk[1] else 0

        for j in range(4, len(row) - 3):
            chunk[i][j] = player_map[chunk[i][j]]

        for j in range(-3, -1):
            chunk[i][j] = team_map[chunk[i][j]]

        # # determine player list
        # player_idxs = []
        # for j in range(4, len(row) - 3):
        #     data[i][j] = player_map[data[i][j]]
        #     player_idxs.append(player_map[chunk[i][j]])
        # players = [1 if v in player_idxs else 0 for v in player_map.values()]
        #
        # # determine team list
        # team_idxs = []
        # for j in range(-3, -1):
        #     team_idxs.append(team_map[chunk[i][j]])
        # teams = [1 if v in team_idxs else 0 for v in team_map.values()]
        #
        # chunk[i] = chunk[i][:3] + players + teams + chunk[i][28:]
    result.sort(key=lambda x: x[0])

    with open(result_file, 'a', encoding='utf-8') as output:
        print('Write...')
        pd.DataFrame(result).drop([0, 1, 2], axis=1).to_csv(output, header=False, encoding='utf-8', index=False)