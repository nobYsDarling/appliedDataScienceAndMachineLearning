import re
from difflib import SequenceMatcher
import fileinput


def read_team(team, display_name):
    # read file
    f = 'data/%s.csv' % team
    h = open(f, 'r', encoding='utf8')
    t = h.read().split("\n")
    h.close()

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


def read_teams(source='data'):
    # read file
    f = source + '/teams.csv'
    h = open(f, 'r', encoding='utf8')
    ts = h.read().split("\n")
    h.close()

    result = {}
    for t in ts:
        name = re.sub('^(.*) - (.*)$', '\g<1>', t)
        disp = re.sub('^(.*) - (.*)$', '\g<2>', t)

        result[name] = read_team(name, disp)

    return result


def get_clubs(teams):
    cs = []
    for t in teams:
        for p in teams[t]['players']:
            players_team = p[1]

            if players_team in [e[0] for e in cs]:
                for idx, v in enumerate(cs):
                    if v[0] == players_team:
                        cs[idx] = (cs[idx][0], cs[idx][1] + 1)
            else:
                cs.append((players_team, 1))

    return sorted(cs, key=lambda x: x[1], reverse=True)


def print_tuple_list(l):
    for a, b in l:
        print("%s: %s" % (str(a), str(b)))


# read teams
teams = read_teams()
# print(teams)
# exit(1)
clubs = get_clubs(teams)

# list clubs
print_tuple_list(clubs)
exit(1)

# test for similarities in club names
# sort out by hand - result in __team_substitutions.csv
# teams = [e[0] for e in clubs]
# for t0 in teams:
#     for t1 in teams:
#         likelihood = SequenceMatcher(None, t0, t1).ratio()
#         if t0 != t1 and 0.6 < likelihood < 0.7:
#             print("%s - %s = %f" % (t0, t1, SequenceMatcher(None, t0, t1).ratio()))
# exit(1)
# with omega = 0.8
# saved to __team_substitutions_0.csv
# reviewed tuples
# saved to __team_substitutions_1.csv
# unified to tuples of (display_name, display_name_variation)
# saved to __team_substitutions_2.csv
# substitute in files
#
# with omega = 0.7
# saved to __team_substitutions_3.csv
# reviewed tuples
# saved to __team_substitutions_4.csv
# unified to tuples of (display_name, display_name_variation)
# saved to __team_substitutions_5.csv
# substitute in files
#
# f = 'data/teams.csv'
# h = open(f, 'r', encoding='utf8')
# ts = h.read().split("\n")
# h.close()
#
# teams = []
# for t in ts:
#     name = re.sub('^(.*) - (.*)$', '\g<1>', t)
#     disp = re.sub('^(.*) - (.*)$', '\g<2>', t)
#
#     teams.append((name, disp))
#
#
# f = 'data/__team_substitutions__5.csv'
# h = open(f, 'r', encoding='utf8')
# substitutions = [l.split(' - ') for l in h.read().split("\n")]
# h.close()
# #
#
# for t in teams:
#     f = 'data/%s.csv' % t[0]
#     h = open(f, 'r', encoding='utf8')
#     ls = h.read().split("\n")
#     h.close()
#
#     result = []
#     for l in ls:
#         s = l
#         for substitution in substitutions:
#             s = re.sub('\(%s\)' % substitution[1], "(%s)" % substitution[0], s)
#         result.append(s)
#
#     f = 'data/%s.csv' % t[0]
#     h = open(f, 'w', encoding='utf8')
#     prev_empty = False
#     for l in result:
#         if l != '':
#             if prev_empty:
#                 h.write("\n")
#             prev_empty = False
#             h.write("%s\n" % l)
#
#         if l == '':
#             prev_empty = True
#
#     h.close()


