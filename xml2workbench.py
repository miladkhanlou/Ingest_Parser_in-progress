#!/usr/bin/env python3

# Todo: add usage here

import xml.etree.ElementTree as ET
import csv
from os import listdir, sep, path
import re

ns = {'':'http://www.loc.gov/mods/v3'}
mods_to_vocab = {
    'corporate': 'corporate_body',
    'personal': 'person',
    'conference': 'conference'
}
class XmlSet(object):
    def __init__(self):
        self.docs = []
        self.headers = set()
    def add(self, doc):
        # Add a parsed document/row with its headers
        self.docs.append(doc)
        self.headers.update(doc.keys())
    def print(self,fp):
        ## Write out to CSV file
        tmp = list(self.headers)
        tmp.sort()
        writer = csv.DictWriter(fp, fieldnames=tmp)
        writer.writeheader()
        for doc in self.docs:
            writer.writerow(doc)
    def input_directory(self, directory):
        files = listdir(directory)
        files.sort()
        for filename in files:
            if filename.endswith(".xml"):
                print("parsing {}".format(filename))
                self.add(parse_mods(directory + sep + filename))
    def maxlen(self, key):
        return max([len(x[key]) for x in self.docs])
    def oversize(self, key):
        return [x[key] for x in self.docs if len(x[key]) > 255]
        
################################### MODS SECTION PARSING ##########################################

def parseTitleInfo(root):
    titles = root.findall('titleInfo', ns)
    data = {'title': '', 'field_alt_title': [], 'field_full_title': ''}
    for title in titles:
        # Titles without types are main. However they're also limited in size.
        if 'type' not in title.attrib:
            data['title'] = concat_title_parts(title)
            data['field_full_title'] = data['title']
            if len(data['title']) > 255 :
                data['title'] = data['title'][:254]
        elif title.get('type') == 'alternative':
            data['field_alt_title'].append(concat_title_parts(title))
        # For the two books with uniform titles, they're being treated as alt titles.
        elif title.get('type') == 'uniform':
            data['field_alt_title'].append(concat_title_parts(title))
        else:
            print("ERROR: title type {}".format(title.get('type')))
    data['field_alt_title'] = '|'.join(data['field_alt_title'])
    return data

def concat_title_parts(titleInfo):
    text = ''
    #FIXME rewrite as foreach?
    non_sort = titleInfo.find('nonSort', ns)
    if non_sort is not None and non_sort.text is not None:
        text += non_sort.text
        if non_sort.text[-1] != ' ':
            text += ' '
    text += titleInfo.find('title', ns).text
    subtitle = titleInfo.find('subTitle', ns)
    if subtitle is not None and subtitle.text is not None:
        text += ' : '
        text += subtitle.text
    partnumber = titleInfo.find('partNumber', ns)
    if partnumber is not None and partnumber.text is not None:
        text += '. '
        text += partnumber.text
    partname = titleInfo.find('partName', ns)
    if partname is not None and partname.text is not None:
        text += '. '
        text += partname.text
    return text

def parseNameInfo(root):
    names = root.findall('name', ns)
    name_data = []
    for name in names:
        
        ## Get name type to determine vocab.
        vocab = 'person'
        if name.get('type') is None:
            # All ilives names have type; notify if otherwise.
            print("ERROR: no type for name {}".format(name.text))
        # else:
        #   nameType = name.get('type')
        #   if nameType in mods_to_vocab.keys():
        #     vocab = mods_to_vocab[nameType]
        elif name.get('type') == 'personal':
            vocab = 'person'
        elif name.get('type') == 'corporate':
            vocab = 'corporate_body'
        elif name.get('type') == 'conference':
            vocab = 'conference'
        else:
            print("ERROR: unhandled name type {}".format(name.get('type')))
        roles = name.findall('role', ns)
        role_text = 'relators:ctb'
        for role in roles:
            # CLEAN ME - deal with improper use of <text> to hold the roleTerm
            text = role.find('text', ns)
            if text is not None:
                if text.text == 'creator':
                    role_text = 'relators:cre'
                else:
                    print("unhandled roleterm {}".format(text.text))
            roleTerms = role.findall('roleTerm',ns)
            for roleTerm in roleTerms:
                if roleTerm.text == 'creator':
                    role_text = 'relators:cre'
                elif roleTerm.text == 'editor' or roleTerm.text == 'editor.':
                    role_text = 'relators:edt'
                elif roleTerm.text == 'Author':
                    role_text = 'relators:aut'
                else:
                    print("unhandled roleterm: {}".format(roleTerm.text))
        name_text = ''
        for namePart in name.findall('namePart', ns):
            if namePart.get('type') in ['termsOfAddress','date']:
                name_text += ', '
            elif namePart.get('type') is not None:
                print("Unhanded namePart type {}".format(namePart.get('type')))
            name_text += namePart.text
        
        name_data.append(role_text + ':' + vocab + ':' + name_text)
    
    return {'field_linked_agent': '|'.join(name_data)}

def parsePidFromFilename(filename):
    temp = path.basename(filename)
    temp = temp.replace('_MODS.xml','')
    return temp.replace('_',':',1)

def parseTypeOfResource(root):
    # Only accept 'collection' and 'text'; map to capitalized to match Drupal
    xml_tor = root.findall('typeOfResource', ns)
    tors = []
    for type in xml_tor:
        if type.get('collection') == "yes":
            tors.append('Collection')
        if type.text == 'collection':
            tors.append('Collection')
        elif type.text == 'text':
            tors.append("Text")
        else:
            # All ilives are collection or text; notify if otherwise.
            print("Uncaught type of resource: {}".format(type.text))
    return {'field_resource_type': '|'.join(tors)}
        
        
def parseGenre(root):
    xml_genres = root.findall('genre',ns)
    genres = []
    for genre in xml_genres:
        tmp = genre.text.lower()
        genres.append(tmp)
    return {'field_genre': '|'.join(genres)}
    
def parseOriginInfo(root):
    data = {'field_place_published': [],
            'field_place_published_country':'', # assuming single valued
            'field_linked_agent': [],
            'field_edtf_date_issued': [],
            'field_edtf_date_created': [],
            'field_date_captured': [] ,
            'field_mode_of_issuance': '',   # assuming single valued
            'field_edition': '',            # assuming single valued
            'field_copyright_date':'',}    # assuming single valued
    xml_originInfo = root.findall('originInfo',ns)
    for oi in xml_originInfo:
        if oi.get('type') is not None:
            # No ilives have types on originInfo.
            print("originInfo has type {}".format(oi.get('type')))
        else:
            for subelem in oi:
                if subelem.tag == '{http://www.loc.gov/mods/v3}place':
                    handled = False
                    for place_subelem in subelem:
                        # Test for authority
                        if place_subelem.get('authority')  in ['marccountry', 'marc']:
                            # This represents a "code" version of the place.
                            data['field_place_published_country'] = place_subelem.text
                            handled = True
                        # Some full place elements wrongly use a <text> tag.
                        elif place_subelem.get('type') == 'text' or place_subelem.tag == '{http://www.loc.gov/mods/v3}text':
                            # this is the longer one
                            data['field_place_published'].append(place_subelem.text)
                            handled = True
                    if not handled:
                        # All islandlives place are either marc auth or type text.
                        print("Place element needs handling. {}".format(subelem.text))
                elif subelem.text is None:
                    #Skip empty elements made by MODS forms.
                    continue
                elif subelem.tag == '{http://www.loc.gov/mods/v3}publisher':
                    # Publishers go in linked agents and need the full elaborated string.
                    data['field_linked_agent'].append('relators:pbl:corporate_body:' + subelem.text )
                elif subelem.tag == '{http://www.loc.gov/mods/v3}dateIssued':
                    data['field_edtf_date_issued'].append(subelem.text)
                elif subelem.tag == '{http://www.loc.gov/mods/v3}dateCreated':
                    data['field_edtf_date_created'].append(subelem.text)
                elif subelem.tag == '{http://www.loc.gov/mods/v3}dateCaptured':
                    data['field_date_captured'].append(subelem.text)
                elif subelem.tag == '{http://www.loc.gov/mods/v3}copyrightDate':
                    data['field_copyright_date'] = subelem.text
                elif subelem.tag == '{http://www.loc.gov/mods/v3}issuance':
                    data['field_mode_of_issuance'] = subelem.text
                elif subelem.tag == '{http://www.loc.gov/mods/v3}edition':
                    data['field_edition'] = subelem.text
                else:
                    print("unhandled origininfo tag is {}".format(subelem.tag))
    
    ###### Clean data #####
    # Clean date issued
    if 'n.d' in data['field_edtf_date_issued']:
        data['field_edtf_date_issued'].remove('n.d')
    # Remove duplicates
    data['field_edtf_date_issued'] = list( dict.fromkeys(data['field_edtf_date_issued'] ) )
    # Move cXXXX dates to copyright date
    for issuedDate in data['field_edtf_date_issued']:
        if len(issuedDate) == 5 and issuedDate.startswith('c'):
            # We have a copyright date
            if data['field_copyright_date']:
                print("MULTIPLE COPYRIGHT DATES: {},{}".format(data['field_copyright_date'],issuedDate))
            else:
                data['field_copyright_date'] = issuedDate.replace('c','')
                data['field_edtf_date_issued'].remove(issuedDate)
    
    # Collapse multi-valued fields
    data['field_place_published'] = '|'.join(data['field_place_published'])
    data['field_linked_agent'] = '|'.join(data['field_linked_agent'])
    data['field_edtf_date_issued'] = '|'.join(data['field_edtf_date_issued'])
    data['field_edtf_date_created'] = '|'.join(data['field_edtf_date_created'])
    data['field_date_captured'] = '|'.join(data['field_date_captured'])
    return data


def parseLanguage(root):
    xml_langs = root.findall('language',ns)
    data = {'field_language': []}
    for lang in xml_langs:
        for lang_term in lang:
            if lang_term.text == 'eng' and lang_term.get('type') == 'code':
                data['field_language'].append('English')
            elif lang_term.text == 'fre' and lang_term.get('type') == 'code':
                data['field_language'].append('French')
            elif lang_term.text == 'a' and lang_term.get('type') == 'code': # FIXME ignore bad data in 2 recs
                continue
            else:
                print("unhandled tag: {}, text: {}, attrib: {}".format(lang_term.tag, lang_term.text, lang_term.attrib))
    return {key: '|'.join(value) for key, value in data.items()}

def parsePhysicalDescription(root):
    data = {
        'field_physical_form' : '',
        'field_extent' : ''
    }
    xml_physDesc = root.findall('physicalDescription',ns)
    for pd in xml_physDesc:
        for elem in pd:
            if elem.tag == '{http://www.loc.gov/mods/v3}form':
                data['field_physical_form'] = elem.text
            elif elem.tag == '{http://www.loc.gov/mods/v3}extent':
                data['field_extent'] = elem.text
            else:
                print("Unhandled element: tag: [{}], text: [{}], attrib: {}".format(elem.tag, elem.text, elem.attrib))
    return data

def parseAbstract(root):
    data = []
    xml_abstract = root.findall('abstract',ns)
    for abstract in xml_abstract:
        if abstract.text is not None:
            if abstract.get('type') is not None:
                data.append(': '.join([abstract.get('type'), abstract.text]))
                print("abstract type: [{}]".format(abstract.get('type')))
            else:
                data.append(abstract.text)
    return {'field_abstract': '|'.join(data) }

def parseTableOfContents(root):
    data = []
    xml_toc = root.findall('tableOfContents',ns)
    for toc in xml_toc:
        # print("found TOC: {}".format(toc.text))
        if toc.text is not None:
            data.append(toc.text)
    return {'field_table_of_contents': '|'.join(data) }

def parseTargetAudience(root):
    xml_ta = root.findall('targetAudience',ns)
    for ta in xml_ta:
        if ta.text is not None:
            print("FOUND: TARGET AUDIENCE {}".format(ta.text))

def parseNote(root):
    data = []
    xml_note = root.findall('note',ns)
    for note in xml_note:
        if note.text is not None:
            if note.get('type') is not None:
                data.append(': '.join([note.get('type'), note.text]))
                #print("note type: [{}]".format(note.get('type')))
            else:
                data.append(note.text)
    return {'field_note': '|'.join(data) }

def trimXML(text):
    if text is None:
        return ''
    return re.sub('\n* *$','',text)

def trimXMLlist(list):
    return [trimXML(x) for x in list if trimXML(x) != '']

def parseSubject(root):
    data = {
        'field_subject': [],
        # 'field_subject_general': [],
        'field_subjects_name': [],
        # 'field_temporal_subject': [],
        'field_geographic_subject': []
    }
    for subject in root.findall('subject',ns):
        if subject.get('authority') == 'lcsh': # Then create a string out of this subject
            components = []
            type = subject[0].tag
            for elem in subject:
                elem.text = trimXML(elem.text)
                if elem.text:
                    components.append(elem.text)
                elif elem.tag == '{http://www.loc.gov/mods/v3}name':
                    nameValue = ' '.join([subelem.text for subelem in elem])
                    components.append(nameValue)
                        
            subject_string = ' -- '.join(components)
            if type == '{http://www.loc.gov/mods/v3}geographic':
                data['field_geographic_subject'].append(subject_string)
                # print('subject string: [{}]'.format(subject_string))
            elif type == '{http://www.loc.gov/mods/v3}topic':
                data['field_subject'].append('subject:' + subject_string)
            elif type == '{http://www.loc.gov/mods/v3}name':
                nametype = mods_to_vocab[subject[0].get('type')]
                data['field_subjects_name'].append(nametype + ':' + subject_string)
            else:
                print("Unhandled subject string of type: {}".format(type))

        hg = subject.find('hierarchicalGeographic',ns)
        if hg:
            data['field_geographic_subject'].append(' -- '.join([trimXML(x) for x in hg.itertext() if trimXML(x) != '']))
        
        if subject.find('cartographics', ns):
            subelem = subject.find('cartographics', ns).find('coordinates', ns)
            if subelem.text and trimXML(subelem.text):
                coordinates = True
                if subject.find('hierarchicalGeographic',ns):
                    also_has_name = True
                    # print(data['field_geographic_subject'][-1])
                    # print(''.join(subelem.itertext()))
                else:
                    print("Coordinates present, does not have name also.")
                    also_has_name = False
                    
    return {key : '|'.join(value) for key, value in data.items()}

def parseClassification(root):
    data = {
        'field_lcc_classification': '',
        'field_classification' : '',
        'field_dewey_classification': ''
        
    }
    for classification in root.findall('classification',ns):
        auth = classification.get('authority')
        if auth == 'ddc':
            data['field_dewey_classification'] = classification.text
        elif auth == 'lcc':
            data['field_lcc_classification'] = classification.text
        else:
            data['field_classification'] = classification.text
            print("ELEMENT text: [{}]".format('; '.join(classification.itertext())))
    return data

def parseRelatedItem(root):
    data = {
        'field_is_succeeded_by': [], # TODO Make fields
        'field_is_preceded_by': [],  # TODO Make fields
        'field_note' : []
    }
    for relatedItem in root.findall('relatedItem',ns):
        if relatedItem.get('type') == "original":
            # From a glance, these are all in note fields
            continue
        # Preceding and succeeding get their own fields
        elif relatedItem.get('type') == "preceding":
            data['field_is_preceded_by'].append(' '.join(trimXMLlist(relatedItem.itertext())))
        elif relatedItem.get('type') == 'succeeding':
            data['field_is_succeeded_by'].append(' '.join(trimXMLlist(relatedItem.itertext())))
        #
        elif relatedItem.get('type') in ['series', 'host'] :
            # Add a note
            data['field_note'].append(relatedItem.get('type') + ': ' + ' '.join(trimXMLlist(relatedItem.itertext())))
        elif relatedItem.get('type') in ['otherVersion', 'constituent'] :
            # Only instance was a self-reference. ignore.
            continue
        elif relatedItem.get('type') is None:
            data['field_note'].append(' '.join(trimXMLlist(relatedItem.itertext())))
        else:
            print("Unhandled Related Item: {}".format(':'.join(trimXMLlist(relatedItem.itertext()))))
            print("TYPE: [{}]".format(relatedItem.get('type')))
        # Found a Part within the work, series it's part of (440), relateditem succeeding name and preceeding name.
    return {key : '|'.join(value) for key, value in data.items()}

def parseIdentifier(root):
    data = {
        'field_identifier': [],
        'field_local_identifier' : [],
        'field_isbn': [],
        'field_oclc_number': []
    }
    for identifier in root.findall('identifier',ns):
        id_type = identifier.get('type')
        id_value = trimXML(identifier.text)
        if id_value is None or id_value == '':
            # There is no value here to process.
            continue
        elif id_type == 'uri':
            # Decision to filter these out as they are broken links
            continue
        if id_type == 'isbn':
            data['field_isbn'].append(identifier.text)
        elif id_type == 'oclc':
            data['field_oclc_number'].append(identifier.text)
        elif id_type == 'local':
            data['field_local_identifier'].append(identifier.text)
        else:
            # print("Identifier type: [{}], value: [{}]".format(str(id_type), str(id_value)))
            data['field_identifier'].append(identifier.text)
    return {key : '|'.join(value) for key, value in data.items()}

def parseAccessCondition(root):
    data = {
        'field_rights': []
    }
    for accessCondition in root.findall('accessCondition',ns):
        id_type = accessCondition.get('type')
        id_value = trimXML(accessCondition.text)
        if id_value is None or id_value == '':
            # There is no value here to process.
            continue
        if id_type:
            data['field_rights'].append(id_type + ': ' + id_value)
        else:
            data['field_rights'].append(id_value)
    return {key : '|'.join(value) for key, value in data.items()}

def parsePart(root):
    data = {}
    for part in root.findall('part',ns):
        print("PART FOUND: [{}]".format(','.join(part.itertext())))
    return data

def parseExtension(root):
    data = {}
    for part in root.findall('extension',ns):
        print("EXT FOUND: [{}]".format(','.join(part.itertext())))
    return data

################################### FILE HANDLING ##########################################

def parse_mods(filename):
    
    # Prepare to parse XML
    tree = ET.parse(filename)
    root = tree.getroot()
    xml_data = {}
    # Parse PID
    pid = parsePidFromFilename(filename)
    xml_data.update({'PID': pid,'field_pid': pid})
    # Parse titleinfo
    xml_data.update(parseTitleInfo(root))
    # Parse name
    xml_data.update(parseNameInfo(root))
    # Parse type of resource
    xml_data.update(parseTypeOfResource(root))
    # Parse genre
    xml_data.update(parseGenre(root))
    # Parse originInfo
    oiData = parseOriginInfo(root)
    # Combine publisher with rest of names
    if oiData['field_linked_agent']:
        if xml_data['field_linked_agent']:
            oiData['field_linked_agent'] = '|'.join([xml_data['field_linked_agent'],oiData['field_linked_agent']])
    else:
        del oiData['field_linked_agent']
    xml_data.update(oiData)
    # Parse language
    xml_data.update(parseLanguage(root))
    # Parse physical Description
    xml_data.update(parsePhysicalDescription(root))
    # parse abstract
    xml_data.update(parseAbstract(root))
    # Parse TableOfContents:
    xml_data.update(parseTableOfContents(root))
    # skip targetAudience, no mapping.
    # Parse notes
    xml_data.update(parseNote(root))
    # Parse subjects
    xml_data.update(parseSubject(root))
    # Parse classification
    xml_data.update(parseClassification(root))
    # Parse relatedItem
    relData = parseRelatedItem(root)
    # Append alterations to MODS note properly:
    if xml_data['field_note']:
        if relData['field_note']:
            relData['field_note'] = '|'.join([relData['field_note'],xml_data['field_note']])
        else:
            del relData['field_note']
    xml_data.update(relData)
    # Parse identifier data
    xml_data.update(parseIdentifier(root))
    # Skip Location; no mapping.
    # Parse AccessCondition
    xml_data.update(parseAccessCondition(root))
    # Look for values in part - none found.
    partData = parsePart(root)
    # Look for values in Extension
    extData = parseExtension(root)
    # Ignore recordInfo data - no mapping.
    return xml_data
    
def main():
    data = XmlSet()
    directory = '/Users/rlefaive/Documents/Projects/2020-ilives-metadata/ilives_mods'
    data.input_directory(directory)
    #FIXME OUTPUT SHORTCUT
    #print("large titles {}".format('.'.join(data.oversize('title'))))
    # print("length alt title: {}".format(data.maxlen('field_alt_title')))
    output_filename = 'output.csv'
    with open(output_filename, 'w') as csv:
        data.print(csv)
    
if __name__ == '__main__':
    main()