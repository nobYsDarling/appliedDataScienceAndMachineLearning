import urllib.request
import urllib.parse
import re
import json

from . import helpers


API_URL = 'https://en.wikipedia.org/w/api.php'

API_PAGE_IDS_ROOT = 13327177  # 2018_FIFA_World_Cup


API_PARAMS_QUERY = 'format=json&titles=%s&action=query&prop=content'
API_PARAMS_SECTIONS = 'action=parse&pageid=%s&prop=sections&format=json'
API_PARAMS_SECTION_CONTENT = 'action=parse&pageid=%s&prop=wikitext&section=%s&format=json'
API_PARAMS_PARSE_TEMPLATE = 'action=expandtemplates&text=%s&prop=wikitext&format=json'


API_PARAMS_CURRENT_SQUAD = 'action=parse&pageid=%s&prop=sections'


DEBUG_INFO = True


__wiki_page_id_by_link_cache = {}


def parse_template(template):
    urls = API_URL + '?' + API_PARAMS_PARSE_TEMPLATE % urllib.request.quote(template)
    if DEBUG_INFO:
        print('parse_template: %s %s' % (template, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    info = re.findall('\[\[([^:\]]*)\]\]', data['expandtemplates']['wikitext'])[0].split('|')

    return {
        'template': template,
        'name': info[1],
        'link': info[0]
    }


def get_page_id_by_link(link, redirects=None):
    if redirects is None:
        redirects = {}

    static_redirect = link in redirects.keys()
    if static_redirect:
        if "" == redirects[link]:
            return None
        else:
            return get_page_id_by_link(redirects[link])

    if link in __wiki_page_id_by_link_cache.keys():
        return __wiki_page_id_by_link_cache[link]

    urls = API_URL + '?' + API_PARAMS_QUERY % urllib.request.quote(link)
    if DEBUG_INFO:
        print('get_page_id_for_link: %s %s' % (link, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())

    page_id = int(list(data['query']['pages'].keys())[0])

    # test if redirect

    __wiki_page_id_by_link_cache[link] = page_id

    return page_id


def get_page_sections(page_id):
    urls = API_URL + '?' + API_PARAMS_SECTIONS % page_id
    if DEBUG_INFO:
        print('get_page_sections_by_id: %s %s' % (page_id, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())

    return data['parse']['sections']


def get_page_section_content_by_id(page_id, section_id):
    urls = API_URL + '?' + API_PARAMS_SECTION_CONTENT % (page_id, section_id)
    if DEBUG_INFO:
        print('get_page_section_content: %s %s' % (page_id, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())

    return data['parse']['wikitext']['*']


def get_page_section_content(page_id, section):
    section_id = helpers.get_page_section_id_by_name(page_id, section)

    return get_page_section_content_by_id(page_id, section_id) if section_id is not None else None


def get_page_section_content_by_priority_list(page_id, sections):
    section_id = None
    i = 0

    while section_id is None and i < len(sections):
        section_id = helpers.get_page_section_id_by_name(page_id, sections[i])
        i += 1

    return get_page_section_content_by_id(page_id, section_id) if section_id is not None else None


# def parse_section_index(team_page_id):
#     index = get_page_sections_by_id(team_page_id)
#
#     print(index)
#     print(get_page_sections_content_by_id(team_page_id, index))


# def parse_squad(text):
#     return [parse_template(team) for team in re.findall('(\{\{fb\|[A-Z]*\}\})', text)]

