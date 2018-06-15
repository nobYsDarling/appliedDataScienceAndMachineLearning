import urllib.request
import urllib.parse
import re
import json

from . import helpers


API_URL = 'https://en.wikipedia.org/w/api.php'

API_PAGE_IDS_ROOT = 13327177  # 2018_FIFA_World_Cup


API_PARAMS_QUERY = 'format=json&titles=%s&action=query&prop=content'
API_PARAMS_PAGE_CONTENT = 'action=parse&pageid=%s&prop=wikitext&format=json'
API_PARAMS_SECTIONS = 'action=parse&pageid=%s&prop=sections&format=json'
API_PARAMS_SECTION_CONTENT = 'action=parse&pageid=%s&prop=wikitext&section=%s&format=json'
API_PARAMS_PARSE_TEMPLATE = 'action=expandtemplates&text=%s&prop=wikitext&format=json'


API_PARAMS_CURRENT_SQUAD = 'action=parse&pageid=%s&prop=sections'


DEBUG_INFO = False

__wiki_parse_template__cache = {}
__wiki_get_page_id_by_link__cache = {}
__wiki_get_page_sections__cache = {}
__wiki_get_page_section_content_by_id__cache = {}
__wiki_get_page_content_by_id__cache = {}
__wiki_get_page_title_by_id__cache = {}


def parse_template(template):
    if template in __wiki_get_page_id_by_link__cache.keys():
        return __wiki_get_page_id_by_link__cache[template]

    urls = API_URL + '?' + API_PARAMS_PARSE_TEMPLATE % urllib.request.quote(template)
    if DEBUG_INFO:
        print('parse_template: %s %s' % (template, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    print(data)
    info = re.findall('\[\[([^:\]]*)\]\]', data['expandtemplates']['wikitext'])[0].split('|')

    if 2 != len(info):
        return None

    data = {
        'template': template,
        'data': data,
        'name': info[1],
        'link': info[0]
    }

    __wiki_get_page_id_by_link__cache[template] = data

    return data


def get_page_id_by_link(link, redirects=None):
    if redirects is None:
        redirects = {}

    static_redirect = link in redirects.keys()
    if static_redirect:
        if "" == redirects[link]:
            return None
        else:
            return get_page_id_by_link(redirects[link])

    if link in __wiki_get_page_id_by_link__cache.keys():
        return __wiki_get_page_id_by_link__cache[link]

    urls = API_URL + '?' + API_PARAMS_QUERY % urllib.request.quote(link)
    if DEBUG_INFO:
        print('get_page_id_for_link: %s %s' % (link, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())

    page_id = int(list(data['query']['pages'].keys())[0])

    info = get_page_content_by_id(page_id)
    redirect = re.findall('#REDIRECT ?\[\[([^\]]*)\]\]', info, re.IGNORECASE)
    if redirect:
        page_id = get_page_id_by_link(redirect[0])

    __wiki_get_page_id_by_link__cache[link] = page_id

    return page_id


def get_page_sections(page_id):
    if page_id in __wiki_get_page_sections__cache.keys():
        return __wiki_get_page_sections__cache[page_id]

    urls = API_URL + '?' + API_PARAMS_SECTIONS % page_id
    if DEBUG_INFO:
        print('get_page_sections: %s %s' % (page_id, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    data = data['parse']['sections']

    __wiki_get_page_sections__cache[page_id] = data

    return data


def get_page_title(page_id):
    if page_id in __wiki_get_page_title_by_id__cache.keys():
        return __wiki_get_page_title_by_id__cache[page_id]

    urls = API_URL + '?' + API_PARAMS_PAGE_CONTENT % page_id
    if DEBUG_INFO:
        print('get_page_title: %s %s' % (page_id, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    data = data['parse']['title']

    __wiki_get_page_title_by_id__cache[page_id] = data

    return data


def get_page_section_content_by_id(page_id, section_id):
    if (page_id, section_id) in __wiki_get_page_section_content_by_id__cache.keys():
        return __wiki_get_page_section_content_by_id__cache[(page_id, section_id)]

    urls = API_URL + '?' + API_PARAMS_SECTION_CONTENT % (page_id, section_id)
    if DEBUG_INFO:
        print('get_page_section_content_by_id: %s %s' % (page_id, urls))
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    data = data['parse']['wikitext']['*']

    __wiki_get_page_section_content_by_id__cache[(page_id, section_id)] = data

    return data


def get_page_content_by_id(page_id):
    if page_id in __wiki_get_page_content_by_id__cache.keys():
        return __wiki_get_page_section_content_by_id__cache[page_id]

    urls = API_URL + '?' + API_PARAMS_PAGE_CONTENT % page_id
    if DEBUG_INFO:
        print('get_page_content_by_id: %s' % page_id)
    url = urllib.request.urlopen(urls)

    data = json.loads(url.read().decode())
    data = data['parse']['wikitext']['*']

    __wiki_get_page_section_content_by_id__cache[page_id] = data

    return data


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

