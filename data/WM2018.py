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

    # Fehlerbehandlung falls auf der Seite keine Daten verfügbar (vereinzelte Spiele)
    while (len(playerNameList) < 11) :
        playerNameList.append(None)
        
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

    # Fehlerbehandlung falls auf der Seite keine Daten verfügbar (vereinzelte Spiele)
    if (len(string) < 4) :
        date = string[2]
        home = string[0]
        away = string[1]
        result = None
    else :
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

def getMatchIDsCup(league, seasonSpecification) :
    matchIDs = []
    parser = getPageContentParser("https://www.ran.de/datenbank/fussball/" + league + "/" + seasonSpecification + "/spielplan/")
    
    for gameday in parser('div', {'class' : 'hs-gameplan'})[0]('div', {'position' : re.compile('.*')}) :
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
        result.append(str(player).replace('\'', ''))
    for player in playerAway :
        result.append(str(player).replace('\'', ''))
    for player in benchHome :
        result.append(str(player).replace('\'', ''))
    for player in benchAway :
        result.append(str(player).replace('\'', ''))
    
    return result

####################################################################################################
    
# SQL
# game: (GameID, League, Season, (Spieltag?), Date, HomeTeam, AwayTeam, Result,
#           Scorer, Cards, Substitutions)
def addGame(table, matchID, league, season, game, conn):
    cur = conn.cursor()

    # Fehlerbehandlung falls auf der Seite keine Daten verfügbar (vereinzelte Spiele)
    while (len(game) < 4) :
        game.append(None)
    
    sql = "INSERT INTO " + table + " (GameID, League, Season, Date, HomeTeam, AwayTeam, Result) VALUES ('%d', '%s', '%s', '%s', '%s', '%s', '%s')"

    cur.execute(sql % (matchID, league, season, game[0], str(game[1]).replace('\'', ''), str(game[2]).replace('\'', ''), game[3]))
    
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
        cur.execute(sql % (matchID, minute, str(name).replace('\'', ''), str(team).replace('\'', '')))
    
    conn.commit()

# cards: (GameID, Minute, Player, Team, Card)
def addCards(table, matchID, cards, conn) :
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Minute, Player, Team, Card) VALUES ('%d', '%d', '%s', '%s', '%s')"

    for player in cards :
        (minute, name, team, card) = player
        cur.execute(sql % (matchID, minute, str(name).replace('\'', ''), str(team).replace('\'', ''), card))
    
    conn.commit()
    
# substitutions: (GameID, Minute, PlayerIn, PlayerOut, Team)
def addSubstitutions(table, matchID, substitutions, conn) :
    cur = conn.cursor()
    sql = "INSERT INTO " + table + " (GameID, Minute, PlayerIn, PlayerOut, Team) VALUES ('%d', '%d', '%s', '%s', '%s')"

    for sub in substitutions :
        (minute, pin, pout, team) = sub
        cur.execute(sql % (matchID, minute, str(pin).replace('\'', ''), str(pout).replace('\'', ''), str(team).replace('\'', '')))
    
    conn.commit()
    
# fill all tables for league and season
def fillLeague(league, season, seasonSpecification, maxGameDays, conn) :
    
    print ('Start gathering MatchIDs...')
    matchIDs = getMatchIDs(league.lower(), seasonSpecification, maxGameDays)
    print ('MatchID gathering completed.')
        
    for matchID in matchIDs:
        url = "https://www.ran.de/datenbank/fussball/" + league.lower() + "/ma" + str(matchID) + "/aufstellung/"
        parser = getPageContentParser(url)

        game = getGameData(parser)
        lineup = getGameLineUp(parser)
        scorer = getScorer(parser)
        cards = getCards(parser)
        substitutions = getSubstitutions(parser)

        if (league == "Super-League") :
            league = "suisuperleague"
            
        league = league.replace('-', '')
        seasonSplit = re.split('-', season)
        preTable = league.lower() + seasonSplit[0] + seasonSplit[1]

        if (preTable[0].isdigit()) :
            preTable = "z" + preTable
    
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
def fillCup(league, season, seasonSpecification, conn) :
    
    print ('Start gathering MatchIDs...')
    matchIDs = getMatchIDsCup(league.lower(), seasonSpecification)
    print ('MatchID gathering completed.')
    
    for matchID in matchIDs:
        url = "https://www.ran.de/datenbank/fussball/" + league.lower() + "/ma" + str(matchID) + "/aufstellung/"
        parser = getPageContentParser(url)
        
        game = getGameData(parser)
        lineup = getGameLineUp(parser)
        scorer = getScorer(parser)
        cards = getCards(parser)
        substitutions = getSubstitutions(parser)
        
        league = league.replace('-', '')
        preTable = league.lower() + season

        if (preTable[0].isdigit()) :
            preTable = "z" + preTable
    
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
def renewLeague(league, season, conn) :
    cur = conn.cursor()

    if (league == "Super-League") :
        league = "suisuperleague"
    
    league = league.replace('-', '')

    preTable = ""
    seasonSplit = re.split('-', season)
    if (len(seasonSplit) == 1) :
        preTable = league.lower() + seasonSplit[0]
    else :
        preTable = league.lower() + seasonSplit[0] + seasonSplit[1]

    if (preTable[0].isdigit()) :
        preTable = "z" + preTable

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
conn = sqlite3.connect('./fifaComplete.db')

####################### BUNDESLIGA #######################

# WM 2018
renewLeague('WM', '2018', conn)
print('Start gathering WM Vorrunde...')
fillCup('WM', '2018', 'se6547/2018-in-russland/ro58472', conn)
print('Gathering WM Vorrunde done.')

# close connection
conn.close()
