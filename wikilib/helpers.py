import wikilib


DEBUG_INFO = True


def get_page_section_id_by_name(page_id, section):
    if DEBUG_INFO:
        print('get_page_section_id_by_id: %s %s' % (page_id, section))

    for s in wikilib.get_page_sections(page_id):
        if s['line'] == section:
            return s['index']