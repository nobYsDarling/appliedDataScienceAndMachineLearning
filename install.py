import sqlite3

conn = sqlite3.connect('data/fifa.db')

cur = conn.cursor()

cur.execute("CREATE TABLE nation ("
            "id             INTEGER PRIMARY KEY  AUTOINCREMENT," 
            "name           CHAR(100) NOT NULL," 
            "link           CHAR(255) NOT NULL,"
            "wiki_page_id   INTEGER   NOT NULL" 
            ");")

cur.execute("CREATE TABLE player ("
            "id             INTEGER PRIMARY KEY  AUTOINCREMENT," 
            "name           CHAR(100) NOT NULL," 
            "number         INTEGER   NOT NULL,"
            "position       CHAR(2)   NOT NULL,"
            "birthday       DATE      NOT NULL,"
            "caps           INTEGER   NOT NULL," 
            "goals          INTEGER   NOT NULL,"
            "wiki_page_id   INTEGER   NOT NULL" 
            ");")

cur.execute("CREATE TABLE team ("
            "id               INTEGER PRIMARY KEY  AUTOINCREMENT," 
            "link             CHAR(255)        NOT NULL," 
            "name             CHAR(100)        NOT NULL," 
            "nationality      CHAR(3)          NOT NULL,"
            "is_national_team INTEGER(1)       NOT NULL,"
            "wiki_page_id     INTEGER          NOT NULL" 
            ");")

cur.execute("CREATE TABLE player_to_team ("
            "player_id INTEGER     NOT NULL," 
            "team_id   INTEGER     NOT NULL,"
            "season    CHAR(9)     NOT NULL,"
            "FOREIGN KEY(player_id) REFERENCES player(id),"
            "FOREIGN KEY(team_id) REFERENCES team(id)"
            ");")


cur.close()
conn.close()
