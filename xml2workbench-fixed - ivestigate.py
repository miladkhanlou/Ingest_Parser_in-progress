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
                print("parsing {} \n---------------------------------------------------".format(filename))
                self.add(parse_mods(directory + sep + filename))
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

### Milad note: Parse name must be mapped currectly
# def parseName(root):

### Milad note: Parse RecordInf must be mapped currectly
# def parsRecordInfo(root):

### Milad note: Parse extention must be mapped currectly
# def parsExtention(root):

def parseTitleInfo(root):
    ## In titleInfo We care about type attribute
    data = {
            'TitleInfo_type_missingAttribs' : [], #SHOWING MISSING ATTRIBUTES IN COMPARISON WITH MASTER
            'TitleInfo_type_Attribs': [], #SHOWING ALL THE ATTRIBUTES IN XML
        }       
    TitleInfo_Master_type_Attribs = ['alternative','translated','abbreviated', 'uniform']

    for titles in root.findall('titleInfo',ns):
        tag_withNoAttrib = []
        for i in titles.iter(): #iter into all the titleInfo tags, get the all the attributes and their values(type,displayLabel), and fill the xml path
            if len(i.attrib) == 0: #if there were no attributes in the tag, we stop and we append that tag name to the tag_withNoAttrib List==> it will be our first <xmlElement>
                # print('---with No attribute==== {}---'.format(i.tag.split('}')[1]))
                tag_withNoAttrib.append(i.tag.split('}')[1])
            if len(i.attrib) > 0: #if there were attributes we continue:
                # print('---with attribute=== {}---'.format(i.tag.split('}')[1]))
                keys = ''
                attrib = ''
                for x in i.attrib: #we use the attribute dictionary to build the xml path
                    keys=x
                    attrib = i.get(x)
                    if len(tag_withNoAttrib) == 0: ##if there we had the xmlPath that has no attrib we need to specify it in the path 
                        # print('<{} {}={}>'.format(i.tag.split('}')[1],keys, attrib))
                        data['TitleInfo_type_missingAttribs'].append('<{} {}={}>'.format(i.tag.split('}')[1],keys, attrib))
                    else: ##if there we did not hab the xmlPath that has no attrib we need to specify it in the path 
                        # print('<{}><{} {}={}>'.format(tag_withNoAttrib[-1],i.tag.split('}')[1],keys, attrib)) 
                        data['TitleInfo_type_missingAttribs'].append('<{}><{} {}={}>'.format(tag_withNoAttrib[-1],i.tag.split('}')[1],keys, attrib))

                # data['TitleInfo_type_missingAttribs'].append(titles.get('type'))

        else:
            continue

    print('---test TitleInfo---')
    print("This is Master type attribs ==> {}".format(TitleInfo_Master_type_Attribs))
    print("Type attrib values ------> {}".format(data['TitleInfo_type_Attribs']))
    print("Missing Type attrib values ------> {}".format(data['TitleInfo_type_missingAttribs']))
    print("\n")
    return {key: '|'.join(value) for key, value in data.items()}

#Milad Notes: Fixing name.text:
#we do not have any functionality to get the namePart.text, roleTerm.text and role.text
# def parseNameInfo(root):
    names = root.findall('name', ns)
        
    return {'field_linked_agent': '|'.join(name_data)}

# def parsePidFromFilename(filename):
    temp = path.basename(filename)
    temp = temp.replace('_MODS.xml','')
    return temp.replace('_',':',1)

### Milad Note: added the field_resource_type data in the output by adding logic
# def parseTypeOfResource(root):
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
        
        
# def parseGenre(root):
    xml_genres = root.findall('genre',ns)
    print("*********************** {}".format(xml_genres))
    genres = []
    for genre in xml_genres:
        if genre is not None and genre.text is not None:
            genretxt = genre.text
            tmp = genretxt.lower()
            genres.append(tmp)
    return {'field_genre': '|'.join(genres)}

# ### Milad Notes: adding fields in Original info, fixiing the logic to get field_place_of_publication(Should not sepcify .get('type') is None):
def parseOriginInfo(root):
    data = {
        'OriginInfo_types': [],
        'OriginInfo_types_missing': []
            }
    placeTerm_master_type = ['text']
    for oi in root.findall('originInfo', ns): #originInfo
        # name_tag = '<{}>'.format(oi.tag.split('}')[1])
        for item in oi: #place, dataIssued, publisher= No type
            name_tag = '<originInfo><{}>'.format(item.tag.split('}')[1])
            for elem in item:
                if elem is not None:
                    data['OriginInfo_types'].append(elem.get('type'))
                    if elem.get('type') not in placeTerm_master_type:
                        data['OriginInfo_types_missing'].append(name_tag + "<{} type:'{}'>".format(elem.tag.split('}')[1], elem.get('type')))
    
    print('---test OriginInfo---')
    print("This is Master type attribs ==> {}".format(placeTerm_master_type))
    print("origin types --------> {}".format(data['OriginInfo_types']))
    print("Missing origin types --------> {}".format(data['OriginInfo_types_missing']))

    return {key: ','.join(value) for key, value in data.items()}


# def parseLanguage(root):
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
    return {key: ','.join(value) for key, value in data.items()}


# ############## Milad Note: note,internetMediaType,digitalOrigin data added ##############
# def parsePhysicalDescription(root):
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
    return {key: ','.join(value) for key, value in data.items()}

### Milad Note: separated the abstracts into two fields according to the child tag's attribute
# def parseAbstract(root):
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
    return {key : ','.join(value) for key, value in data.items()}

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

# def parseNote(root):
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
    return {key : ','.join(value) for key, value in data.items()}

# def trimXML(text):
    if text is None:
        return ''
    return re.sub('\n* *$','',text)

# def trimXMLlist(list):
    return [trimXML(x) for x in list if trimXML(x) != '']

# def parseSubject(root):
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
# def parseLocation(root):
    data = {"field_physical_location": [],
            "field_institution_web_site": [], 
            # "field_oclc_symbol": [],
            "field_sublocation": [],
            "field_shelf_location": []
            }
    for location in root.findall('location', ns):
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
    
    return {key : ','.join(value) for key, value in data.items()}


def parseRelatedItem(root):
    data = {
        #Milad note: field_is_succeeded_by,field_is_preceded_by are not needed to be parsed
        'relatedItem_types' : [], #all the attribs For reference
        'relatedItem_type_missing' : [],
        'relatedItem_titleInfo_displaylabel' : [], #all the attribs For reference
        'relatedItem_titleInfo_displaylabel_missing' : [],
        'relatedItem_url_displaylabel': [],#all the attribs For reference
        'relatedItem_url_displaylabel_missing': []
    }
    
    xpath = []
    types = ["host"]
    titleInfo_displayLabels = ['Parent Item Title','Digital Collection', 'Repository Collection',]
    url_displayLabels = ['Relation','Repository Collection Guide']
    
    for relatedItem in root.findall('relatedItem',ns):
        #all the attribs For reference
        data['relatedItem_types'].append(relatedItem.get('type')) 
        if relatedItem.get('type') not in types:
            data['relatedItem_type_missing'].append(relatedItem.get('type'))
        for item in relatedItem:
            if item is not None:
                tag_name = "<relatedItem><{}".format(item.tag.split("}")[1])
                #Conditions for items within tags:
                if item.get('displayLabel') is not None:
                    #Condition for both 'location' and 'titleInfo' 
                    if 'location' in item.tag:
                        data['relatedItem_titleInfo_displaylabel'].append(item.get('displayLabel'))  #all the attribs For reference
                        if item.get('displayLabel') not in url_displayLabels:
                            data['relatedItem_url_displaylabel_missing'].append(tag_name + " displayLabel= '{}'>".format(item.get('displayLabel')))
                    #Condition for both 'titleInfo' 
                    if 'titleInfo' in item.tag:
                        data['relatedItem_url_displaylabel'].append(item.get('displayLabel')) #all the attribs For reference
                        if item.get('displayLabel') not in titleInfo_displayLabels:
                            data['relatedItem_titleInfo_displaylabel_missing'].append(tag_name + " displayLabel= '{}'>".format(item.get('displayLabel')))

                if item.get('displayLabel') is None:
                    for child in item:
                        if child.get('displayLabel') is not None:
                            data['relatedItem_titleInfo_displaylabel'].append(child.get('displayLabel'))  #all the attribs For reference
                            tag_name = tag_name + "><{} displayLabel='{}'>".format(child.tag.split("}")[1], child.get('displayLabel'))
                            xpath.append(tag_name)
                            if child.get('displayLabel') not in url_displayLabels:
                                data['relatedItem_url_displaylabel_missing'].append(tag_name)
                                
    print('---test RelatedItem---')
    print("Missing type value --------> {}".format(data['relatedItem_type_missing']))
    print("Missing url labels --------> {}".format(data['relatedItem_url_displaylabel_missing']))
    print("Missing titleInfo labels --------> {}".format(data['relatedItem_titleInfo_displaylabel_missing']))
    print("\n")

    return {key : '|'.join(value) for key, value in data.items()}

# ### Milad Note: added the functionality to add data for field_local_identifier. to write two idnetifiers together, the way librarians wanted e.g TypeName:identifyerText
def parseIdentifier(root):
    data = {
        'identifier_displayLabel_missingAttribs' : [], #SHOWING MISSING ATTRIBUTES IN COMPARISON WITH MASTER
        'identifier_displayLabel_Attribs': [], #SHOWING ALL THE ATTRIBUTES IN XML
    }
    identifier_Master_displayLabel_Attribs = ['Item Number', 'ISBN']
        
    for identifier in root.findall('identifier',ns):
        data['identifier_displayLabel_Attribs'].append(identifier.get('displayLabel'))
        if identifier.get('displayLabel') not in identifier_Master_displayLabel_Attribs:
            data['identifier_displayLabel_missingAttribs'].append(identifier.get('displayLabel'))
            
    print('---test Identifier---')
    print("identifier displaylabel --------> {}".format(data['identifier_displayLabel_Attribs']))
    print("Missing Identifier displaylabel --------> {}".format(data['identifier_displayLabel_missingAttribs']))
    print("\n")
    return {key : ','.join(value) for key, value in data.items()}


#### Milad note: 5 fields added insteaed of field_rights. Codes for field rights commented out ####
# def parseAccessCondition(root):
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
        'part_types': [],
        'part_types_missing': []
    }
    masterType = ['Volume']

    for parts in root.findall('part',ns):
        for child in parts:
            if child.get('type') is not None:
            #master type info
                data['part_types'].append(child.get('type'))
            #missing types
            if child.get('type') not in masterType:
                data['part_types_missing'].append('<part><detail type="{}"'.format(child.get('type')))

    print('---test part---')
    print("This is Master type attribs ==> {}".format(masterType))
    print("Type attrib values ------> {}".format(data['part_types']))
    print("Missing Type attrib values ------> {}".format(data['part_types_missing']))
    print("\n")
    return {key : ','.join(value) for key, value in data.items()}



################################### FILE HANDLING ##########################################

def parse_mods(filename):
    
    # Prepare to parse XML
    tree = ET.parse(filename)
    root = tree.getroot()
    xml_data = {}
    # Parse PID
    # pid = parsePidFromFilename(filename)
    # xml_data.update({'PID': pid,'field_pid': pid})
    # Parse titleinfo
    xml_data.update(parseTitleInfo(root))
    # Parse name
    # xml_data.update(parseNameInfo(root))
    # Parse type of resource
    # xml_data.update(parseTypeOfResource(root))
    # # Parse genre
    # xml_data.update(parseGenre(root))
    #Parse originInfo
    oiData = parseOriginInfo(root)
    # #Combine publisher with rest of names
    # if oiData['field_linked_agent']:
    #     if xml_data['field_linked_agent']:
    #         oiData['field_linked_agent'] = '|'.join([xml_data['field_linked_agent'],oiData['field_linked_agent']])
    # else:
    #     del oiData['field_linked_agent']
    xml_data.update(oiData)
    # Parse language
    # xml_data.update(parseLanguage(root))
    # # Parse physical Description
    # xml_data.update(parsePhysicalDescription(root))
    # # parse abstract
    # xml_data.update(parseAbstract(root))
    # # Parse TableOfContents:
    # #xml_data.update(parseTableOfContents(root))
    # # skip targetAudience, no mapping.
    # # Parse notes
    # xml_data.update(parseNote(root))
    # # Parse subjects
    # xml_data.update(parseSubject(root))
    #Milad note: Ignore Parse classification
    #xml_data.update(parseClassification(root))
    # Parse relatedItem
    relData = parseRelatedItem(root)
    # Append alterations to MODS note properly:
    # if xml_data['field_note']:
    #     if relData['field_note']:
    #         relData['field_note'] = '|'.join([relData['field_note'],xml_data['field_note']])
    #     else:
    #         del relData['field_note']
    xml_data.update(relData)
    # # Parse identifier data
    xml_data.update(parseIdentifier(root))
    # # Parse Location
    # xml_data.update(parseLocation(root))
    # # Parse AccessCondition
    # xml_data.update(parseAccessCondition(root))
    # #Parse Part
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
    output_filename = 'Test_Missing values.csv'
    with open(output_filename, 'w', encoding="utf-8") as csv:
        data.print(csv)
main()