import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import sqlite3

def getPageContentParser(url) :
    # disable ssl check
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # url request
    request = urllib.request.urlopen(url , context=ctx)

    content = request.read()

    # html parser
    parser = BeautifulSoup(content, "html.parser")

    return parser

# Gibt Liste mit Startern zurück
# home==true -> Home Starter
# home==false -> Away Starter
def getStarter(parser, home) :

    if home :
        starter = parser('div', {'class' : 'hs-lineup-list hs-starter home'})[0]
    else :
        starter = parser('div', {'class' : 'hs-lineup-list hs-starter away'})[0]

    playerNames = starter('div', {'class' : 'person-name person-name-'})

    playerNameList = []
    
    for player in playerNames :
        playerNameList.append(player.a.string)

    #### debug ####
    #if (len(playerNameList) < 11) :
    #    print ('LängeFehlerStarter: ' + str(len(playerNameList)))
    #    print (playerNameList)
    ###############


    return playerNameList

# Bankspieler
# home==true -> Home Bench
# home==false -> Away Bench
def getBench(parser, home) :
    if home :
        bench = parser('div', {'class' : 'hs-lineup-list hs-bench home'})[0]
    else :
        bench = parser('div', {'class' : 'hs-lineup-list hs-bench away'})[0]

    playerNames = bench('div', {'class' : 'person-name person-name-'})

    playerNameList = []
    
    for player in playerNames :
        playerNameList.append(player.a.string)

    # Fehlerbehandlung, falls weniger als 12 auf der Bank
    while (len(playerNameList) < 12) :
        playerNameList.append(None)

    return playerNameList

# Auswechslungen: Spieler mit Minute
# (Minute, SpielerEin, SpielerAus, Team)
def getSubstitutions(parser) :
    substitutionEvents = parser('div', {'class' : 'hs-timeline-normal'})[0]('div', {'class' : re.compile('^event playing substitution.*')})

    substitutions = []
    for sub in substitutionEvents :
        substitutions.append((int(sub['data-minute']),
                              sub['data-person'],
                              sub['data-person-out'],
                              sub['data-team']))

    return substitutions
    
# gelbe oder rote Karten nach Minuten
# (Minute, Spieler, Team, Kartenart)
# Kartenart: yellow | red | yellow-red
def getCards(parser) :
    cardEvents = parser('div', {'class' : 'hs-timeline-normal'})[0]('div', {'class' : re.compile('^event card.*')})

    cards = []
    for card in cardEvents :
        cards.append((int(card['data-minute']),
                      card['data-person'],
                      card['data-team'],
                      card['data-kind']))

    return cards

# Torschützen nach Minuten
# (Minute, Schütze, Team)
def getScorer(parser) :
    goalEvents = parser('div', {'class' : 'hs-timeline-normal'})[0]('div', {'class' : re.compile('^event goal.*')})

    scorer = []
    for goal in goalEvents :
        scorer.append((int(goal['data-minute']),
                       goal['data-person'],
                       goal['data-team']))

    return scorer
    
# Date, Hometeam, Awayteam, Result
def getGameData(parser) :
    string = parser('head')[0]('title',{ 'data-react-helmet' : 'true'})[0].string
    string = re.split(' - ' , re.split(' \| ' ,string)[0])
    date = string[3]
    home = string[0]
    away = string[1]
    result = string[2]

    return [date, home, away, result]

####################################################################################################

# MatchIDs
def getMatchIDs(league, seasonSpecification, maxGameDays) :
    matchIDs = []
    for gamedayID in range(1, maxGameDays + 1) :
        parser = getPageContentParser("https://www.ran.de/datenbank/fussball/" + league + "/" + seasonSpecification + "/spieltag/md" + str(gamedayID) + "/ergebnisse-und-tabelle/")
        for gameday in parser('div', {'class' : 'hs-gameplan'})[0]('div', {'class' : re.compile('.*finished match.*')}) :
            matchIDs.append(int(gameday['ma_id']))
    
    return matchIDs

def getMatchIDsCup(league, seasonSpecification, groups, rounds) :
    matchIDs = []
    for gameday in groups :
        parser = getPageContentParser("https://www.ran.de/datenbank/fussball/" + league + "/" + seasonSpecification + "/" + gameday + "/ergebnisse-und-tabelle/")
        for gameday in parser('div', {'class' : 'hs-gameplan'})[0]('div', {'class' : re.compile('.*finished match.*')}) :
            matchIDs.append(int(gameday['ma_id']))

    for gameday in rounds :
        parser = getPageContentParser("https://www.ran.de/datenbank/fussball/" + league + "/" + seasonSpecification + "/" + gameday + "/ergebnisse/")
        for gameday in parser('div', {'class' : 'hs-gameplan'})[0]('div', {'class' : re.compile('.*finished match.*')}) :
            matchIDs.append(int(gameday['ma_id']))
    
    return matchIDs

# LineUp
# lineup: (Player1Home, ..., Player11Home, Player1Away, ..., Player11Away,
#           Bench1Home, ..., Bench12Home, Bench1Away, ..., Bench12Away)
def getGameLineUp(parser) :
    playerHome = getStarter(parser, True)
    playerAway = getStarter(parser, False)
    benchHome = getBench(parser, True)
    benchAway = getBench(parser, False)

    result = []
    for player in playerHome :
        result.append(player)
    for player in playerAway :
        result.append(player)
    for player in benchHome :
        result.append(player)
    for player in benchAway :
        result.append(player)

    #### debug ####
    #if (len(result) < 36) :
    #    print ('LängeFehler: ' + str(len(result)))
    #    print (result)
    ###############
    
    return result

####################################################################################################
    
# SQL
# game: (GameID, League, Season, (Spieltag?), Date, HomeTeam, AwayTeam, Result,
#           Scorer, Cards, Substitutions)
def addGame(table, matchID, league, season, game, conn):
    cur = conn.cursor()
    
    sql = "INSERT INTO " + table + " (GameID, League, Season, Date, HomeTeam, AwayTeam, Result) VALUES ('%d', '%s', '%s', '%s', '%s', '%s', '%s')"

    cur.execute(sql % (matchID, league, season, game[0], game[1], game[2], game[3]))
    
    conn.commit()

# lineup: (GameID, Player1Home, ..., Player11Home, Player1Away, ..., Player11Away,
#           Bench1Home, ..., Bench12Home, Bench1Away, ..., Bench12Away)
def addLineUp(table, matchID, lineup, conn):
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Player1Home, Player2Home, Player3Home, Player4Home, Player5Home, Player6Home, Player7Home, Player8Home, Player9Home, Player10Home, Player11Home, Player1Away, Player2Away, Player3Away, Player4Away, Player5Away, Player6Away, Player7Away, Player8Away, Player9Away, Player10Away, Player11Away, Bench1Home, Bench2Home, Bench3Home, Bench4Home, Bench5Home, Bench6Home, Bench7Home, Bench8Home, Bench9Home, Bench10Home, Bench11Home, Bench12Home, Bench1Away, Bench2Away, Bench3Away, Bench4Away, Bench5Away, Bench6Away, Bench7Away, Bench8Away, Bench9Away, Bench10Away, Bench11Away, Bench12Away) VALUES ('%d', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"

    cur.execute(sql % (matchID, lineup[0], lineup[1], lineup[2], lineup[3], lineup[4], lineup[5],
                       lineup[6], lineup[7], lineup[8], lineup[9], lineup[10], lineup[11], lineup[12],
                       lineup[13], lineup[14], lineup[15], lineup[16], lineup[17], lineup[18], lineup[19],
                       lineup[20], lineup[21], lineup[22], lineup[23], lineup[24], lineup[25], lineup[26],
                       lineup[27], lineup[28], lineup[29], lineup[30], lineup[31], lineup[32], lineup[33],
                       lineup[34], lineup[35], lineup[36], lineup[37], lineup[38], lineup[39], lineup[40],
                       lineup[41], lineup[42], lineup[43], lineup[44], lineup[45]))
    conn.commit()

# scorer: (GameID, Minute, Scorer, Team)
def addScorer(table, matchID, scorer, conn) :
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Minute, Scorer, Team) VALUES ('%d', '%d', '%s', '%s')"

    for oneScorer in scorer :
        (minute, name, team) = oneScorer
        cur.execute(sql % (matchID, minute, name, team))
    
    conn.commit()

# cards: (GameID, Minute, Player, Team, Card)
def addCards(table, matchID, cards, conn) :
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Minute, Player, Team, Card) VALUES ('%d', '%d', '%s', '%s', '%s')"

    for player in cards :
        (minute, name, team, card) = player
        cur.execute(sql % (matchID, minute, name, team, card))
    
    conn.commit()
    
# substitutions: (GameID, Minute, PlayerIn, PlayerOut, Team)
def addSubstitutions(table, matchID, substitutions, conn) :
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Minute, PlayerIn, PlayerOut, Team) VALUES ('%d', '%d', '%s', '%s', '%s')"

    for sub in substitutions :
        (minute, pin, pout, team) = sub
        cur.execute(sql % (matchID, minute, pin, pout, team))
    
    conn.commit()
    
# fill all tables for league and season
def fillLeague(league, season, seasonSpecification, maxGameDays, conn) :
    zusatz = "/aufstellung/"
    if (league.lower() in ['sueper-lig', 'eredivisie', 'premier-liga', 'primeira-liga', 'superleague', 'aut-bundesliga', 'super-league', 'bra-serie-a', 'arg-primera-division']) :
        zusatz = "/spieldetails/"
    
    print ('Start gathering MatchIDs...')
    matchIDs = getMatchIDs(league.lower(), seasonSpecification, maxGameDays)
    print ('MatchID gathering completed.')
        
    for matchID in matchIDs:
        url = "https://www.ran.de/datenbank/fussball/" + league.lower() + "/ma" + str(matchID) + zusatz
        parser = getPageContentParser(url)

        game = getGameData(parser)
        lineup = getGameLineUp(parser)
        scorer = getScorer(parser)
        cards = getCards(parser)
        substitutions = getSubstitutions(parser)

        league = league.replace('-', '')
        seasonSplit = re.split('-', season)
        preTable = league.lower() + seasonSplit[0] + seasonSplit[1]
    
        print('Add GameData.')
        table1 = preTable +"gamedata"
        addGame(table1, matchID, league, season, game, conn)
        print('Add LineUp.')
        table2 = preTable + "lineup"
        addLineUp(table2, matchID, lineup, conn)
        print('Add Scorer.')
        table3 = preTable + "scorer"
        addScorer(table3, matchID, scorer, conn)
        print('Add Cards.')
        table4 = preTable + "cards"
        addCards(table4, matchID, cards, conn)
        print('Add Substitutions.')
        table5 = preTable + "substitutions"
        addSubstitutions(table5, matchID, substitutions, conn)

# fill all tables for cup and season
def fillCup(league, season, seasonSpecification, groups, rounds, conn) :
    zusatz = "/aufstellung/"
    if (league.lower() in ['klub-wm', 'afrika-cup', 'freundschaft', 'copa-america', 'copa-libertadores']) :
        zusatz = "/spieldetails/"

    print ('Start gathering MatchIDs...')
    matchIDs = getMatchIDs(league.lower(), seasonSpecification, groups, rounds)
    print ('MatchID gathering completed.')
        
    for matchID in matchIDs:
        url = "https://www.ran.de/datenbank/fussball/" + league.lower() + "/ma" + str(matchID) + zusatz
        parser = getPageContentParser(url)

        game = getGameData(parser)
        lineup = getGameLineUp(parser)
        scorer = getScorer(parser)
        cards = getCards(parser)
        substitutions = getSubstitutions(parser)

        league = league.replace('-', '')
        preTable = league.lower() + season
    
        print('Add GameData.')
        table1 = preTable +"gamedata"
        addGame(table1, matchID, league, season, game, conn)
        print('Add LineUp.')
        table2 = preTable + "lineup"
        addLineUp(table2, matchID, lineup, conn)
        print('Add Scorer.')
        table3 = preTable + "scorer"
        addScorer(table3, matchID, scorer, conn)
        print('Add Cards.')
        table4 = preTable + "cards"
        addCards(table4, matchID, cards, conn)
        print('Add Substitutions.')
        table5 = preTable + "substitutions"
        addSubstitutions(table5, matchID, substitutions, conn)
        
# delete and create new: all tables for league and season
def renewLigue(league, season, conn) :
    cur = conn.cursor()

    league = league.replace('-', '')

    preTable = ""
    seasonSplit = re.split('-', season)
    if (len(seasonSplit) == 1) :
        preTable = league.lower() + seasonSplit[0]
    else :
        preTable = league.lower() + seasonSplit[0] + seasonSplit[1]

    table1 = preTable +"gamedata"
    table2 = preTable + "lineup"
    table3 = preTable + "scorer"
    table4 = preTable + "cards"
    table5 = preTable + "substitutions"

    cur.execute("DROP TABLE IF EXISTS " + table1)
    cur.execute("DROP TABLE IF EXISTS " + table2)
    cur.execute("DROP TABLE IF EXISTS " + table3)
    cur.execute("DROP TABLE IF EXISTS " + table4)
    cur.execute("DROP TABLE IF EXISTS " + table5)
                
    cur.execute("CREATE TABLE " + table1 + " (GameID, League, Season, Date, HomeTeam, AwayTeam, Result)")
    cur.execute("CREATE TABLE " + table2 + " (GameID, Player1Home, Player2Home, Player3Home, Player4Home, Player5Home, Player6Home, Player7Home, Player8Home, Player9Home, Player10Home, Player11Home, Player1Away, Player2Away, Player3Away, Player4Away, Player5Away, Player6Away, Player7Away, Player8Away, Player9Away, Player10Away, Player11Away, Bench1Home, Bench2Home, Bench3Home, Bench4Home, Bench5Home, Bench6Home, Bench7Home, Bench8Home, Bench9Home, Bench10Home, Bench11Home, Bench12Home, Bench1Away, Bench2Away, Bench3Away, Bench4Away, Bench5Away, Bench6Away, Bench7Away, Bench8Away, Bench9Away, Bench10Away, Bench11Away, Bench12Away)")
    cur.execute("CREATE TABLE " + table3 + " (GameID, Minute, Scorer, Team)")
    cur.execute("CREATE TABLE " + table4 + " (GameID, Minute, Player, Team, Card)")
    cur.execute("CREATE TABLE " + table5 + " (GameID, Minute, PlayerIn, PlayerOut, Team)")


    conn.commit()

####################################################################################################

# Data import
conn = sqlite3.connect('fifaLeagueGames.db')

####################### BUNDESLIGA #######################

# Bundesliga 2012-2013
renewLigue('Bundesliga', '2012-2013', conn)
print('Start gathering Bundesliga 12/13...')
fillLeague('Bundesliga', '2012-2013', 'se9024/2012-2013/ro29872', 34, conn)
print('Gathering Bundesliga 12/13 done.')

# Bundesliga 2013-2014
renewLigue('Bundesliga', '2013-2014', conn)
print('Start gathering Bundesliga 13/14...')
fillLeague('Bundesliga', '2013-2014', 'se11976/2013-2014/ro38889', 34, conn)
print('Gathering Bundesliga 13/14 done.')

# Bundesliga 2014-2015
renewLigue('Bundesliga', '2014-2015', conn)
print('Start gathering Bundesliga 14/15...')
fillLeague('Bundesliga', '2014-2015', 'se15388/2014-2015/ro47269', 34, conn)
print('Gathering Bundesliga 14/15 done.')

# Bundesliga 2015-2016
renewLigue('Bundesliga', '2015-2016', conn)
print('Start gathering Bundesliga 15/16...')
fillLeague('Bundesliga', '2015-2016', 'se18336/2015-2016/ro57041', 34, conn)
print('Gathering Bundesliga 15/16 done.')

# Bundesliga 2016-2017
renewLigue('Bundesliga', '2016-2017', conn)
print('Start gathering Bundesliga 16/17...')
fillLeague('Bundesliga', '2016-2017', 'se20812/2016-2017/ro63882', 34, conn)
print('Gathering Bundesliga 16/17 done.')

# Bundesliga 2017-2018
renewLigue('Bundesliga', '2017-2018', conn)
print('Start gathering Bundesliga 17/18...')
fillLeague('Bundesliga', '2017-2018', 'se23906/2017-2018/ro73072', 34, conn)
print('Gathering Bundesliga 17/18 done.')

####################### PREMIER LEAGUE #######################

# Premier League 2012-2013
renewLigue('Premier-League', '2012-2013', conn)
print('Start gathering Premier League 12/13...')
fillLeague('Premier-League', '2012-2013', 'se9032/2012-2013/ro29915', 38, conn)
print('Gathering Premier League 12/13 done.')

# Premier League 2013-2014
renewLigue('Premier-League', '2013-2014', conn)
print('Start gathering Premier League 13/14...')
fillLigue('Premier-League', '2013-2014', 'se11979/2013-2014/ro38892', 38, conn)
print('Gathering Premier League 13/14 done.')

# Premier League 2014-2015
renewLigue('Premier-League', '2014-2015', conn)
print('Start gathering Premier League 14/15...')
fillLeague('Premier-League', '2014-2015', 'se15390/2014-2015/ro47271', 38, conn)
print('Gathering Premier League 14/15 done.')

# Premier League 2015-2016
renewLigue('Premier-League', '2015-2016', conn)
print('Start gathering Premier League 15/16...')
fillLeague('Premier-League', '2015-2016', 'se18350/2015-2016/ro57071', 38, conn)
print('Gathering Premier League 15/16 done.')

# Premier League 2016-2017
renewLigue('Premier-League', '2016-2017', conn)
print('Start gathering Premier League 16/17...')
fillLeague('Premier-League', '2016-2017', 'se20827/2016-2017/ro63945', 38, conn)
print('Gathering Premier League 16/17 done.')

# Premier League 2017-2018
renewLigue('Premier-League', '2017-2018', conn)
print('Start gathering Premier League 17/18...')
fillLeague('Premier-League', '2017-2018', 'se23911/2017-2018/ro73079', 38, conn)
print('Gathering Premier League 17/18 done.')

####################### PRIMERA DIVISION #######################

# Primera Division 2012-2013
renewLigue('Primera-Division', '2012-2013', conn)
print('Start gathering Primera Division 12/13...')
fillLeague('Primera-Division', '2012-2013', 'se9034/2012-2013/ro29917', 38, conn)
print('Gathering Primera Division 12/13 done.')

# Primera Division 2013-2014
renewLigue('Primera-Division', '2013-2014', conn)
print('Start gathering Primera Division 13/14...')
fillLeague('Primera-Division', '2013-2014', 'se11980/2013-2014/ro38893', 38, conn)
print('Gathering Primera Division 13/14 done.')

# Primera Division 2014-2015
renewLigue('Primera-Division', '2014-2015', conn)
print('Start gathering Primera Division 14/15...')
fillLigue('Primera-Division', '2014-2015', 'se15380/2014-2015/ro47268', 38, conn)
print('Gathering Primera Division 14/15 done.')

# Primera Division 2015-2016
renewLigue('Primera-Division', '2015-2016', conn)
print('Start gathering Primera Division 15/16...')
fillLeague('Primera-Division', '2015-2016', 'se18343/2015-2016/ro57057', 38, conn)
print('Gathering Primera Division 15/16 done.')

# Primera Division 2016-2017
renewLigue('Primera-Division', '2016-2017', conn)
print('Start gathering Primera Division 16/17...')
fillLeague('Primera-Division', '2016-2017', 'se20829/2016-2017/ro63947', 38, conn)
print('Gathering Primera Division 16/17 done.')

# Primera Division 2017-2018
renewLigue('Primera-Division', '2017-2018', conn)
print('Start gathering Primera Division 17/18...')
fillLeague('Primera-Division', '2017-2018', 'se23902/2017-2018/ro73064', 38, conn)
print('Gathering Primera Division 17/18 done.')

####################### LIGUE 1 #######################

# Ligue 1 2012-2013
renewLigue('Ligue-1', '2012-2013', conn)
print('Start gathering Ligue 1 12/13...')
fillLeague('Ligue-1', '2012-2013', 'se9060/2012-2013/ro29987', 38, conn)
print('Gathering Ligue 1 12/13 done.')

# Ligue 1 2013-2014
renewLigue('Ligue-1', '2013-2014', conn)
print('Start gathering Ligue 1 13/14...')
fillLeague('Ligue-1', '2013-2014', 'se11983/2013-2014/ro38897', 38, conn)
print('Gathering Ligue 1 13/14 done.')

# Ligue 1 2014-2015
renewLigue('Ligue-1', '2014-2015', conn)
print('Start gathering Ligue 1 14/15...')
fillLeague('Ligue-1', '2014-2015', 'se15486/2014-2015/ro47531', 38, conn)
print('Gathering Ligue 1 14/15 done.')

# Ligue 1 2015-2016
renewLigue('Ligue-1', '2015-2016', conn)
print('Start gathering Ligue 1 15/16...')
fillLeague('Ligue-1', '2015-2016', 'se18352/2015-2016/ro57075', 38, conn)
print('Gathering Ligue 1 15/16 done.')

# Ligue 1 2016-2017
renewLigue('Ligue-1', '2016-2017', conn)
print('Start gathering Ligue 1 16/17...')
fillLeague('Ligue-1', '2016-2017', 'se20831/2016-2017/ro63949', 38, conn)
print('Gathering Ligue 1 16/17 done.')

# Ligue 1 2017-2018
renewLigue('Ligue-1', '2017-2018', conn)
print('Start gathering Ligue 1 17/18...')
fillLeague('Ligue-1', '2017-2018', 'se23908/2017-2018/ro73075', 38, conn)
print('Gathering Ligue 1 17/18 done.')

####################### SERIE A #######################

# Serie A 2012-2013
renewLigue('Serie-A', '2012-2013', conn)
print('Start gathering Serie A 12/13...')
fillLeague('Serie-A', '2012-2013', 'se9033/2012-2013/ro29916', 38, conn)
print('Gathering Serie A 12/13 done.')

# Serie A 2013-2014
renewLigue('Serie-A', '2013-2014', conn)
print('Start gathering Serie A 13/14...')
fillLeague('Serie-A', '2013-2014', 'se11981/2013-2014/ro38894', 38, conn)
print('Gathering Serie A 13/14 done.')

# Serie A 2014-2015
renewLigue('Serie-A', '2014-2015', conn)
print('Start gathering Serie A 14/15...')
fillLeague('Serie-A', '2014-2015', 'se15391/2014-2015/ro47272', 38, conn)
print('Gathering Serie A 14/15 done.')

# Serie A 2015-2016
renewLigue('Serie-A', '2015-2016', conn)
print('Start gathering Serie A 15/16...')
fillLeague('Serie-A', '2015-2016', 'se18351/2015-2016/ro57074', 38, conn)
print('Gathering Serie A 15/16 done.')

# Serie A 2016-2017
renewLigue('Serie-A', '2016-2017', conn)
print('Start gathering Serie A 16/17...')
fillLeague('Serie-A', '2016-2017', 'se20830/2016-2017/ro63948', 38, conn)
print('Gathering Serie A 16/17 done.')

# Serie A 2017-2018
renewLigue('Serie-A', '2017-2018', conn)
print('Start gathering Serie A 17/18...')
fillLeague('Serie-A', '2017-2018', 'se23947/2017-2018/ro73211', 38, conn)
print('Gathering Serie A 17/18 done.')

####################### SÜPERLIG #######################

# Süper Lig 2012-2013
renewLigue('Sueper-Lig', '2012-2013', conn)
print('Start gathering Süper Lig 12/13...')
fillLeague('Sueper-Lig', '2012-2013', 'se9037/2012-2013/ro29924', 34, conn)
print('Gathering Süper Lig 12/13 done.')

# Süper Lig 2013-2014
renewLigue('Sueper-Lig', '2013-2014', conn)
print('Start gathering Süper Lig 13/14...')
fillLeague('Sueper-Lig', '2013-2014', 'se11982/2013-2014/ro38896', 34, conn)
print('Gathering Süper Lig 13/14 done.')

# Süper Lig 2014-2015
renewLigue('Sueper-Lig', '2014-2015', conn)
print('Start gathering Süper Lig 14/15...')
fillLeague('Sueper-Lig', '2014-2015', 'se15700/2014-2015/ro48154', 34, conn)
print('Gathering Süper Lig 14/15 done.')

# Süper Lig 2015-2016
renewLigue('Sueper-Lig', '2015-2016', conn)
print('Start gathering Süper Lig 15/16...')
fillLeague('Sueper-Lig', '2015-2016', 'se18486/2015-2016/ro57289', 34, conn)
print('Gathering Süper Lig 15/16 done.')

# Süper Lig 2016-2017
renewLigue('Sueper-Lig', '2016-2017', conn)
print('Start gathering Süper Lig 16/17...')
fillLeague('Sueper-Lig', '2016-2017', 'se20839/2016-2017/ro63964', 34, conn)
print('Gathering Süper Lig 16/17 done.')

# Süper Lig 2017-2018
renewLigue('Sueper-Lig', '2017-2018', conn)
print('Start gathering Süper Lig 17/18...')
fillLeague('Sueper-Lig', '2017-2018', 'se23921/2017-2018/ro73096', 34, conn)
print('Gathering Süper Lig 17/18 done.')

####################### EREDIVISIE #######################

# Eredivisie 2012-2013
renewLigue('Eredivisie', '2012-2013', conn)
print('Start gathering Eredivisie 12/13...')
fillLeague('Eredivisie', '2012-2013', 'se9045/2012-2013/ro29934', 34, conn)
print('Gathering Eredivisie 12/13 done.')

# Eredivisie 2013-2014
renewLigue('Eredivisie', '2013-2014', conn)
print('Start gathering Eredivisie 13/14...')
fillLeague('Eredivisie', '2013-2014', 'se11984/2013-2014/ro38898', 34, conn)
print('Gathering Eredivisie 13/14 done.')

# Eredivisie 2014-2015
renewLigue('Eredivisie', '2014-2015', conn)
print('Start gathering Eredivisie 14/15...')
fillLeague('Eredivisie', '2014-2015', 'se15420/2014-2015/ro47362', 34, conn)
print('Gathering Eredivisie 14/15 done.')

# Eredivisie 2015-2016
renewLigue('Eredivisie', '2015-2016', conn)
print('Start gathering Eredivisie 15/16...')
fillLeague('Eredivisie', '2015-2016', 'se18491/2015-2016/ro57308', 34, conn)
print('Gathering Eredivisie 15/16 done.')

# Eredivisie 2016-2017
renewLigue('Eredivisie', '2016-2017', conn)
print('Start gathering Eredivisie 16/17...')
fillLeague('Eredivisie', '2016-2017', 'se20909/2016-2017/ro64172', 34, conn)
print('Gathering Eredivisie 16/17 done.')

# Eredivisie 2017-2018
renewLigue('Eredivisie', '2017-2018', conn)
print('Start gathering Eredivisie 17/18...')
fillLeague('Eredivisie', '2017-2018', 'se23927/2017-2018/ro73164', 34, conn)
print('Gathering Eredivisie 17/18 done.')

####################### PREMIER LIGA #######################

# Premier Liga 2012-2013
renewLigue('Premier-Liga', '2012-2013', conn)
print('Start gathering Premier Liga 12/13...')
fillLeague('Premier-Liga', '2012-2013', 'se9064/2012-2013/ro29996', 30, conn)
print('Gathering Premier Liga 12/13 done.')

# Premier Liga 2013-2014
renewLigue('Premier-Liga', '2013-2014', conn)
print('Start gathering Premier Liga 13/14...')
fillLeague('Premier-Liga', '2013-2014', 'se12008/2013-2014/ro39206', 30, conn)
print('Gathering Premier Liga 13/14 done.')

# Premier Liga 2014-2015
renewLigue('Premier-Liga', '2014-2015', conn)
print('Start gathering Premier Liga 14/15...')
fillLeague('Premier-Liga', '2014-2015', 'se15398/2014-2015/ro47298', 30, conn)
print('Gathering Premier Liga 14/15 done.')

# Premier Liga 2015-2016
renewLigue('Premier-Liga', '2015-2016', conn)
print('Start gathering Premier Liga 15/16...')
fillLeague('Premier-Liga', '2015-2016', 'se18485/2015-2016/ro57288', 30, conn)
print('Gathering Premier Liga 15/16 done.')

# Premier Liga 2016-2017
renewLigue('Premier-Liga', '2016-2017', conn)
print('Start gathering Premier Liga 16/17...')
fillLeague('Premier-Liga', '2016-2017', 'se20908/2016-2017/ro64171', 30, conn)
print('Gathering Premier Liga 16/17 done.')

# Premier Liga 2017-2018
renewLigue('Premier-Liga', '2017-2018', conn)
print('Start gathering Premier Liga 17/18...')
fillLeague('Premier-Liga', '2017-2018', 'se23914/2017-2018/ro73082', 30, conn)
print('Gathering Premier Liga 17/18 done.')

####################### PRIMEIRA LIGA #######################

# Primeira Liga 2012-2013
renewLigue('Primeira-Liga', '2012-2013', conn)
print('Start gathering Primeira Liga 12/13...')
fillLeague('Primeira-Liga', '2012-2013', 'se9035/2012-2013/ro29921', 30, conn)
print('Gathering Primeira Liga 12/13 done.')

# Primeira Liga 2013-2014
renewLigue('Primeira-Liga', '2013-2014', conn)
print('Start gathering Primeira Liga 13/14...')
fillLeague('Primeira-Liga', '2013-2014', 'se11988/2013-2014/ro39148', 30, conn)
print('Gathering Primeira Liga 13/14 done.')

# Primeira Liga 2014-2015
renewLigue('Primeira-Liga', '2014-2015', conn)
print('Start gathering Primeira Liga 14/15...')
fillLeague('Primeira-Liga', '2014-2015', 'se15397/2014-2015/ro47297', 34, conn)
print('Gathering Primeira Liga 14/15 done.')

# Primeira Liga 2015-2016
renewLigue('Primeira-Liga', '2015-2016', conn)
print('Start gathering Primeira Liga 15/16...')
fillLeague('Primeira-Liga', '2015-2016', 'se18442/2015-2016/ro57198', 34, conn)
print('Gathering Primeira Liga 15/16 done.')

# Primeira Liga 2016-2017
renewLigue('Primeira-Liga', '2016-2017', conn)
print('Start gathering Primeira Liga 16/17...')
fillLeague('Primeira-Liga', '2016-2017', 'se20840/2016-2017/ro63965', 34, conn)
print('Gathering Primeira Liga 16/17 done.')

# Primeira Liga 2017-2018
renewLigue('Primeira-Liga', '2017-2018', conn)
print('Start gathering Primeira Liga 17/18...')
fillLeague('Primeira-Liga', '2017-2018', 'se23910/2017-2018/ro73078', 34, conn)
print('Gathering Primeira Liga 17/18 done.')

####################### SUPERLEAGUE #######################

# Superleague 2012-2013
renewLigue('Superleague', '2012-2013', conn)
print('Start gathering Superleague 12/13...')
fillLeague('Superleague', '2012-2013', 'se9379/2012-2013/ro31060', 30, conn)
print('Gathering Superleague 12/13 done.')

# Superleague 2013-2014
renewLigue('Superleague', '2013-2014', conn)
print('Start gathering Superleague 13/14...')
fillLeague('Superleague', '2013-2014', 'se11999/2013-2014/ro39168', 34, conn)
print('Gathering Superleague 13/14 done.')

# Superleague 2014-2015
renewLigue('Superleague', '2014-2015', conn)
print('Start gathering Superleague 14/15...')
fillLeague('Superleague', '2014-2015', 'se15430/2014-2015/ro47401', 34, conn)
print('Gathering Superleague 14/15 done.')

# Superleague 2015-2016
renewLigue('Superleague', '2015-2016', conn)
print('Start gathering Superleague 15/16...')
fillLeague('Superleague', '2015-2016', 'se18776/2015-2016/ro57980', 30, conn)
print('Gathering Superleague 15/16 done.')

# Superleague 2016-2017
renewLigue('Superleague', '2016-2017', conn)
print('Start gathering Superleague 16/17...')
fillLeague('Superleague', '2016-2017', 'se21892/2016-2017/ro67396', 30, conn)
print('Gathering Superleague 16/17 done.')

# Superleague 2017-2018
renewLigue('Superleague', '2017-2018', conn)
print('Start gathering Superleague 17/18...')
fillLeague('Superleague', '2017-2018', 'se24483/2017-2018/ro74455', 30, conn)
print('Gathering Superleague 17/18 done.')

####################### BUNDESLIGA (AUT) #######################

# AUT-Bundesliga 2012-2013
renewLigue('AUT-Bundesliga', '2012-2013', conn)
print('Start gathering AUT-Bundesliga 12/13...')
fillLeague('AUT-Bundesliga', '2012-2013', 'se9067/2012-2013/ro30004', 36, conn)
print('Gathering AUT-Bundesliga 12/13 done.')

# AUT-Bundesliga 2013-2014
renewLigue('AUT-Bundesliga', '2013-2014', conn)
print('Start gathering AUT-Bundesliga 13/14...')
fillLeague('AUT-Bundesliga', '2013-2014', 'se12201/2013-2014/ro39681', 36, conn)
print('Gathering AUT-Bundesliga 13/14 done.')

# AUT-Bundesliga 2014-2015
renewLigue('AUT-Bundesliga', '2014-2015', conn)
print('Start gathering AUT-Bundesliga 14/15...')
fillLeague('AUT-Bundesliga', '2014-2015', 'se15414/2014-2015/ro47334', 36, conn)
print('Gathering AUT-Bundesliga 14/15 done.')

# AUT-Bundesliga 2015-2016
renewLigue('AUT-Bundesliga', '2015-2016', conn)
print('Start gathering AUT-Bundesliga 15/16...')
fillLeague('AUT-Bundesliga', '2015-2016', 'se18367/2015-2016/ro57100', 36, conn)
print('Gathering AUT-Bundesliga 15/16 done.')

# AUT-Bundesliga 2016-2017
renewLigue('AUT-Bundesliga', '2016-2017', conn)
print('Start gathering AUT-Bundesliga 16/17...')
fillLeague('AUT-Bundesliga', '2016-2017', 'se20896/2016-2017/ro64092', 36, conn)
print('Gathering AUT-Bundesliga 16/17 done.')

# AUT-Bundesliga 2017-2018
renewLigue('AUT-Bundesliga', '2017-2018', conn)
print('Start gathering AUT-Bundesliga 17/18...')
fillLeague('AUT-Bundesliga', '2017-2018', 'se23922/2017-2018/ro73105', 36, conn)
print('Gathering AUT-Bundesliga 17/18 done.')

####################### SUPER LEAGUE #######################

# Super League 2012-2013
renewLigue('Super-League', '2012-2013', conn)
print('Start gathering Super League 12/13...')
fillLeague('Super-League', '2012-2013', 'se9080/2012-2013/ro30038', 36, conn)
print('Gathering Super League 12/13 done.')

# Super League 2013-2014
renewLigue('Super-League', '2013-2014', conn)
print('Start gathering Super League 13/14...')
fillLeague('Super-League', '2013-2014', 'se12441/2013-2014/ro40203', 36, conn)
print('Gathering Super League 13/14 done.')

# Super League 2014-2015
renewLigue('Super-League', '2014-2015', conn)
print('Start gathering Super League 14/15...')
fillLeague('Super-League', '2014-2015', 'se15417/2014-2015/ro47342', 36, conn)
print('Gathering Super League 14/15 done.')

# Super League 2015-2016
renewLigue('Super-League', '2015-2016', conn)
print('Start gathering Super League 15/16...')
fillLeague('Super-League', '2015-2016', 'se18372/2015-2016/ro57107', 36, conn)
print('Gathering Super League 15/16 done.')

# Super League 2016-2017
renewLigue('Super-League', '2016-2017', conn)
print('Start gathering Super League 16/17...')
fillLeague('Super-League', '2016-2017', 'se20904/2016-2017/ro64135', 36, conn)
print('Gathering Super League 16/17 done.')

# Super League 2017-2018
renewLigue('Super-League', '2017-2018', conn)
print('Start gathering Super League 17/18...')
fillLeague('Super-League', '2017-2018', 'se23964/2017-2018/ro73253', 36, conn)
print('Gathering Super League 17/18 done.')

####################### SERIE A (BRA) #######################

# Serie A (Bra) 2013
renewLigue('bra-serie-a', '2012-2013', conn)
print('Start gathering Serie A (Bra) 12/13...')
fillLeague('bra-serie-a', '2012-2013', 'se11745/2013/ro37283', 38, conn)
print('Gathering Serie A (Bra) 12/13 done.')

# Serie A (Bra) 2014
renewLigue('bra-serie-a', '2013-2014', conn)
print('Start gathering Serie A (Bra) 13/14...')
fillLeague('bra-serie-a', '2013-2014', 'se15244/2014/ro46270', 38, conn)
print('Gathering Serie A (Bra) 13/14 done.')

# Serie A (Bra) 2015
renewLigue('bra-serie-a', '2014-2015', conn)
print('Start gathering Serie A (Bra) 14/15...')
fillLeague('bra-serie-a', '2014-2015', 'se17882/2015/ro53454', 38, conn)
print('Gathering Serie A (Bra) 14/15 done.')

# Serie A (Bra) 2016
renewLigue('bra-serie-a', '2015-2016', conn)
print('Start gathering Serie A (Bra) 15/16...')
fillLeague('bra-serie-a', '2015-2016', 'se20604/2016/ro62844', 38, conn)
print('Gathering Serie A (Bra) 15/16 done.')

# Serie A (Bra) 2017
renewLigue('bra-serie-a', '2016-2017', conn)
print('Start gathering Serie A (Bra) 16/17...')
fillLeague('bra-serie-a', '2016-2017', 'se23494/2017/ro71637', 38, conn)
print('Gathering Serie A (Bra) 16/17 done.')

# Serie A (Bra) 2018
renewLigue('bra-serie-a', '2017-2018', conn)
print('Start gathering Serie A (Bra) 17/18...')
fillLeague('bra-serie-a', '2017-2018', 'se27727/2018/ro89861/spieltag', 11, conn)
print('Gathering Serie A (Bra) 17/18 done.')

####################### PRIMERA DIVISION (ARG) #######################

# Primera Division (Arg) 2012-2013
renewLigue('arg-primera-division', '2012-2013', conn)
print('Start gathering Primera Division (Arg) 12/13...')
fillLeague('arg-primera-division', '2012-2013', 'se9356/2012-2013-torneo-inicial/ro30979', 19, conn)
print('Gathering Primera Division (Arg) 12/13 done.')

# Primera Division (Arg) 2012-2013
renewLigue('arg-primera-division', '2012-2013', conn)
print('Start gathering Primera Division (Arg) 12/13...')
fillLeague('arg-primera-division', '2012-2013', 'se9357/2012-2013-torneo-final/ro30980', 19, conn)
print('Gathering Primera Division (Arg) 12/13 done.')

# Primera Division (Arg) 2013-2014
renewLigue('arg-primera-division', '2013-2014', conn)
print('Start gathering Primera Division (Arg) 13/14...')
fillLeague('arg-primera-division', '2013-2014', 'se12991/2013-2014-torneo-inicial/ro41830', 19, conn)
print('Gathering Primera Division (Arg) 13/14 done.')


# Primera Division (Arg) 2013-2014
renewLigue('arg-primera-division', '2013-2014', conn)
print('Start gathering Primera Division (Arg) 13/14...')
fillLeague('arg-primera-division', '2013-2014', 'se15003/2013-2014-torneo-final/ro45354', 19, conn)
print('Gathering Primera Division (Arg) 13/14 done.')

# Primera Division (Arg) 2014-2015
renewLigue('arg-primera-division', '2014-2015', conn)
print('Start gathering Primera Division (Arg) 14/15...')
fillLeague('arg-primera-division', '2014-2015', 'se15595/2014-2015-torneo-inicial/ro47866', 19, conn)
print('Gathering Primera Division (Arg) 14/15 done.')

# Primera Division (Arg) 2015
renewLigue('arg-primera-division', '2014-2015', conn)
print('Start gathering Primera Division (Arg) 2015...')
fillLeague('arg-primera-division', '2014-2015', 'se16954/2015/ro51734', 30, conn)
print('Gathering Primera Division (Arg) 2015 done.')

# Primera Division (Arg) 2016
renewLigue('arg-primera-division', '2015-2016', conn)
print('Start gathering Primera Division (Arg) 2016...')
fillLeague('arg-primera-division', '2015-2016', 'se20036/2016/ro61044', 16, conn)
print('Gathering Primera Division (Arg) 2016 done.')

# Primera Division (Arg) 2016-2017
renewLigue('arg-primera-division', '2016-2017', conn)
print('Start gathering Primera Division (Arg) 16/17...')
fillLeague('arg-primera-division', '2016-2017', 'se21890/2016-2017/ro67353', 30, conn)
print('Gathering Primera Division (Arg) 16/17 done.')

# Primera Division (Arg) 2017-2018
renewLigue('arg-primera-division', '2017-2018', conn)
print('Start gathering Primera Division (Arg) 17/18...')
fillLeague('arg-primera-division', '2017-2018', 'se24540/2017-2018/ro74633', 27, conn)
print('Gathering Primera Division (Arg) 17/18 done.')

####################### BUNDESLIGA #######################

# Bundesliga 2012-2013
renewLigue('Bundesliga', '2012-2013', conn)
print('Start gathering Bundesliga 12/13...')
fillLeague('Bundesliga', '2012-2013', 'se9024/2012-2013/ro29872', 34, conn)
print('Gathering Bundesliga 12/13 done.')

# Bundesliga 2013-2014
renewLigue('Bundesliga', '2013-2014', conn)
print('Start gathering Bundesliga 13/14...')
fillLeague('Bundesliga', '2013-2014', 'se11976/2013-2014/ro38889', 34, conn)
print('Gathering Bundesliga 13/14 done.')

# Bundesliga 2014-2015
renewLigue('Bundesliga', '2014-2015', conn)
print('Start gathering Bundesliga 14/15...')
fillLeague('Bundesliga', '2014-2015', 'se15388/2014-2015/ro47269', 34, conn)
print('Gathering Bundesliga 14/15 done.')

# Bundesliga 2015-2016
renewLigue('Bundesliga', '2015-2016', conn)
print('Start gathering Bundesliga 15/16...')
fillLeague('Bundesliga', '2015-2016', 'se18336/2015-2016/ro57041', 34, conn)
print('Gathering Bundesliga 15/16 done.')

# Bundesliga 2016-2017
renewLigue('Bundesliga', '2016-2017', conn)
print('Start gathering Bundesliga 16/17...')
fillLeague('Bundesliga', '2016-2017', 'se20812/2016-2017/ro63882', 34, conn)
print('Gathering Bundesliga 16/17 done.')

# Bundesliga 2017-2018
renewLigue('Bundesliga', '2017-2018', conn)
print('Start gathering Bundesliga 17/18...')
fillLeague('Bundesliga', '2017-2018', 'se23906/2017-2018/ro73072', 34, conn)
print('Gathering Bundesliga 17/18 done.')

####################### 2. BUNDESLIGA #######################

# 2. Bundesliga 2012-2013
renewLigue('2-Bundesliga', '2012-2013', conn)
print('Start gathering 2. Bundesliga 12/13...')
fillLeague('2-Bundesliga', '2012-2013', 'se9025/2012-2013/ro29873', 34, conn)
print('Gathering 2. Bundesliga 12/13 done.')

# 2. Bundesliga 2013-2014
renewLigue('2-Bundesliga', '2013-2014', conn)
print('Start gathering 2. Bundesliga 13/14...')
fillLeague('2-Bundesliga', '2013-2014', 'se11977/2013-2014/ro38890', 34, conn)
print('Gathering 2. Bundesliga 13/14 done.')

# 2. Bundesliga 2014-2015
renewLigue('2-Bundesliga', '2014-2015', conn)
print('Start gathering 2. Bundesliga 14/15...')
fillLeague('2-Bundesliga', '2014-2015', 'se15389/2014-2015/ro47270', 34, conn)
print('Gathering 2. Bundesliga 14/15 done.')

# 2. Bundesliga 2015-2016
renewLigue('2-Bundesliga', '2015-2016', conn)
print('Start gathering 2. Bundesliga 15/16...')
fillLeague('2-Bundesliga', '2015-2016', 'se18337/2015-2016/ro57043', 34, conn)
print('Gathering 2. Bundesliga 15/16 done.')

# 2. Bundesliga 2016-2017
renewLigue('2-Bundesliga', '2016-2017', conn)
print('Start gathering 2. Bundesliga 16/17...')
fillLeague('2-Bundesliga', '2016-2017', 'se20816/2016-2017/ro63910', 34, conn)
print('Gathering 2. Bundesliga 16/17 done.')

# 2. Bundesliga 2017-2018
renewLigue('2-Bundesliga', '2017-2018', conn)
print('Start gathering 2. Bundesliga 17/18...')
fillLeague('2-Bundesliga', '2017-2018', 'se23912/2017-2018/ro73080', 34, conn)
print('Gathering 2. Bundesliga 17/18 done.')

####################### DFB POKAL #######################

DFBGroups = []
DFBRounds= ['1-runde', '2-runde', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']

# DFB-Pokal 2012-2013
renewLigue('DFB-Pokal', '2013', conn)
print('Start gathering DFB-Pokal 12/13...')
fillCup('DFB-Pokal', '2013', 'se9167/2012-2013/ro30260', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 12/13 done.')

# DFB-Pokal 2013-2014
renewLigue('DFB-Pokal', '2014', conn)
print('Start gathering DFB-Pokal 13/14...')
fillCup('DFB-Pokal', '2014', 'se12096/2013-2014/ro39981', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 13/14 done.')

# DFB-Pokal 2014-2015
renewLigue('DFB-Pokal', '2015', conn)
print('Start gathering DFB-Pokal 14/15...')
fillCup('DFB-Pokal', '2015', 'se15490/2014-2015/ro47544', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 14/15 done.')

# DFB-Pokal 2015-2016
renewLigue('DFB-Pokal', '2016', conn)
print('Start gathering DFB-Pokal 15/16...')
fillCup('DFB-Pokal', '2016', 'se18517/2015-2016/ro57639', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 15/16 done.')

# DFB-Pokal 2016-2017
renewLigue('DFB-Pokal', '2017', conn)
print('Start gathering DFB-Pokal 16/17...')
fillCup('DFB-Pokal', '2017', 'se20914/2016-2017/ro64452', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 16/17 done.')

# DFB-Pokal 2017-2018
renewLigue('DFB-Pokal', '2018', conn)
print('Start gathering DFB-Pokal 17/18...')
fillCup('DFB-Pokal', '2018', 'se23924/2017-2018/ro73116', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 17/18 done.')

# TODO
# ANDERE POKALE: England, Spanien, Frankreich, Italien

####################### WM #######################

# WM 2014
renewLigue('WM', '2014', conn)
print('Start gathering WM 2014...')
fillCup('WM', '2014', 'se5334/2014-in-brasilien/ro25613', ['gruppe-a', 'gruppe-b', 'gruppe-c', 'gruppe-d', 'gruppe-e', 'gruppe-f', 'gruppe-g', 'gruppe-h'], ['achtelfinale', 'viertelfinale', 'halbfinale', 'spiel-um-platz-3', 'finale'], conn)
print('Gathering WM 2014 done.')

####################### EM #######################

EMGroups = ['gruppe-a', 'gruppe-b', 'gruppe-c', 'gruppe-d']
EMRounds = ['viertelfinale', 'halbfinale', 'finale']

# EM 2012
renewLigue('Europameisterschaft', '2012', conn)
print('Start gathering EM 2012...')
fillCup('Europameisterschaft', '2012', 'se5068/2012-in-polen-ukraine/ro25515', EMGroups, EMRounds, conn)
print('Gathering EM 2012 done.')

# EM 2016
renewLigue('Europameisterschaft', '2016', conn)
print('Start gathering EM 2016...')
fillCup('Europameisterschaft', '2016', 'se5836/2016-in-frankreich/ro47087', EMGroups, EMRounds, conn)
print('Gathering EM 2016 done.')

####################### AFRIKA CUP #######################

ACGroups = ['gruppe-a', 'gruppe-b', 'gruppe-c', 'gruppe-d']
ACRounds = ['viertelfinale', 'halbfinale', 'spiel-um-platz-3', 'finale']

# Afrika Cup 2015
renewLigue('Afrika-Cup', '2015', conn)
print('Start gathering Afrika Cup 2015...')
fillCup('Afrika-Cup', '2015', 'se13960/2015-aequatorialguinea/ro51525', ACGroups,ACRounds, conn)
print('Gathering Afrika Cup 2015 done.')

# Afrika Cup 2017
renewLigue('Afrika-Cup', '2017', conn)
print('Start gathering Afrika Cup 2017...')
fillCup('Afrika-Cup', '2017', 'se15251/2017-gabun/ro69396', ACGroups, ACRounds, conn)
print('Gathering Afrika Cup 2017 done.')

####################### COPA AMERICA #######################

CopaGroups = ['gruppe-a', 'gruppe-b', 'gruppe-c']
CopaGroups2 = ['gruppe-a', 'gruppe-b', 'gruppe-c', 'gruppe-d']
CopaRounds = ['viertelfinale', 'halbfinale', 'spiel-um-platz-3', 'finale']

# Copa America 2015
renewLigue('Copa-America', '2015', conn)
print('Start gathering Copa America 2015...')
fillCup('Copa-America', '2015', 'se16178/2015-in-chile/ro49756', CopaGroups, CopaRounds, conn)
print('Gathering Copa America 2015 done.')

# Copa America 2016
renewLigue('Copa-America', '2016', conn)
print('Start gathering Copa America 2016...')
fillCup('Copa-America', '2016', 'se16184/2016-in-den-usa/ro60935', CopaGroups2, CopaRounds, conn)
print('Gathering Copa America 2016 done.')

####################### FREUNDSCHAFTSSPIELE #######################

FGroups = []
FRounds2018 = ['januar', 'februar', 'maerz', 'april', 'mai', 'juni']
FRounds = ['januar', 'februar', 'maerz', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'dezember']

# Freundschaftsspiele 2013
renewLigue('freundschaft', '2013', conn)
print('Start gathering Freundschaftsspiele 2013...')
fillCup('freundschaft', '2013', 'se5815/2013/ro30678', FGroups,FRounds, conn)
print('Gathering Freundschaftsspiele 2013 done.')

# Freundschaftsspiele 2014
renewLigue('freundschaft', '2014', conn)
print('Start gathering Freundschaftsspiele 2014...')
fillCup('Afreundschaft', '2014', 'se6989/2014/ro45626', FGroups, FRounds, conn)
print('Gathering Freundschaftsspiele 2014 done.')

# Freundschaftsspiele 2015
renewLigue('freundschaft', '2015', conn)
print('Start gathering Freundschaftsspiele 2015...')
fillCup('freundschaft', '2015', 'se15297/2015/ro46848', FGroups,FRounds, conn)
print('Gathering Freundschaftsspiele 2015 done.')

# Freundschaftsspiele 2016
renewLigue('freundschaft', '2016', conn)
print('Start gathering Freundschaftsspiele 2016...')
fillCup('Afreundschaft', '2016', 'se18734/2016/ro61024', FGroups, FRounds, conn)
print('Gathering Freundschaftsspiele 2016 done.')

# Freundschaftsspiele 2017
renewLigue('freundschaft', '2017', conn)
print('Start gathering Freundschaftsspiele 2017...')
fillCup('freundschaft', '2017', 'se20806/2017/ro70394', FGroups,FRounds, conn)
print('Gathering Freundschaftsspiele 2017 done.')

# Freundschaftsspiele 2018
renewLigue('freundschaft', '2018', conn)
print('Start gathering Freundschaftsspiele 2018...')
fillCup('Afreundschaft', '2018', 'se23552/2018/ro81224', FGroups, FRounds2018, conn)
print('Gathering Freundschaftsspiele 2018 done.')

####################### CONFED CUP 2017 #######################

# Confed Cup 2017
renewLigue('Confed-Cup', '2017', conn)
print('Start gathering Confed Cup 2017...')
fillCup('Confed-Cup', '2017', 'se18688/2017-in-russland/ro58481', ['gruppe-a', 'gruppe-b'], ['halbfinale', 'spiel-um-platz-3', 'finale'], conn)
print('Gathering Confed Cup 2017 done.')

####################### DFB POKAL #######################

DFBGroups = []
DFBRounds= ['1-runde', '2-runde', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']

# DFB-Pokal 2012-2013
renewLigue('DFB-Pokal', '2013', conn)
print('Start gathering DFB-Pokal 12/13...')
fillCup('DFB-Pokal', '2013', 'se9167/2012-2013/ro30260', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 12/13 done.')

# DFB-Pokal 2013-2014
renewLigue('DFB-Pokal', '2014', conn)
print('Start gathering DFB-Pokal 13/14...')
fillCup('DFB-Pokal', '2014', 'se12096/2013-2014/ro39981', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 13/14 done.')

# DFB-Pokal 2014-2015
renewLigue('DFB-Pokal', '2015', conn)
print('Start gathering DFB-Pokal 14/15...')
fillCup('DFB-Pokal', '2015', 'se15490/2014-2015/ro47544', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 14/15 done.')

# DFB-Pokal 2015-2016
renewLigue('DFB-Pokal', '2016', conn)
print('Start gathering DFB-Pokal 15/16...')
fillCup('DFB-Pokal', '2016', 'se18517/2015-2016/ro57639', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 15/16 done.')

# DFB-Pokal 2016-2017
renewLigue('DFB-Pokal', '2017', conn)
print('Start gathering DFB-Pokal 16/17...')
fillCup('DFB-Pokal', '2017', 'se20914/2016-2017/ro64452', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 16/17 done.')

# DFB-Pokal 2017-2018
renewLigue('DFB-Pokal', '2018', conn)
print('Start gathering DFB-Pokal 17/18...')
fillCup('DFB-Pokal', '2018', 'se23924/2017-2018/ro73116', DFBGroups, DFBRounds, conn)
print('Gathering DFB-Pokal 17/18 done.')

####################### KLUB WM #######################

klubWMGroups = []
klubWMRounds = ['1-runde', '2-runde', 'halbfinale', 'spiel-um-platz-5', 'spiel-um-platz-3', 'finale']

# Klub WM 2012
renewLigue('Klub-WM', '2012', conn)
print('Start gathering Klub WM 2012...')
fillCup('Klub-WM', '2012', 'se9649/2012/ro31972', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2012 done.')

# Klub WM 2013
renewLigue('Klub-WM', '2013', conn)
print('Start gathering Klub WM 2013...')
fillCup('Klub-WM', '2013', 'se12250/2013/ro39776', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2013 done.')

# Klub WM 2014
renewLigue('Klub-WM', '2014', conn)
print('Start gathering Klub WM 2014...')
fillCup('Klub-WM', '2014', 'se15840/2014/ro48506', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2014 done.')

# Klub WM 2015
renewLigue('Klub-WM', '2015', conn)
print('Start gathering Klub WM 2015...')
fillCup('Klub-WM', '2015', 'se19062/2015/ro59491', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2015 done.')

# Klub WM 2016
renewLigue('Klub-WM', '2016', conn)
print('Start gathering Klub WM 2016...')
fillCup('Klub-WM', '2016', 'se21864/2016/ro67315', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2016 done.')

# Klub WM 2017
renewLigue('Klub-WM', '2017', conn)
print('Start gathering Klub WM 2017...')
fillCup('Klub-WM', '2017', 'se25049/2017/ro75936', klubWMGroups, klubWMRounds, conn)
print('Gathering Klub WM 2017 done.')

####################### EUROPA LEAGUE #######################

EuropaLeagueGroups = ['gruppe-a', 'gruppe-b', 'gruppe-c', 'gruppe-d', 'gruppe-e', 'gruppe-f', 'gruppe-g', 'gruppe-h', 'gruppe-i', 'gruppe-j', 'gruppe-k', 'gruppe-l']
EuropaLeagueRounds = ['2-runde', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']
EuropaLeagueRounds2 = ['sechzehntelfinale', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']

# Europa League 2012-2013
renewLigue('Europa-League', '2013', conn)
print('Start gathering Europa League 12/13...')
fillCup('Europa-League', '2013', 'se9511/2012-2013/ro31485', EuropaLeagueGroups, EuropaLeagueRounds, conn)
print('Gathering Europa League 12/13 done.')

# Europa League 2013-2014
renewLigue('Europa-League', '2014', conn)
print('Start gathering Europa League 13/14...')
fillCup('Europa-League', '2014', 'se13326/2013-2014/ro42863', EuropaLeagueGroups, EuropaLeagueRounds2, conn)
print('Gathering Europa League 13/14 done.')

# Europa League 2014-2015
renewLigue('Europa-League', '2015', conn)
print('Start gathering Europa League 14/15...')
fillCup('Europa-League', '2015', 'se15503/2014-2015/ro48731', EuropaLeagueGroups, EuropaLeagueRounds2, conn)
print('Gathering Europa League 14/15 done.')

# Europa League 2015-2016
renewLigue('Europa-League', '2016', conn)
print('Start gathering Europa League 15/16...')
fillCup('Europa-League', '2016', 'se18511/2015-2016/ro58791', EuropaLeagueGroups, EuropaLeagueRounds2, conn)
print('Gathering Europa League 15/16 done.')

# Europa League 2016-2017
renewLigue('Europa-League', '2017', conn)
print('Start gathering Europa League 16/17...')
fillCup('Europa-League', '2017', 'se21936/2016-2017/ro67568', EuropaLeagueGroups, EuropaLeagueRounds2, conn)
print('Gathering Europa League 16/17 done.')

# Europa League 2017-2018
renewLigue('Europa-League', '2018', conn)
print('Start gathering Europa League 17/18...')
fillCup('Europa-League', '2018', 'se23973/2017-2018/ro73323', EuropaLeagueGroups, EuropaLeagueRounds2, conn)
print('Gathering Europa League 17/18 done.')

####################### COPA LIBERTADORES #######################

CopaLiberGroups = ['gruppe-1', 'gruppe-2', 'gruppe-3', 'gruppe-4', 'gruppe-5', 'gruppe-6', 'gruppe-7', 'gruppe-8']
CopaLiberRounds = ['1-runde', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']
CopaLiberRounds2017 = ['1-runde', '2-runde', '3-runde', 'achtelfinale', 'viertelfinale', 'halbfinale', 'finale']
CopaLiberRounds2018 = ['1-runde', '2-runde', '3-runde']

# Copa Libertadores 2013
renewLigue('Copa-Libertadores', '2013', conn)
print('Start gathering Copa Libertadores 2013...')
fillCup('Copa-Libertadores', '2013', 'se10500/2013/ro39280', CopaLiberGroups, CopaLiberRounds, conn)
print('Gathering Copa Libertadores 2013 done.')

# Copa Libertadores 2014
renewLigue('Copa-Libertadores', '2014', conn)
print('Start gathering Copa Libertadores 2014...')
fillCup('Copa-Libertadores', '2014', 'se14916/2014/ro47360', CopaLiberGroups, CopaLiberRounds, conn)
print('Gathering Copa Libertadores 2014 done.')

# Copa Libertadores 2015
renewLigue('Copa-Libertadores', '2015', conn)
print('Start gathering Copa Libertadores 2015...')
fillCup('Copa-Libertadores', '2015', 'se16732/2015/ro57230', CopaLiberGroups, CopaLiberRounds, conn)
print('Gathering Copa Libertadores 2015 done.')

# Copa Libertadores 2016
renewLigue('Copa-Libertadores', '2016', conn)
print('Start gathering Copa Libertadores 2016...')
fillCup('Copa-Libertadores', '2016', 'se20006/2016/ro63972', CopaLiberGroups, CopaLiberRounds, conn)
print('Gathering Copa Libertadores 2016 done.')

# Copa Libertadores 2017
renewLigue('Copa-Libertadores', '2017', conn)
print('Start gathering Copa Libertadores 2017...')
fillCup('Copa-Libertadores', '2017', 'se22552/2017/ro75739', CopaLiberGroups, CopaLiberRounds2017, conn)
print('Gathering Copa Libertadores 2017 done.')

# Copa Libertadores 2018
renewLigue('Copa-Libertadores', '2018', conn)
print('Start gathering Copa Libertadores 2018...')
fillCup('Copa-Libertadores', '2018', 'se25859/2018/ro81476', CopaLiberGroups2018, CopaLiberRounds2018, conn)
print('Gathering Copa Libertadores 2018 done.')

# close connection
conn.close()
