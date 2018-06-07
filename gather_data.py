import json
import operator
import re

import sqlite3
import urllib

import wikilib

WIKI_PAGE_IDS_GROUPS = [55809037]  # , 55809010, 55809044, 55809054, 55809062, 55809069, 55809077, 55809085]
WIKI_PLAYER_MAP = {
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

    'Yasser Al Mosailem': 'Yasser_Al-Mosailem',
}
WIKI_PLAYER_MAP_INV = {v: k for k, v in WIKI_PLAYER_MAP.items()}
API_PARAMS_GET_PLAYER_INFO_CONTENT = 'action=parse&pageid=%d&prop=wikitext&rvsection=0&rvprop=content&format=json'

TEAM_NAT_MAP = {
    'FC Istra': 'RUS',
    'FC Zenit St. Petersburg': 'RUS'
}

def get_teams_from_groups(team_page_id):
    return wikilib.get_page_section_content_by_id(team_page_id, '1')  # section 1 == group listing


def parse_teams(text):
    return [wikilib.parse_template(team) for team in re.findall('(\{\{fb\|[A-Z]*\}\})', text)]


def get_team_list():
    grouped_teams = [parse_teams(get_teams_from_groups(pid)) for pid in WIKI_PAGE_IDS_GROUPS]

    teams = [team for group in grouped_teams for team in group]

    for i, t in enumerate(teams):
        teams[i]['wiki_page_id'] = wikilib.get_page_id_by_link(t['link'])
        teams[i]['nationality'] = t['template'].strip("{}").split('|')[1]
        teams[i]['current_squad'] = get_current_squad(teams[i]['wiki_page_id'])

    return teams


def get_player_detail_info(link):
    def get_info(pid, link):
        static_redirect = link in WIKI_PLAYER_MAP.keys()
        if static_redirect:
            if "" == WIKI_PLAYER_MAP[link]:
                return None
            else:
                return get_player_detail_info(WIKI_PLAYER_MAP[link])

        url = urllib.request.urlopen(wikilib.API_URL + '?' + API_PARAMS_GET_PLAYER_INFO_CONTENT % pid)
        data = json.loads(url.read().decode())

        info = data['parse']['wikitext']['*']

        redirect = re.findall('#REDIRECT \[\[([^\]]*)\]\]', info)
        if redirect:
            return get_player_detail_info(redirect[0])

        return info

    def parse_info(link, info):
        redirect = re.findall('#REDIRECT \[\[([^\]]*)\]\]', info)
        if redirect:
            return get_player_detail_info(redirect[0])

        may_refer = re.findall('\'\'\'[^\']*\'\'\' may refer to:', info)
        if may_refer:
            footballer = re.findall('.*\[\[(%s \(footballer\))\]\].*' % link, info)
            if footballer:
                return get_player_detail_info(footballer[0])

        return info

    def parse_team_nationality(pid, name):
        if name in TEAM_NAT_MAP.keys():
            return TEAM_NAT_MAP[name]

        data = wikilib.get_page_section_content_by_priority_list(pid, ['Current squad', 'Players'])
        info = data['parse']['wikitext']['*']

        redirect = re.findall('#REDIRECT \[\[([^\]]*)\]\]', info)
        if redirect:
            return get_player_detail_info(redirect[0])

        nats = re.findall(r'\bnat= *([A-Z]*) *\b', data)
        _t = {}
        for n in nats:
            if n in _t.keys():
                _t[n] += 1
            else:
                _t[n] = 1

        return max(_t.items(), key=operator.itemgetter(1))[0]

    page_id = wikilib.get_page_id_by_link(link, WIKI_PLAYER_MAP)
    info = get_info(page_id, link)
    if type(info) is dict:
        return info

    if info is not None:
        info = parse_info(link, info)
        print(link)
        years = re.findall('[^a-z]years[0-9]* *= *([1-2][0-9][0-9][0-9].?[1-2]?[0-9]?[0-9]?[0-9]?)', info)
        clubs = re.findall('[^a-z]clubs[0-9]* *= *.?.?.?\[\[([^\]]*)\]\]', info)

        # some wiki data is broken e.g.
        # https://en.wikipedia.org/w/api.php?pageid=13042838&action=parse&prop=wikitext&format=json
        # years5 node but no clubs5
        years = years[:min([len(years), len(clubs)])]
        clubs = clubs[:min([len(years), len(clubs)])]
    else:
        years = []
        clubs = []

    # build season data
    _result = {}
    for i, y in enumerate(years):
        ys = y.split('–')

        club_info = clubs[i].strip('[]').split('|')
        club = {
            'name': club_info[1] if len(club_info) > 1 else club_info[0],
            'link': club_info[0],
        }

        # loans override host club
        if 1 == len(ys):
            _result[ys[0]] = club
        else:
            lb = int(ys[0])
            ub = (2018 if 0 == len(ys[1]) else int(ys[1])) + 1
            _current_years = list(range(lb, ub))

            for y in _current_years:
                _result[y] = club
    years = list(_result.keys())
    clubs = list(_result.values())
    clubs = [{
                'link': club['link'],
                'name': club['name'],
                'nationality': 'XXX',  # parse_team_nationality(wikilib.get_page_id_by_link(club['link']), club['link']),  # todo
                'is_national_team': 0,
                'wiki_page_id': wikilib.get_page_id_by_link(club['link'])
            } for club in clubs]
    return {
        'wiki_page_id': page_id,
        'years': years,
        'clubs': clubs,
    }


def get_current_squad(team_page_id):
    data = wikilib.get_page_section_content_by_priority_list(team_page_id, ['Current squad', 'Players'])

    print(team_page_id)
    if team_page_id == 28320974:
        print(team_page_id)

    # two possibilities
    idx = data.find('===Recent call-ups===')
    if idx >= 0:
        data = data[:idx]

    idx = data.find('===Recent===')
    if idx >= 0:
        data = data[:idx]

    squad = []
    for l in re.findall(
            r'{{nat fs g player|no=([0-9]*)\|pos=(GK|DF|MF|FW)\|name=(\[\[[^\]]*\]\]).*\|age=(\{\{([^\}]*)\}\})\|caps=([0-9]*)\|goals=([0-9]*)\|club=(\[\[[^\]]*\]\])\|clubnat=([A-Z]*)',
            data):
        if all('' + e for e in l):
            # try:
            club_info = l[7].strip('[]').split('|')

            # ** syntax to merge objects
            squad.append(
                {
                    **{
                        'name': u'' + l[2].strip('[]'),
                        'number': int(l[0]),
                        'position': l[1],
                        'caps': int(l[5]),
                        'goals': int(l[6]),
                        'team': {
                            'link': club_info[0],
                            'name': club_info[1] if len(club_info) > 1 else club_info[0],
                            'nationality': l[8],
                            'wiki_page_id': wikilib.get_page_id_by_link(club_info[0]),
                        },
                        'birthday': re.sub(
                            r'[^\|]*\|([1-2][0-9]*)\|([0-9]*)\|([0-9]*)\|.*',
                            r'\1-\2-\3',
                            l[4]
                        ),
                    },
                    **get_player_detail_info(u'' + l[2].strip('[]').split('|')[0])
                }
            )

    return squad


def assert_team(team, is_national_team, conn):
    cur = conn.cursor()

    cur.execute("SELECT id FROM team WHERE link = \"%s\"" % team['link'])
    id = cur.fetchone()
    if id is None:
        cur.execute(
            "INSERT INTO team (link, name, nationality, is_national_team, wiki_page_id) "
            "VALUES (\"%s\", \"%s\", '%s', %d, %d)" % (
                team['link'],
                team['name'],
                team['nationality'],
                is_national_team,
                team['wiki_page_id']
            )
        )
        conn.commit()

        team['team_id'] = cur.lastrowid
    else:
        team['team_id'] = id[0]

    return team


def add_nation(team, conn):
    cur = conn.cursor()
    sql = "INSERT INTO nation (name, link, wiki_page_id) VALUES ('%s', '%s', %d)"

    cur.execute(sql % (team['name'], team['link'], team['wiki_page_id']))
    conn.commit()

    team['nation_id'] = cur.lastrowid


def add_squad(team, conn):
    cur = conn.cursor()

    for player in team['current_squad']:
        print(player)

        t = player['team']
        t = assert_team(t, 0, conn)

        if player['name'][0] =='N':
            print(player)
        sql = "INSERT INTO player (name, number, position, birthday, caps, goals, wiki_page_id) VALUES (\"%s\", %d, '%s', '%s', %d, %d, %d)"
        cur.execute(sql % (
            player['name'],
            int(player['number']),
            player['position'],
            player['birthday'],
            int(player['caps']),
            int(player['goals']),
            player['wiki_page_id']
        ))
        conn.commit()

        sql = "INSERT INTO player_to_team (player_id, team_id, season) VALUES (%d, %d, '2017-2018')"
        cur.execute(sql % (cur.lastrowid, t['team_id']))

        for i, _team in enumerate(player['clubs']):
            assert_team(_team, 0, conn)

    conn.commit()


conn = sqlite3.connect('data/fifa.db')
cur = conn.cursor()
cur.execute("DELETE FROM nation")
cur.execute("DELETE FROM team")
cur.execute("DELETE FROM player")
cur.execute("DELETE FROM player_to_team")
conn.commit()

print('Start gathering teams...')
for team in get_team_list():
    print('Gathering teams done.')
    print('Assert Team.')
    assert_team(team, 1, conn)
    print('Add Nation.')
    add_nation(team, conn)
    print('Add Squad.')
    add_squad(team, conn)

conn.close()
