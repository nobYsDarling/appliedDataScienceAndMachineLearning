import re

import urllib.request
import urllib as ul
import urllib3
import json


def read_team(team, display_name='', source='data_enriched'):
    # read file
    f = source + '/%s.csv' % team
    h = open(f, 'r', encoding='utf8')
    t = h.read().split("\n")
    h.close()

    if '' == display_name:
        display_name = team

    # build return value
    d = {
        'display_name': display_name,
        'trainer': t[0],
        'market_value': t[1],
        'fifa_rank': t[2],
        'players': []
    }
    for p in t[4:]:
        if '' != p:
            name = re.sub('^([^(]*) \(.*$', '\g<1>', p)
            club = re.sub('^[^(]* \(([^)]*)\).*$', '\g<1>', p)
            d['players'].append((name, club))

            if name == club:
                print(team)
                print(name)

                exit(1)

    return d


def read_teams(source='data_enriched'):
    # read file
    f = source + '/teams.csv'
    h = open(f, 'r', encoding='utf8')
    ts = h.read().split("\n")
    h.close()

    result = {}
    for t in ts:
        name = re.sub('^(.*) - (.*)$', '\g<1>', t)
        disp = re.sub('^(.*) - (.*)$', '\g<2>', t)

        result[name] = read_team(name, disp, source)

    return result


def get_players(teams):
    ps = []

    for t in teams:
        for p in teams[t]['players']:
            ps.append(p)

    return ps

PLAYER_STATIC_REDIRECTS = {
    'Danny Rose': 'Danny Rose (footballer, born 1990)',
    'Seyed Hossein Hosseini': 'Hossein Hosseini (footballer, born 1992)',
    'Marcelo': 'Marcelo (footballer, born 1988)',
    'Fernandinho': 'Fernandinho_(footballer)',
    'Fred': 'Fred_(footballer, born 1983)',
    'Paulinho': 'Paulinho (footballer, born 1988)',
    'Lee Yong': 'Lee Yong (footballer, born 1986)',
    'Lee Jae-sung': 'Lee Jae-sung (footballer, born 1992)',
    'Brad Jones': 'Brad Jones (footballer)',
    'James Meredith': 'James Meredith (footballer)',
    'Ederson': 'Ederson_Honorato_Campos',
    'Fagner': 'Fagner_Conserva_Lemos',
    'João Miranda': 'João Miranda de Souza Filho',
    'Willian': 'Willian_(footballer,_born_1988)',
    # columbia
    'Carlos Sánchez': 'Carlos Sánchez Moreno',
    'José Izquierdo': 'José Heriberto Izquierdo Mena',
    'Sebastián Pérez': 'Sebastián Pérez Cardona',
    # egypt
    'Mahmoud Abdel Aziz': 'Mahmoud Abdel Aziz (footballer)',
    'Kahraba': 'Kahraba (footballer)',
    'Mahmoud Hassan': 'Mahmoud_Hassan_(footballer)',
    'Ahmed Hassan': 'Ahmed_Hassan_(footballer)',
    # england
    'Phil Jones': 'Phil Jones (footballer, born 1992)',
    # france
    'Djibril Sidibé': 'Djibril Sidibé (footballer, born 1992)',
    'N’Golo Kanté': 'N\'Golo_Kanté',
    'Steven N’Zonzi': 'Steven N\'Zonzi',
    # iceland
    'Hannes Halldorsson': 'Hannes_Þór_Halldórsson',
    # nigeria
    'Ahmed Musa': 'Ahmed_Musa_(footballer)',
    # panama
    'Jose Calderon': 'José Calderón (Panamanian footballer)',
    'Alex Rodriguez': 'Álex Rodríguez (Panamanian footballer)',
    'Adalberto Carrasquilla': '',  # no wiki page
    'Cristian Martinez': 'Cristian Martínez (Panamanian footballer)',
    'Ismael Diaz': 'Ismael Díaz (Panamanian footballer)',
    'Jose Fajardo': 'José Fajardo (footballer)',
    # peru
    'Sergio Pena': 'Sergio Peña (Peruvian footballer)',
    # peru
    'Beto': 'Beto (footballer, born 1982)',
    'Pepe': 'Pepe (footballer, born 1983)',
    'Bruno Fernandes': 'Bruno Fernandes (footballer, born 1994)',
    'Manuel Fernandes': 'Manuel Fernandes (footballer, born 1986)',
    'André Silva': 'André Silva (footballer, born 1995)',
    'João Mário': 'João Mário (Portuguese footballer)',
}


def get_wiki_info(name):
    def get_info(s):
        static_redirect = name in PLAYER_STATIC_REDIRECTS.keys()
        if static_redirect:
            if "" == PLAYER_STATIC_REDIRECTS[name]:
                return None
            else:
                return get_wiki_info(PLAYER_STATIC_REDIRECTS[name])

        url = urllib.request.urlopen("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=%s&rvsection=0&" % ul.request.quote(s))
        data = json.loads(url.read().decode())

        return list(data['query']['pages'].values())[0]['revisions'][0]['*']

    def parse_info(name, info):
        redirect = re.findall('#REDIRECT \[\[([^\]]*)\]\]', info)
        if redirect:
            return get_wiki_info(redirect[0])

        may_refer = re.findall('\'\'\'[^\']*\'\'\' may refer to:', info)
        if may_refer:
            footballer = re.findall('.*\[\[(%s \(footballer\))\]\].*' % name, info)
            if footballer:
                return get_wiki_info(footballer[0])

        # print('### PARSE INFO ###')
        # print(info)

        return info
        # print(info)
        # exit(1)

    info = get_info(name)
    if info is not None:
        info = parse_info(name, info)

        years = re.findall('[^a-z]years[0-9]* *= *([1-2][0-9][0-9][0-9].?[1-2]?[0-9]?[0-9]?[0-9]?)', info)
        clubs = re.findall('[^a-z]clubs[0-9]* *= *.?.?.?\[\[([^\]]*)\]\]', info)
    else:
        years = []
        clubs = []
    # print(info)
    print(years)
    print(clubs)
    return info


# print(get_wiki_info("N’Golo_Kanté"))
# exit(1)
i = 0

# flipped names in south korea to macth wikipedia names
for p in read_team('saudi-arabia')['players']:
    print(p)
    get_wiki_info(p[0])

    if i == 10:
        exit(1)

    # i += 1

