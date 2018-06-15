import re

import sqlite3
import urllib

import wikilib


conn = sqlite3.connect('data/fifa.db')
cur = conn.cursor()

teams = cur.execute('SELECT GROUP_CONCAT(id), * FROM team GROUP BY wiki_page_id HAVING count(*) > 1;').fetchall()
for team in teams:
    ids = [int(e) for e in team[0].split(',')]
    title = wikilib.get_page_title(team[6])

    cur.execute('UPDATE team SET link="%s" WHERE id=%d;' % (title, ids[0]))
    for team_id in ids[1:]:
        cur.execute('DELETE FROM team WHERE id=%d;' % team_id)

    conn.commit()

cur.close()
conn.close()