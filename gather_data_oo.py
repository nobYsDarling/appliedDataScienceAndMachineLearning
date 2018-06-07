class Team:
    """ represents a team """
    id = None
    name = None
    link = None
    nationality = None
    is_national_team = None
    wiki_page_id = None

    def __init__(self, name, link, nationality, is_national_team, wiki_page_id):
        self.id = id
        self.name = name
        self.link = link
        self.nationality = nationality
        self.is_national_team = is_national_team
        self.wiki_page_id = wiki_page_id


class TeamList:
    """ represents a list of teams """
    l = []

    def __init__(self, o):
        self.l = o if type(o) is list else [o]
