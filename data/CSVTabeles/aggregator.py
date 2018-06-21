import pandas as pd

from os import listdir
from os.path import isfile, join
import re

PATH = './'
result_file = './__data_set.csv'

for f in listdir(PATH):
    if isfile(join(PATH, f)) and f.endswith('gamedata.csv'):
        file_game_data = f
        file_line_up = f.replace('gamedata', 'lineup')

        game_data = pd.read_csv(PATH + file_game_data, encoding='utf8').drop(['League'], axis=1)
        line_up = pd.read_csv(PATH + file_line_up, encoding='utf8')
        line_up = line_up.drop(['Bench%d%s' % (i, state) for i in range(1, 13) for state in ['Home', 'Away']], axis=1)

        data_partial = game_data.merge(line_up, on='GameID')

        players = ['Player%d%s' % (i, state) for i in range(1, 12) for state in ['Home', 'Away']]

        with open(result_file, 'a', encoding='utf-8') as output:
            data_partial.to_csv(output, header=False)
