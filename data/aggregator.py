import os

import pandas as pd
import math
import sqlite3
import time
import datetime
import numpy as np
import sys

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
    "wm2018gamedata",
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

GAME_DATA_TABLES = GAME_DATA_TABLES_2014_2016 + GAME_DATA_TABLES_2016_2018

PATH_FILE_RESULT = './data.csv'
DATABASE_NAME = './fifaComplete.db'


def get_file_output_name(complex=True, test=False):
    """
    returns related filename
    
    :param complex: 
    :return: 
    """
    return PATH_FILE_RESULT \
        .replace('.csv', '_complex.csv' if complex else '_simple.csv') \
        .replace('.csv', '_test.csv' if test else '_train.csv')


def get_data_from_table(table: str, where=None, purify=False) -> list:
    """
    builds list of [
        GameID,
        League,
        Season,
        Players...,
        result
    ]
    
    :param purify: 
    :param where: 
    :param table: related gamedata table
    :return: 
    """

    # preparation
    table_game_data = table
    table_line_up = table.replace('gamedata', 'lineup')

    #  get data from database
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    pre_select = ['gd.GameID', 'League', 'Season', 'Date']
    select = pre_select + ['Player%d%s' % (i, state) for state in ['Home', 'Away'] for i in range(1, 12)]

    select.append('result')
    data = cur.execute(
        'SELECT %s FROM %s as gd INNER JOIN %s lu ON gd.GameID = lu.GameID %s;'
        % (
            ','.join(select),
            table_game_data,
            table_line_up,
            '' if where is None else 'WHERE %s' % where
        )
    ).fetchall()

    cur.close()
    conn.close()

    # thin out data by lines with missing player info
    _data = []
    for row in data:
        # test if all players have bee set
        if not any([e == 'None' for e in row[len(pre_select):-1]]):
            tmp = list(row)
            # date data to unix timestamp
            tmp[3] = time.mktime(datetime.datetime.strptime(tmp[3], "%d.%m.%Y").timetuple())
            _data.append(tmp)
    data = _data

    return data


def get_data_from_tables(tables) -> list:
    """
    
    :param tables: 
    :return: 
    """
    result = []

    for _table in tables:
        result = result + get_data_from_table(_table)

    return result


def get_fifa_players() -> set:
    """
    returns set of all player names, that have been active in wm2018
    
    :return: set
    """
    table_game_data = 'wm2018gamedata'
    table_line_up = table_game_data.replace('gamedata', 'lineup')

    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    select = ['GameID'] + ['Player%d%s' % (i, state) for state in ['Home', 'Away'] for i in range(1, 12)]
    # bench
    # select = select + ['Bench%d%s' % (i, state) for i in range(1, 13) for state in ['Home', 'Away']]
    data = cur.execute(
        'SELECT %s FROM %s'
        % (
            ','.join(select),
            table_line_up
        )
    ).fetchall()

    result = []
    for l in data:
        result += list(l)

    result = list(set(result))
    result.remove('None')

    cur.close()
    conn.close()

    return set(result)


PLAYER_MAP = None


def get_player_map():
    global PLAYER_MAP

    if PLAYER_MAP is not None:
        return PLAYER_MAP
    data = get_data_from_tables(GAME_DATA_TABLES_2016_2018)

    PLAYER_MAP = list(set([player for row in data for player in row[4:-1]]))
    PLAYER_MAP = {k: v for v, k in enumerate(PLAYER_MAP)}

    return PLAYER_MAP


all_players_in_wm = []


def create_data_set(data, target_file, complex=True):
    """
    
    :param target_file: 
    :param data: 
    :param complex: 
    :return: 
    """
    # {'player_name' => 0, 'player_name' => 1, ...}
    player_map = get_player_map()

    # {'team_name' => 0, 'team_name' => 1, ...}
    # team_map = list(set([team for row in data for team in row[-3:-1]]))
    # team_map = {k: v for v, k in enumerate(team_map)}

    players_in_fifa_wm = set(get_fifa_players())
    output_result = []

    # os.remove(result_file)
    for i, row in enumerate(data):
        # has national players in wm 2018
        player_names = row[4:len(row) - 1]  # 'gd.GameID', 'League', 'Season', 'Date', ..., result
        has_wm_players = len(set(player_names).intersection(players_in_fifa_wm)) > 0

        # set result
        if row[len(row) - 1] != 'None':
            game_chunk = [int(s) for s in row[len(row) - 1].split(':')]
            data[i][26] = 1 if game_chunk[0] > game_chunk[1] else 2 if game_chunk[0] < game_chunk[1] else 0
        else:
            data[i][26] = None

        # filter by has wm players
        if has_wm_players:
            output_result.append(data[i])

    # all players, that played with players, that participates in wm
    global all_players_in_wm
    for l in output_result:
        all_players_in_wm = list(set(all_players_in_wm + l[4:len(l) - 1]))

    # create players part for home and away team
    chunks = [
        output_result[int(len(output_result) / 2):],
        output_result[:int(len(output_result) / 2)]
    ]
    for j, data in enumerate(chunks):
        result = []
        for i, l in enumerate(data):
            first_part = l[:4]
            player_part = l[4:len(l) - 1]
            result_part = [int(l[len(l) - 1]) if l[len(l) - 1] is not None else 0]

            if complex:
                new_player_part_home = [int(player in player_part[:11]) for player in all_players_in_wm]
                new_player_part_away = [int(player in player_part[11:]) for player in all_players_in_wm]
                new_player_part = new_player_part_home + new_player_part_away
                valid = sum(new_player_part_home) == sum(new_player_part_away) == 11 and
            else:
                new_player_part = [player_map[player] for player in player_part]
                valid = True

            if valid:
                result.append(first_part + new_player_part + result_part)

        result.sort(key=lambda x: x[0])

        # remove data.csv, if existent
        if 0 == j:
            try:
                os.remove(target_file)
            except OSError:
                pass

        # write new data
        with open(target_file, 'a', encoding='utf-8') as output:
            print('Write...')
            if complex:
                df = pd.DataFrame(
                    result
                ).drop(
                    [0, 1, 2],
                    axis=1
                )

                df.columns = list(range(len(result[0]) - 3))

                print('df.shape')
                print(df.shape)
                # for k, v in {k: np.int32 if k >= 3 else np.str_ for k in range(df.shape[0])}.items():
                #     try:
                #         df[k] = df[k].astype(v, errors='raise')
                #     except:
                #         print(sys.exc_info()[0])
                #         print(list(set(df[k].values)))
                #         print(k)
                #         print(v)
                #         print(result[0])
                #         exit(1)

                print('csv')
                df.to_csv(
                    output,
                    header=False,
                    encoding='utf-8',
                    index=False
                )
            else:
                pd.DataFrame(data).to_csv(output, header=False, encoding='utf-8', index=False)


def create_test_data_set(complex=True):
    """

    :param complex: 
    :return: 
    """
    # get finals
    game_ids = ["2451959", "2451960", "2451961", "2451962", "2451964", "2451963", "2451966", "2451965", "2451968",
                "2451967", "2451969", "2451970", "2451971", "2451972", "2451973", "8534362"]
    table_game_data = 'wm2018gamedata'

    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()

    select = ['GameID', 'League', 'Season', 'Date', 'HomeTeam', 'AwayTeam']
    data = cur.execute(
        'SELECT %s FROM %s as gd %s ORDER BY gd.GameID ASC;'
        % (
            ','.join(select),
            table_game_data,
            'WHERE gd.GameID IN (%s)' % ','.join('"' + str(gid) + '"' for gid in game_ids)
        )
    ).fetchall()

    _data = []
    for l in data:
        home_team = l[4]
        away_team = l[5]

        select = ['Player%d%s' % (i, state) for i in range(1, 12) for state in ['Home', 'Away']]
        home_team_lineup = list(cur.execute(
            'SELECT %s, gd.HomeTeam, gd.AwayTeam FROM wm2018lineup lu '
            'INNER JOIN wm2018gamedata gd on gd.GameID = lu.GameID '
            'WHERE lu.Player11Home <> "None" AND lu.Player11Away <> "None"'
            'AND gd.HomeTeam = "%s" OR gd.AwayTeam = "%s"' %
            (
                ','.join(select),
                home_team,
                home_team
            )
        ).fetchone())

        if home_team == home_team_lineup[len(home_team_lineup) - 2]:
            home_team_lineup = home_team_lineup[:11]
        else:
            home_team_lineup = home_team_lineup[11:22]

        away_team_lineup = list(cur.execute(
            'SELECT %s, gd.HomeTeam, gd.AwayTeam FROM wm2018lineup lu '
            'INNER JOIN wm2018gamedata gd on gd.GameID = lu.GameID '
            'WHERE lu.Player11Home <> "None" AND lu.Player11Away <> "None"'
            'AND gd.HomeTeam = "%s" OR gd.AwayTeam = "%s"' %
            (
                ','.join(select),
                away_team,
                away_team
            )
        ).fetchone())

        if away_team == away_team_lineup[len(away_team_lineup) - 2]:
            away_team_lineup = away_team_lineup[:11]
        else:
            away_team_lineup = away_team_lineup[11:22]

        _data.append(list(l[:4]) + home_team_lineup + away_team_lineup + ['None'])
        _data[len(_data) - 1][3] = time.mktime(
            datetime.datetime.strptime(_data[len(_data) - 1][3], "%d.%m.%Y").timetuple())
        data = _data

    cur.close()
    conn.close()

    create_data_set(data, get_file_output_name(complex, True), complex)


def create_train_data_set(complex=True):
    """

    :param complex: 
    :return: 
    """
    # get data from database
    data = get_data_from_tables(GAME_DATA_TABLES_2016_2018)

    create_data_set(data, get_file_output_name(complex, False), complex)


# main
if __name__ == '__main__':
    print('Create simple train data set...')
    create_train_data_set(False)
    print('Done.')
    print('Create complex train data set...')
    create_train_data_set()
    print('Done.')
    print('Create simple test data set...')
    create_test_data_set(False)
    print('Done.')
    print('Create complex test data set...')
    create_test_data_set()
    print('Done.')
