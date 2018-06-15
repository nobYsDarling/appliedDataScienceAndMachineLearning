import json
import operator
import re

import sqlite3
import urllib

import wikilib

WIKI_PAGE_IDS_GROUPS = [55809037, 55809010, 55809044, 55809054, 55809062, 55809069, 55809077, 55809085]
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
    'FC Zenit St. Petersburg': 'RUS',
    'FC Mozdok': 'RUS',
    'FC Spartak-Alania Vladikavkaz': 'RUS',
    'FC Akademiya Togliatti': 'RUS',
    'FC SKA-Energiya Khabarovsk': 'RUS',
    'FC Sibiryak Bratsk': 'RUS',
    'FC Terek Grozny': 'RUS',
    'FC Zvezda Irkutsk': 'RUS',
    'FC Zhemchuzhina-Sochi': 'RUS',
    'FC Karelia Petrozavodsk': 'RUS',
    'FC Akademiya Tolyatti': 'RUS',
    'FC Levadia Tallinn': 'RUS',
    'FC Spartak Tambov': 'RUS',
    'FC Moscow': 'RUS',
    'Al-Ahli (Jeddah)': 'KSA',
    'Al-Ahli SC (Jeddah)': 'KSA',
    'Al Nassr FC': 'KSA',
    'Al-Qadisiyah FC': 'KSA',
    'Al-Shabab Riyadh': 'KSA',
    'Al-Ittihad (Jeddah)': 'KSA',
    'Al-Khaleej Club (Saudi)': 'KSA',
    'Al Shabab FC (Riyadh)': 'KSA',
    'Louletano': 'POR',
    'Al-Nassr': 'KSA',
    'Al-Qadisiya Al Khubar': 'KSA',
    'Damietta SC': 'EGY',
    'Al-Merreikh SC': 'SDN',
    'Wadi Degla FC': 'EGY',
    'Tala\'ea El-Gaish SC': 'EGY',
    'Haras El-Hodood SC': 'EGY',
    'Petrojet FC': 'EGY',
    'ENPPI Club': 'EGY',
    'Al Ahly': 'EGY',
    'Kazma Sporting Club': 'EGY',
    'Smouha Sporting Club': 'EGY',
    'Ghazl El-Mehalla': 'EGY',
    'El Zamalek': 'EGY',
    'Al-Masry SC': 'EGY',
    'Barnsley F.C.': 'EGY',
    'Ismaily': 'EGY',
    'PAOK F.C.': 'GRE',
    'Al Wasl FC': 'KSA',
    'Petrojet': 'EGY',
    'Gil Vicente F.C': 'POR',
    'Ittihad FC': 'KSA',
    'Galatasaray S.K. (football team)': 'TUR',
    'Cerro Largo FC': 'URU',
    'C.A. Cerro': 'URU',
    'Granada C.F.': 'ESP',
    'Puebla F.C.': 'MEX',
    'C.A. Peñarol': 'URU',
    'Club Atlético Peñarol': 'URU',
    'C.A. Bella Vista': 'URU',
    'Reggina Calcio': 'ITA',
    'Ismaily SC': 'EGY',
    'Zamalek SC': 'EGY',
    'Wadi Degla SC': 'EGY',
    'Al Ittihad Alexandria Club': 'EGY',
    'El Gouna FC': 'EGY',
    'Ghazl El Mahalla SC': 'EGY',
    'El Mokawloon SC': 'EGY',
    'Montevideo Wanderers F.C.': 'URU',
    'Club Nacional de Football': 'URU',
    'Racing Club de Montevideo': 'URU',
    'Defensor Sporting': 'URU',
    'Club Olimpia': 'PAR',
    'Liverpool F.C. (Montevideo)': 'URU',
    'Central Español': 'URU',
    'Albacete Balompié': 'ESP',
    'Club Atlético River Plate (Montevideo)': 'URU',
    'AZ Alkmaar': 'NED',
    'New York Red Bulls': 'USA',
    'VfL Bochum II': 'GER',
    'UD Salamanca': 'ESP',
    'Independiente Santa Fe': 'COL',
    'Club Santa Fe': 'COL',
    'JS Kairouan': 'TUN',
    'Lanceros Boyacá': 'COL',
    'Lierse S.K.': 'BEL',
    'FC Metalist Kharkiv': 'UKR',
    'FC Vilnius': 'LTU',
    'FC VSS Košice': 'SVK',
}
NAT_NAT_MAPPING = {'Afghanistan': 'AFG', 'Albania': 'ALB', 'Algeria': 'DZA', 'American Samoa': 'ASM', 'Andorra': 'AND',
                   'Angola': 'AGO', 'Anguilla': 'AIA', 'Antarctica': 'ATA', 'Antigua and Barbuda': 'ATG',
                   'Argentina': 'ARG', 'Armenia': 'ARM', 'Aruba': 'ABW', 'Australia': 'AUS', 'Austria': 'AUT',
                   'Azerbaijan': 'AZE', 'Bahamas': 'BHS', 'Bahrain': 'BHR', 'Bangladesh': 'BGD', 'Barbados': 'BRB',
                   'Belarus': 'BLR', 'Belgium': 'BEL', 'Belize': 'BLZ', 'Benin': 'BEN', 'Bermuda': 'BMU',
                   'Bhutan': 'BTN', 'Bolivia': 'BOL', 'Caribbean Netherlands': 'BES', 'Bosnia and Herzegovina': 'BIH',
                   'Botswana': 'BWA', 'Bouvet Island': 'BVT', 'Brazil': 'BRA', 'British Indian Ocean Territory': 'IOT',
                   'Brunei Darussalam': 'BRN', 'Bulgaria': 'BGR', 'Burkina Faso': 'BFA', 'Burundi': 'BDI',
                   'Cabo Verde': 'CPV', 'Cambodia': 'KHM', 'Cameroon': 'CMR', 'Canada': 'CAN', 'Cayman Islands': 'CYM',
                   'Central African Republic': 'CAF', 'Chad': 'TCD', 'Chile': 'CHL', 'China': 'CHN',
                   'Christmas Island': 'CXR', 'Cocos Islands': 'CCK', 'Colombia': 'COL', 'Comoros': 'COM',
                   'Congo': 'COG', 'Democratic Republic of the Congo': 'COD', 'Cook Islands': 'COK',
                   'Costa Rica': 'CRI', 'Croatia': 'HRV', 'Cuba': 'CUB', 'Cyprus': 'CYP', 'Czechia': 'CZE',
                   'Denmark': 'DNK', 'Djibouti': 'DJI', 'Dominica': 'DMA', 'Dominican Republic': 'DOM', 'England': 'ENG',
                   'Ecuador': 'ECU', 'Egypt': 'EGY', 'El Salvador': 'SLV', 'Equatorial Guinea': 'GNQ', 'Eritrea': 'ERI',
                   'Estonia': 'EST', 'Ethiopia': 'ETH', 'Falkland Islands': 'FLK', 'Faroe Islands': 'FRO',
                   'Fiji': 'FJI', 'Finland': 'FIN', 'France': 'FRA', 'French Guiana': 'GUF', 'French Polynesia': 'PYF',
                   'French Southern Territories': 'ATF', 'Gabon': 'GAB', 'Gambia': 'GMB', 'Georgia': 'GEO',
                   'Germany': 'DEU', 'Ghana': 'GHA', 'Gibraltar': 'GIB', 'Greece': 'GRC', 'Greenland': 'GRL',
                   'Grenada': 'GRD', 'Guadeloupe': 'GLP', 'Guam': 'GUM', 'Guatemala': 'GTM', 'Guernsey': 'GGY',
                   'Guinea': 'GIN', 'Guinea-Bissau': 'GNB', 'Guyana': 'GUY', 'Haiti': 'HTI',
                   'Heard Island and McDonald Islands': 'HMD', 'Vatican City': 'VAT', 'Honduras': 'HND',
                   'Hong Kong': 'HKG', 'Hungary': 'HUN', 'Iceland': 'ISL', 'India': 'IND', 'Indonesia': 'IDN',
                   'Iran': 'IRN', 'Iraq': 'IRQ', 'Ireland': 'IRL', 'Isle of Man': 'IMN', 'Israel': 'ISR',
                   'Italy': 'ITA', 'Jamaica': 'JAM', 'Japan': 'JPN', 'Jersey': 'JEY', 'Jordan': 'JOR',
                   'Kazakhstan': 'KAZ', 'Kenya': 'KEN', 'Kiribati': 'KIR', 'North Korea': 'PRK', 'South Korea': 'KOR',
                   'Kuwait': 'KWT', 'Kyrgyzstan': 'KGZ', 'Laos': 'LAO', 'Latvia': 'LVA', 'Lebanon': 'LBN',
                   'Lesotho': 'LSO', 'Liberia': 'LBR', 'Libya': 'LBY', 'Liechtenstein': 'LIE', 'Lithuania': 'LTU',
                   'Luxembourg': 'LUX', 'Macao': 'MAC', 'Republic of Macedonia': 'MKD', 'Madagascar': 'MDG',
                   'Malawi': 'MWI', 'Malaysia': 'MYS', 'Maldives': 'MDV', 'Mali': 'MLI', 'Malta': 'MLT',
                   'Marshall Islands': 'MHL', 'Martinique': 'MTQ', 'Mauritania': 'MRT', 'Mauritius': 'MUS',
                   'Mayotte': 'MYT', 'Mexico': 'MEX', 'Federated States of Micronesia': 'FSM', 'Moldova': 'MDA',
                   'Monaco': 'MCO', 'Mongolia': 'MNG', 'Montenegro': 'MNE', 'Montserrat': 'MSR', 'Morocco': 'MAR',
                   'Mozambique': 'MOZ', 'Myanmar': 'MMR', 'Namibia': 'NAM', 'Nauru': 'NRU', 'Nepal': 'NPL',
                   'Netherlands': 'NLD', 'New Caledonia': 'NCL', 'New Zealand': 'NZL', 'Nicaragua': 'NIC',
                   'Niger': 'NER', 'Nigeria': 'NGA', 'Niue': 'NIU', 'Norfolk Island': 'NFK',
                   'Northern Mariana Islands': 'MNP', 'Norway': 'NOR', 'Oman': 'OMN', 'Pakistan': 'PAK', 'Palau': 'PLW',
                   'Palestine': 'PSE', 'Panama': 'PAN', 'Papua New Guinea': 'PNG', 'Paraguay': 'PRY', 'Peru': 'PER',
                   'Philippines': 'PHL', 'Pitcairn': 'PCN', 'Poland': 'POL', 'Portugal': 'PRT', 'Puerto Rico': 'PRI',
                   'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS', 'Rwanda': 'RWA',
                   'Saint Helena, Ascension and Tristan da Cunha': 'SHN', 'Saint Kitts and Nevis': 'KNA',
                   'Saint Lucia': 'LCA', 'Collectivity of Saint Martin': 'MAF', 'Saint Pierre and Miquelon': 'SPM',
                   'Saint Vincent and the Grenadines': 'VCT', 'Samoa': 'WSM', 'San Marino': 'SMR',
                   'Sao Tome and Principe': 'STP', 'Saudi Arabia': 'SAU', 'Senegal': 'SEN', 'Serbia': 'SRB',
                   'Seychelles': 'SYC', 'Sierra Leone': 'SLE', 'Singapore': 'SGP', 'Sint Maarten': 'SXM',
                   'Slovakia': 'SVK', 'Slovenia': 'SVN', 'Solomon Islands': 'SLB', 'Somalia': 'SOM',
                   'South Africa': 'ZAF', 'South Georgia and the South Sandwich Islands': 'SGS', 'South Sudan': 'SSD',
                   'Spain': 'ESP', 'Sri Lanka': 'LKA', 'Sudan': 'SDN', 'Suriname': 'SUR',
                   'Svalbard and Jan Mayen': 'SJM', 'Swaziland': 'SWZ', 'Sweden': 'SWE', 'Switzerland': 'CHE',
                   'Syria': 'SYR', 'Taiwan': 'TWN', 'Tajikistan': 'TJK', 'Tanzania': 'TZA', 'Thailand': 'THA',
                   'East Timor': 'TLS', 'Togo': 'TGO', 'Tokelau': 'TKL', 'Tonga': 'TON', 'Trinidad and Tobago': 'TTO',
                   'Tunisia': 'TUN', 'Turkey': 'TUR', 'Turkmenistan': 'TKM', 'Turks and Caicos Islands': 'TCA',
                   'Tuvalu': 'TUV', 'Uganda': 'UGA', 'Ukraine': 'UKR', 'United Arab Emirates': 'ARE',
                   'United Kingdom': 'GBR', 'United States': 'USA', 'United States Minor Outlying Islands': 'UMI',
                   'Uruguay': 'URY', 'Uzbekistan': 'UZB', 'Vanuatu': 'VUT', 'Venezuela': 'VEN', 'Vietnam': 'VNM',
                   'British Virgin Islands': 'VGB', 'United States Virgin Islands': 'VIR', 'Wallis and Futuna': 'WLF',
                   'Western Sahara': 'ESH', 'Yemen': 'YEM', 'Zambia': 'ZMB', 'Zimbabwe': 'ZWE', }


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

        redirect = re.findall('#REDIRECT ?\[\[([^\]]*)\]\]', info, re.IGNORECASE)
        if redirect:
            return get_player_detail_info(redirect[0])

        return info

    def parse_info(link, info):
        redirect = re.findall('#REDIRECT ?\[\[([^\]]*)\]\]', info, re.IGNORECASE)
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

        info = wikilib.get_page_section_content_by_priority_list(pid, ['Current squad', 'Current squads', 'Players'])

        if info is None:
            info = wikilib.get_page_content_by_id(pid)

        empty = re.findall('{{Empty section\|date[^}]*}}', info)
        if empty:
            return []

        empty = re.findall('{{cl|UD Salamanca footballers}}', info)
        if empty:
            return []

        empty = re.findall('{{See also\|:Category:[^}]*}}', info)
        if empty:
            return []

        redirect = re.findall('#REDIRECT ?\[\[([^\]]*)\]\]', info, re.IGNORECASE)
        if redirect:
            page_id = wikilib.get_page_id_by_link(redirect[0])
            return parse_team_nationality(page_id, name)

        template = re.findall('({{[^}]*}})', info)
        if 1 == len(template) and len(info) < 255:
            print(template)
            info = wikilib.parse_template(template[0])['data']['expandtemplates']['wikitext']

        nats = re.findall(r'\bnat= *([A-Z]*) *\b', info, re.IGNORECASE)
        _t = {}
        for n in nats:
            if n in _t.keys():
                _t[n] += 1
            else:
                _t[n] = 1

        if 0 == len(_t.keys()):
            _nat_values = list(set(TEAM_NAT_MAP.values()))
            nats = re.findall(r'\b(%s)\b' % '|'.join(_nat_values), info)
            _t = {}
            for n in nats:
                if n in _t.keys():
                    _t[n] += 1
                else:
                    _t[n] = 1

            nats = re.findall(r'\b(%s)\b' % '|'.join(list(NAT_NAT_MAPPING.keys())), info)
            for n in nats:
                _k = NAT_NAT_MAPPING[n]
                if _k in _t.keys():
                    _t[_k] += 1
                else:
                    _t[_k] = 1

            nats = re.findall(r'\b(%s)\b' % '|'.join(list(NAT_NAT_MAPPING.values())), info)
            for n in nats:
                if n in _t.keys():
                    _t[n] += 1
                else:
                    _t[n] = 1

        if name == 'Íþróttabandalag Akraness':
            print(_t)
        candidate = max(_t.items(), key=operator.itemgetter(1))[0] if len(_t.keys()) else None
        if candidate in NAT_NAT_MAPPING.keys():
            candidate = NAT_NAT_MAPPING[candidate]

        return candidate

    page_id = wikilib.get_page_id_by_link(link, WIKI_PLAYER_MAP)
    info = get_info(page_id, link)
    if type(info) is dict:
        return info

    if info is not None:
        info = parse_info(link, info)
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
        ys = [(int(e.strip(' ') if '' != e.strip(' ') else 2018)) for e in re.split('–|−|-|\||&', y)]
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
            ub = int(ys[1])
            _current_years = list(range(lb, ub))

            for y in _current_years:
                _result[y] = club
    years = list(_result.keys())
    clubs = list(_result.values())
    clubs = [{
        'link': club['link'],
        'name': club['name'],
        'nationality': parse_team_nationality(wikilib.get_page_id_by_link(club['link']), club['link']),  # todo
        'is_national_team': 0,
        'wiki_page_id': wikilib.get_page_id_by_link(club['link'])
    } for club in clubs]
    return {
        'wiki_page_id': page_id,
        'years': years,
        'clubs': clubs,
    }


def get_current_squad(team_page_id):
    data = wikilib.get_page_section_content_by_priority_list(team_page_id, ['Current squad', 'Current squads', 'Players'])
    print(team_page_id)
    if int(team_page_id) == 3642837:
        print(1)
    empty = re.findall('{{Empty section\|date=[^}]*}}', data)
    if empty:
        return []

    empty = re.findall('{{cl|UD Salamanca footballers}}', data)
    if empty:
        return []

    empty = re.findall('{{See also\|:Category:[^}]*}}', data)
    if empty:
        return []

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
                            r'[^\|]*\|(df=yes\|)?([1-2][0-9]*)\|([0-9]*)\|([0-9]*).*',
                            r'\2-\3-\4',
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

        if player['name'][0] == 'N':
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

        player_id = cur.lastrowid
        sql = "INSERT INTO player_to_team (player_id, team_id, season) VALUES (%d, %d, '2018-2019')"
        cur.execute(sql % (player_id, t['team_id']))

        for i, _team in enumerate(player['clubs']):
            assert_team(_team, 0, conn)
            year = player['years'][i]

            if 2018 != year:
                sql = "INSERT INTO player_to_team (player_id, team_id, season) VALUES (%d, %d, '%s')"
                cur.execute(sql % (player_id, t['team_id'], '%d-%d' % (year, year + 1)))

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
