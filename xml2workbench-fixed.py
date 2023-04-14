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
    #INPUT DATA STARTS
    def input_directory(self, directory):
        files = listdir(directory)
        files.sort()
        for filename in files:
            if filename.endswith(".xml"):
                print("parsing {}".format(filename))
                self.add(parse_mods(directory + sep + filename))
    #NOT USING THIS
    def maxlen(self, key):
        return max([len(x[key]) for x in self.docs])
    def oversize(self, key):
        return [x[key] for x in self.docs if len(x[key]) > 255]
        
################################### MODS SECTION PARSING ###################################
## Milad notes: changes to the way it writes text to fix the errors:
def concat_title_parts(titleInfo):
    text = ''
    #FIXME rewrite as foreach?
    non_sort = titleInfo.find('nonSort', ns)
    if non_sort is not None and non_sort.text is not None:
        text += non_sort.text
        if non_sort.text[-1] != ' ':
            text += ' '

    title = titleInfo.find('title', ns)
    if title is not None and title.text is not None:
        text += title.text
        text += ' : '
               
    subtitle = titleInfo.find('subTitle', ns)
    if subtitle is not None and subtitle.text is not None:
        # text += ' : '
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

### Milad note: Parse name
# def parseName(root):

### Milad note: Parse RecordInf
# def parsRecordInfo(root):

### Milad note: Parse extention
# def parsExtention(root):

### Milad note: Parse
def parseTitleInfo(root):
    titles = root.findall('titleInfo', ns)
    data = {'title': '', 'field_alt_title': [], 'field_full_title': ''}
    for title in titles:
        # Titles without types are main. However they're also limited in size.
        if 'type' not in title.attrib:
            data['title'] = concat_title_parts(title).split(" : ")[0]
            #data['title'] = concat_title_parts(title)
            data['field_full_title'] = data['title']
            if len(data['title']) > 255 :
                data['title'] = data['title'][:254]
                
        elif title.get('type') == 'alternative':
            data['field_alt_title'].append(concat_title_parts(title))

        elif title.get('type') == 'translated':
            data['field_alt_title'].append(concat_title_parts(title))
            
        elif title.get('type') == 'abbreviated':
            data['field_alt_title'].append(concat_title_parts(title))
            
        elif title.get('type') == 'uniform':
            data['field_alt_title'].append(concat_title_parts(title))
        else:
            print("ERROR: title type {}".format(title.get('type')))
    data['field_alt_title'] = '|'.join(data['field_alt_title'])
    return data

#Milad Notes: Fixing name.text:
#we do not have any functionality to get the namePart.text, roleTerm.text and role.text
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
        if name.get('type') in mods_to_vocab.keys():
            vocab = mods_to_vocab[name.get('type')]
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

### Milad Note: added the field_resource_type data in the output by adding logic
def parseTypeOfResource(root):
    # Only accept 'collection' and 'text'; map to capitalized to match Drupal
    xml_tor = root.findall('typeOfResource', ns)
    tors = []
    for type in xml_tor:
        if type.text is not None: 
            tors.append(type.text)
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
    print("*********************** {}".format(xml_genres))
    genres = []
    for genre in xml_genres:
        if genre is not None and genre.text is not None:
            genretxt = genre.text
            tmp = genretxt.lower()
            genres.append(tmp)
    return {'field_genre': '|'.join(genres)}

### Milad Notes: adding fields in Original info, fixiing the logic to get field_place_of_publication(Should not sepcify .get('type') is None):
def parseOriginInfo(root):
    data = {'field_place_of_publication': [],
            #'field_place_of_publication_country':'',
            'field_linked_agent': [],
            'field_edtf_date_issued': [],
            'field_edtf_date_created': [],
            'field_date_captured': [] ,
            #'field_mode_of_issuance': '',  
            #'field_edition': '',        
            #'field_copyright_date':'' 
            } 
    xml_originInfo = root.findall('originInfo',ns)
    for oi in xml_originInfo:
        # if oi.get('type') is None:
        #     # No ilives have types on originInfo.
        #     print("originInfo has type {}".format(oi.get('type')))
        # else:
        for subelem in oi:
            if 'place' in subelem.tag:
                handled = False
                for place_subelem in subelem:
                    # Test for authority
                    if place_subelem.get('authority') in ['marccountry', 'marc']:
                        # This represents a "code" version of the place.
                        data['field_place_of_publication_country'] = place_subelem.text
                        handled = True
                    # Some full place elements wrongly use a <text> tag.
                    elif place_subelem.get('type') == 'text' or "placeTerm" in place_subelem.tag:
                        # this is the longer one
                        data['field_place_of_publication'].append(place_subelem.text)
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
            elif subelem.tag == '{http://www.loc.gov/mods/v3}copyrightDate':                                                               #No need for LDL#
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
                data['field_copyright_date'] = issuedDate.replace('c','')                                                                      #No need for LDL#
                data['field_edtf_date_issued'].remove(issuedDate)
    
    # Collapse multi-valued fields
    data['field_place_of_publication'] = '|'.join(data['field_place_of_publication'])
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


############## Milad Note: note,internetMediaType,digitalOrigin data added ##############
def parsePhysicalDescription(root):
    data = {
        'field_physical_form' : [],
        'field_extent' : [],
        'field_physical_description_note': [], 
        'Field_internet_Media_Type': [],
        'digital_Origin': []
    }
    xml_physDesc = root.findall('physicalDescription',ns)
    for Desc in xml_physDesc:
        for elem in Desc.iter():
            if 'note' in elem.tag:
                data['field_physical_description_note'].append(elem.text)
            if 'extent' in elem.tag:
                data['field_extent'].append(elem.text)
            if 'internetMediaType' in elem.tag:
                data['Field_internet_Media_Type'].append(elem.text)
            if 'digitalOrigin' in elem.tag:
                data['digital_Origin'].append(elem.text)
            if 'form' in elem.tag:
                data['field_physical_form'].append(elem.text)
            elif elem.tag == 'internetMediaType':
                data['Field_internet_Media_Type'].append(elem.text)
            else:
                print("Unhandled element: tag: [{}], text: [{}], attrib: {}".format(elem.tag, elem.text, elem.attrib))
    return {key: '|'.join(value) for key, value in data.items()}
### Milad Note: separated the abstracts into two fields according to the child tag's attribute
def parseAbstract(root):
    data = {
        'field_harmful_content_notice': [],
        'field_abstract_description': []
        # 'abstract': [] #In case if we needed to add all the abstact texts into one field
    }
    xml_abstract = root.findall('abstract',ns)
    for abstract in xml_abstract:
        if abstract.text is not None:
            if abstract.get('displayLabel') == 'Harmful Content Notice':
                data['field_harmful_content_notice'].append(abstract.text)
            if abstract.get('displayLabel') == 'Description':
                data['field_abstract_description'].append(abstract.text)
            # if abstract.get('type') is not None:
            #     data['abstract'].append(': '.join([abstract.get('type'), abstract.text]))
            #     print("abstract type: [{}]".format(abstract.get('type')))

            # else:
            #     data['abstract'].append(abstract.text)
    # return {'field_abstract': '|'.join(data) }
    return {key : '|'.join(value) for key, value in data.items()}

###Milad Note: We do not have tableOfContents field in LDL
# def parseTableOfContents(root):
    data = []
    xml_toc = root.findall('tableOfContents',ns)
    for toc in xml_toc:
        # print("found TOC: {}".format(toc.text))
        if toc.text is not None:
            data.append(toc.text)
    return {'field_table_of_contents': '|'.join(data) }

# def parseTargetAudience(root):
    xml_ta = root.findall('targetAudience',ns)
    for ta in xml_ta:
        if ta.text is not None:
            print("FOUND: TARGET AUDIENCE {}".format(ta.text))

def parseNote(root):
    data = {
        'field_note' : [],
        'field_source_note': [],
        'field_preferred_citation' : [],
        'field_harmful_content_notice': [],
        'fieldNoteNew': []
    }
    ###Milad Notes: data added to field_source_note,field_preferred_citation,field_harmful_content_notice, fieldNoteNew fields according to their attributes and tags
    xml_note = root.findall('note',ns)
    for note in xml_note:
        if note.text is not None:  
            if note.get('type') == 'ownership':
                data['field_source_note'].append(note.text)
            elif note.get('type') == 'preferred citation':
                data['field_preferred_citation'].append(note.text)
            if note.get('type') == 'content': 
                # if "displayLabel" not in note.attrib: # If we do not have any display labels Then create a string out of this subject
                #     data['field_subject'].append(note.text)
                if note.get('displayLabel') == 'Harmful Content Notice':
                    data['field_harmful_content_notice'].append(note.text)
                if note.get('displayLabel') == 'Note':
                    data['fieldNoteNew'].append(note.text)
            
            # elif note.text is not None:
            else:
                # data['field_note'] == ': '.join([note.get('type'), note.text, '|'])
                data['field_note'].append('{}:{}'.format(note.get('type'), note.text))

        # return {'field_note': '|'.join(data) }
    return {key : '|'.join(value) for key, value in data.items()}

def trimXML(text):
    if text is None:
        return ''
    return re.sub('\n* *$','',text)

def trimXMLlist(list):
    return [trimXML(x) for x in list if trimXML(x) != '']

def parseSubject(root):
    data = {
        'field_subject': [],
        'field_geographic_subject': [],
        'field_subjects_name': []
    }
    for subject in root.findall('subject',ns):
        #####Milad Note: Changed the logic to write text in 'topic' like topic1.text--topc2.text (see the return at the end of this function)
        if "displayLabel" not in subject.attrib: # Then create a string out of this subject
            for sub in subject.iter():
                if 'topic' in sub.tag and sub.text is not None:
                    data['field_subject'].append(sub.text)
                
        ##### Milad Note: change the way and logic that data written to field_subjects_name 
        if subject.get('displayLabel') == 'Name Subject':
            for elems in subject.iter(): #use iter to output the certain tag or attrib
                if 'namePart' in elems.tag:
                    data['field_subjects_name'].append(elems.text)
                            
        for locIter in subject.iter(): #Milad note: text in <subject><geographic> should go here, regardless of @displayLabel--so @displayLabel can be disregarded 
            if 'geographic' in locIter.tag:
                data['field_geographic_subject'].append(locIter.text)
                
        ######################## Milad Note: Guess we do not need ######################## 
        # if subject.find('cartographics', ns):
        #     subelem = subject.find('cartographics', ns).find('coordinates', ns)
        #     if subelem.text and trimXML(subelem.text):
        #         coordinates = True
        #         if subject.find('hierarchicalGeographic',ns):
        #             also_has_name = True
        #             # print(data['field_geographic_subject'][-1])
        #             # print(''.join(subelem.itertext()))
        #         else:
        #             print("Coordinates present, does not have name also.")
        #             also_has_name = False
        
    for key, value in data.items():
        if key != "field_subject":
            return {key : '|'.join(value)}
        else: 
            return {key : '--'.join(value)}

#### Milad note: Add pars location logic
def parseLocation(root):
    data = {"field_physical_location": [],
            "field_institution_web_site": [], 
            # "field_oclc_symbol": [],
            "field_sublocation": [],
            "field_shelf_location": []
            }
    for location in root.findall('location', ns):
        print("Location ---------------------***********************")
        for locs in location.iter():
            if 'physicalLocation' in locs.tag :
                if locs.get("displayLabel") == "Physical Location":
                    data["field_physical_location"].append(locs.text) 
                if locs.get("displayLabel") == "OCLC Member Symbol":
                    data["field_institution_web_site"].append(locs.text)
            if 'subLocation' in locs.tag:
                data["field_sublocation"].append(locs.text)
            if 'shelfLocator' in locs.tag:
                data["field_shelf_location"].append(locs.text)
    
    print('test Texts')
    print("field physical location: {}".format(data["field_physical_location"]))
    print("field institution web site: {}".format(data["field_institution_web_site"]))
    print("field sublocation: {}".format(data["field_sublocation"]))
    print("field shelf location: {}".format(data["field_shelf_location"]))
    
    return {key : '|'.join(value) for key, value in data.items()}


def parseRelatedItem(root):
    data = {
        #Milad note: field_is_succeeded_by,field_is_preceded_by are not needed to be parsed
        'field_note' : [],
        'field_digital_collection': [],
        'field_digital_collection_url': [],
        'field_repository_collection': [],
        'field_repository_collection_guide': [],
        'field_parent_Item_Title': []
    }

    for relatedItem in root.findall('relatedItem',ns):
        if relatedItem.get('type') == "original":
            # From a glance, these are all in note fields
            continue
        # Milad note: Preceding and succeeding are not needed in LDL, Fileds are commented out
        elif relatedItem.get('type') == 'series':
            # Add a note
            data['field_note'].append(relatedItem.get('type') + ': ' + ' '.join(trimXMLlist(relatedItem.itertext())))
            
    ######## Milad note: New logics to add a few fields by parsing into tags, child tags, get the text eccouridng to the tag's attribute ########
        elif relatedItem.get('type') == 'host':
            for elems in relatedItem.iter():
                if "titleInfo" in elems.tag:
                    if elems.get('displayLabel') == 'Parent Item Title':
                        for elem in elems:
                            data['field_parent_Item_Title'].append(elem.text)
                            
                    if elems.get('displayLabel') == 'Digital Collection':
                        for elem in elems:
                            data['field_digital_collection'].append(elem.text)

                    if elems.get('displayLabel') == 'Repository Collection':
                        for elem in elems:
                            data['field_repository_collection'].append(elem.text)
                            
                if "location" in elems.tag:
                    for elem in elems:
                        if elem.get('displayLabel') == 'Relation':
                                data['field_digital_collection_url'].append(elem.text)
                                
                        if elem.get('displayLabel') == 'Repository Collection Guide':
                            for elem in elems:
                                data['field_repository_collection_guide'].append(elem.text)
                                
            print("New Fields:***") 
            print("field digital collection: {}".format(data["field_digital_collection"]))
            print("MyField parent item title: {}".format(data["field_parent_Item_Title"]))
            print("field repository collection: {}".format(data["field_repository_collection"]))
            print("field digital collection URL: {}".format(data["field_digital_collection_url"]))
            print("field repository collection guide: {}".format(data["field_repository_collection_guide"]))

        elif relatedItem.get('type') == 'series' :
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

### Milad Note: added the functionality to add data for field_local_identifier. to write two idnetifiers together, the way librarians wanted e.g TypeName:identifyerText
def parseIdentifier(root):
    data = {
        'field_identifier': [],
        'field_local_identifier' : [],
        'identifier_displayLabel_missingAttribs' : [], #SHOWING MISSING ATTRIBUTES IN COMPARISON WITH MASTER
        'identifier_displayLabel_Attribs': [], #SHOWING ALL THE ATTRIBUTES IN XML
        'identifier_Master_displayLabel_Attribs': []
        #Milad note: field_isbn,field_oclc_number are not needed to be parsed
    }
    identifier_Master_displayLabel_Attribs = ['Item Number', 'ISBN']
    for i in identifier_Master_displayLabel_Attribs:
        data['identifier_Master_displayLabel_Attribs'].append(i)
    localType = ''
    isbnType = ''
    for identifier in root.findall('identifier',ns):
        data['identifier_displayLabel_Attribs'].append(identifier.get('displayLabel'))
        print('**************************************************************************.{}'.format(data['identifier_displayLabel_Attribs']))
        if identifier.get('displayLabel') not in identifier_Master_displayLabel_Attribs:
            data['identifier_displayLabel_missingAttribs'].append(identifier.get('displayLabel'))
        id_type = identifier.get('type')
        id_value = trimXML(identifier.text)
        if id_value is None or id_value == '':
            # There is no value here to process.
            continue
        elif id_type == 'uri':
            # Decision to filter these out as they are broken links
            continue
        # if id_type == 'isbn':
        #     data['field_isbn'].append(identifier.text)
        elif id_type == 'oclc':
            data['field_oclc_number'].append(identifier.text)
        if id_type == 'local':
            localType= identifier.text
        if id_type == 'isbn':
            isbnType= id_type
            data['field_local_identifier'].append("{}:{}".format(isbnType,localType))

        else:
            # print("Identifier type: [{}], value: [{}]".format(str(id_type), str(id_value)))
            data['field_identifier'].append(identifier.text)

    return {key : '|'.join(value) for key, value in data.items()}

#### Milad note: 5 fields added insteaed of field_rights. Codes for field rights commented out ####
def parseAccessCondition(root):
    data = {
        # 'field_rights': [],
        'field_rights_statement': [],
        'field_rights_information': [],
        'field_access_restrictions': [],
        'field_contact_information': [],
        'field_rights_statement_uri': []
    }
    for accessCondition in root.findall('accessCondition',ns):
        attributes = accessCondition.attrib
        print("This is accessCondition Attributes .... {}".format(attributes))
        
        id_type = accessCondition.get('type')
        disp_label = accessCondition.get('displayLabel')
        
        # add field_rights_statement
        if id_type == "use and reproduction" and disp_label == "Rights Statement": 
            data["field_rights_statement"].append(accessCondition.text)
            
        # add field_rights_statement_uri: xlink:href is not a attribute
        
        ###Milad Note: field_rights_statement_uri has ERROR. It does not see xlink:href as an attribute
        #A) use the right attribute name by using root.get('attributeName')
        if disp_label == "xlink:href": 
            data["field_rights_statement_uri"].append(accessCondition.get('xlink:href'))
        #B) use attribute name by getting root.attrib in a dictionary, Output be like: {'type': 'use and reproduction', 'displayLabel': 'Rights Information'} 
        if attributes.keys() == 'xlink:href': 
            data["field_rights_statement_uri"].append(attributes.values())
            
        # add field_rights_information
        if id_type == "use and reproduction" and disp_label == "Rights Information": 
            data["field_rights_information"].append(accessCondition.text)
        
        # add field_contact_information
        if id_type == "use and reproduction" and disp_label == "Contact Information": 
            data["field_contact_information"].append(accessCondition.text)
        
        # add field_access_restrictions
        if id_type == "restrictions on access" and disp_label == "Restrictions on Access": 
            data["field_access_restrictions"].append(accessCondition.text)

    return {key : '|'.join(value) for key, value in data.items()}

#### Milad Notes: Added Pars part ####
def parsePart(root):
    data = {
        'field_caption' : [],
        'field_number' : [],
        'field_title' : [],
    }
    for part in root.findall('part',ns):
        for prt in part.iter():
            if 'caption' in prt.tag :
                data['field_caption'].append(prt.text)
                
            if 'number' in prt.tag :
                data['field_number'].append(prt.text)
                
            if 'title' in prt.tag:
                data['field_title'].append(prt.text)
    return {key : '|'.join(value) for key, value in data.items()}



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
    #Parse originInfo
    oiData = parseOriginInfo(root)
    #Combine publisher with rest of names
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
    #xml_data.update(parseTableOfContents(root))
    # skip targetAudience, no mapping.
    # Parse notes
    xml_data.update(parseNote(root))
    # Parse subjects
    xml_data.update(parseSubject(root))
    #Milad note: Ignore Parse classification
    #xml_data.update(parseClassification(root))
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
    # Parse Location
    xml_data.update(parseLocation(root))
    # Parse AccessCondition
    xml_data.update(parseAccessCondition(root))
    #Parse Part
    xml_data.update(parsePart(root))
    # Look for values in Extension
    # extData = parseExtension(root) #### Milad Notes:no parseExtension ####
    #Milad Note: no mapping for recordInfo data 
    return xml_data
    
def main():
    data = XmlSet()
    directory = 'Data'
    data.input_directory(directory)
    #FIXME OUTPUT SHORTCUT
    #print("large titles {}".format('.'.join(data.oversize('title'))))
    # print("length alt title: {}".format(data.maxlen('field_alt_title')))
    output_filename = 'Test.csv'
    with open(output_filename, 'w', encoding="utf-8") as csv:
        data.print(csv)
main()