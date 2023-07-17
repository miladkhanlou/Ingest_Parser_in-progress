#!/usr/bin/env python3

# Todo: add usage here

import xml.etree.ElementTree as ET
import csv
from lxml import etree
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
        text += ''
        text += partnumber.text
    partname = titleInfo.find('partName', ns)
    if partname is not None and partname.text is not None:
        text += ''
        text += partname.text
    return text

######################################################################################### FINDING MISSING XML PATHS INSIDE THE XML MASTER #########################################################################################

def parseTitleInfo(root):
    ## In titleInfo We care about type attribute
    data = {
            'TitleInfo_type_missingAttribs' : [], #SHOWING MISSING ATTRIBUTES IN COMPARISON WITH MASTER
            'TitleInfo_Displaylabel_missingAttribs' : [], #SHOWING MISSING ATTRIBUTES IN COMPARISON WITH MASTER
            'TitleInfo_type_Attribs': [], #SHOWING ALL THE ATTRIBUTES IN XML
        }       
    TitleInfo_Master_type_Attribs = ['alternative','translated','abbreviated', 'uniform']

    for titles in root.findall('titleInfo',ns):
        # for titles in titleInfo.iter():
        tag_withNoAttrib = []
        stringToWrite = ''

        ############## If titleInfo has no attributes
        if len(titles.attrib) == 0:
            stringToWrite = '<{}>'.format(titles.tag.split('}')[1])

            for item in titles.iter(): #tags within titleInfo without attributes 
                if len(item.attrib) > 0: #if they have attributes add it to the data dictionary
                    for x in item.attrib: #we use the attribute dictionary to build the xml path
                        keys=x
                        attrib = item.get(x)
                    stringToWrite = stringToWrite + '<{} {}="{}">'.format(item.tag.split('}')[1], keys, attrib)
                    #Add to dictionary accoring to the attribute name
                    if 'type' in keys: #write to type if the attribute within titleInfo tag exists
                        data['TitleInfo_type_missingAttribs'].append(stringToWrite) #Just to be make sure, we do not have this logic
                    if 'DisplayLabel' in keys and attrib not in TitleInfo_Master_type_Attribs: #write to displayLabel if the attribute within titleInfo tag exists
                        data['TitleInfo_Displaylabel_missingAttribs'].append(stringToWrite)

        ############## If titleInfo has attributes
        if len(titles.attrib) > 0:
            for x in titles.attrib: #we use the attribute dictionary to build the xml path
                keys=x
                attrib = titles.get(x)
            if 'type' in keys:
                data['TitleInfo_type_missingAttribs'].append('<{} {}="{}">'.format(titles.tag.split('}')[1],keys,attrib))
            if 'DisplayLabel' in attrib and attrib not in TitleInfo_Master_type_Attribs:
                data['TitleInfo_Displaylabel_missingAttribs'].append('<{} {}="{}">'.format(titles.tag.split('}')[1],keys,attrib))
            for item in titles.iter(): #tags within titleInfo with attributes 
                if len(item.attrib) > 0: #if they have attributes add it to the data dictionary
                    for x in item.attrib: #we use the attribute dictionary to build the xml path
                        keys=x
                        attrib = item.get(x)
                        stringToWrite = stringToWrite + '<{} {}="{}">'.format(item.tag.split('}')[1], keys, attrib)
                    #Add to dictionary accoring to the attribute name
                    if 'type' in keys and item != titles: #write to type if the attribute within titleInfo tag exists AND LET IT KNOW THAT THIS TYPE ATTRIBUTE IS NOT THE PARENT TAG
                        data['TitleInfo_type_missingAttribs'].append(stringToWrite) #Just to be make sure, we do not have this logic
                    if 'DisplayLabel' in keys and attrib not in TitleInfo_Master_type_Attribs: #write to displayLabel if the attribute within titleInfo tag exists
                        data['TitleInfo_Displaylabel_missingAttribs'].append(stringToWrite)


    print('---test TitleInfo---')
    print("Master 'DisplayLabel' attribs ==> {}".format(TitleInfo_Master_type_Attribs))
    print("'Type' attrib values ------> {}".format(data['TitleInfo_type_Attribs']))
    print("Missing 'Type' attrib values ------> {}".format(data['TitleInfo_type_missingAttribs']))
    print("Missing 'DisplayLabel' attrib values ------> {}".format(data['TitleInfo_Displaylabel_missingAttribs']))

    print("\n")
    return {key: '|'.join(value) for key, value in data.items()}

####################################################################################################################################################################################################################################

def parseOriginInfo(root):
    data = {
        'OriginInfo_types': [],
        'OriginInfo_types_missing': [],
        'OriginInfo_DisplayLabel_missing': []
            }
    
    value1 = []
    value2 = []
    value3 = []
    placeTerm_master_type = ['text']

########### 1
    # for child in root.findall("originInfo", ns):
    #     if len(child):   # if there are children, get their text attribute and according to that write in a right field:
    #         for subchild in child:
    #             if len(subchild.attrib) > 0:
    #                 for x in subchild.attrib: #we use the attribute dictionary to build the xml path
    #                     keys=x
    #                     attrib = subchild.get(x)
    #                 if keys == 'type' and attrib not in placeTerm_master_type:
    #                     subchildString = "<{}><{} {}='{}'>".format(child.tag.split("}")[1], subchild.tag.split("}")[1], keys, attrib)
    #                     data['OriginInfo_types_missing'].append(subchildString)
    #                 if keys == 'DisplayLabel':
    #                     subchildString = "<{}><{} {}='{}'>".format(child.tag.split("}")[1], subchild.tag.split("}")[1], keys, attrib)
    #                     data['OriginInfo_DisplayLabel_missing'].append(subchildString) 
    #             else:
    #                 print("<{}><{}>".format(child.tag.split("}")[1], subchild.tag.split("}")[1]))
    #             if len(subchild):  # if there are children in child, get their text attribute and according to that write in a right field:
    #                 for inner_child in subchild:
    #                     if len(inner_child.attrib) > 0:
    #                         for x in inner_child.attrib: #we use the attribute dictionary to build the xml path
    #                             keys=x
    #                             attrib = inner_child.get(x)
    #                         if keys == 'type' and attrib not in placeTerm_master_type:
    #                             childString = "<{}><{}><{} {}= '{}'>".format(child.tag.split("}")[1], subchild.tag.split("}")[1],inner_child.tag.split("}")[1], keys, attrib)
    #                             data['OriginInfo_types_missing'].append(childString)
    #                         if keys == 'DisplayLabel':
    #                             childString = "<{}><{}><{} {}= '{}'>".format(child.tag.split("}")[1], subchild.tag.split("}")[1],inner_child.tag.split("}")[1], keys, attrib)
    #                             data['OriginInfo_DisplayLabel_missing'].append(childString) 
    #                     else:
    #                         print("<{}><{}><{}>".format(child.tag.split("}")[1], subchild.tag.split("}")[1],inner_child.tag.split("}")[1]))

########### 2
    for oi in root.findall('originInfo',ns):
        ancestorTag = '<{}>'.format(oi.tag.split('}')[1]) #write the ancestor's tag name to build the xml
        for parent in oi.findall('*'):
            if len(parent.attrib) == 0:
                parentString = ancestorTag + '<{}>'.format(parent.tag.split('}')[1])
                print(parentString)
            if len(parent.attrib) > 0:
                for x in parent.attrib: #we use the attribute dictionary to build the xml path
                    keys=x
                    attrib = parent.get(x)
                if keys == 'type' and attrib not in placeTerm_master_type:
                    parentString = ancestorTag + '<{} {}="{}">'.format(parent.tag.split('}')[1], keys,attrib)
                    data['OriginInfo_types_missing'].append(parentString)
                if keys == 'DisplayLabel': #we usually do not have Display Lapbel in PlaceTerm buy I added it in case of need
                    parentString = ancestorTag + '<{} {}="{}">'.format(parent.tag.split('}')[1], keys,attrib)
                    data['OriginInfo_DisplayLabel_missing'].append(parentString)                    
            for child in parent.findall("*"):
                if len(child.attrib) == 0:
                    childString = parentString + '<{}>'.format(child.tag.split('}')[1])
                    print(childString)
                if len(child.attrib) > 0:
                    for x in child.attrib: #we use the attribute dictionary to build the xml path
                        keys=x
                        attrib = child.get(x)
                        if keys == 'type' and attrib not in placeTerm_master_type:
                            childString = parentString + '<{} {}="{}">'.format(child.tag.split('}')[1], keys,attrib)
                            data['OriginInfo_types_missing'].append(childString)
                        if keys == 'DisplayLabel':
                            childString = parentString + '<{} {}="{}">'.format(child.tag.split('}')[1], keys,attrib)
                            data['OriginInfo_DisplayLabel_missing'].append(childString)                    # print('- - ' + childString)


########### 3
    # for oi in root.findall('originInfo', ns): #originInfo
    #     # name_tag = '<{}>'.format(oi.tag.split('}')[1])
    #     for item in oi: #place, dataIssued, publisher= No type
    #         name_tag = '<originInfo><{}>'.format(item.tag.split('}')[1])
    #         for elem in item:
    #             if elem is not None:
    #                 data['OriginInfo_types'].append(elem.get('type'))
    #                 if elem.get('type') not in placeTerm_master_type:
    #                     data['OriginInfo_types_missing'].append(name_tag + "<{} type:'{}'>".format(elem.tag.split('}')[1], elem.get('type')))
    
    print('---test OriginInfo---')
    print("This is Master type attribs ==> {}".format(placeTerm_master_type))
    print("origin types --------> {}".format(data['OriginInfo_types']))
    print("Missing origin types --------> {}".format(data['OriginInfo_types_missing']))
    print("Missing origin DisplayLabel --------> {}".format(data['OriginInfo_DisplayLabel_missing']))
    print("\n")

    return {key: ','.join(value) for key, value in data.items()}

####################################################################################################################################################################################################################################

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
    
#
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
####################################################################################################################################################################################################################################
# ### Milad Note: added the functionality to add data for field_local_identifierto write two idnetifiers together, the way librarians wanted e.g TypeName:identifyerText
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
        
    return {key : ','.join(value) for key, value in data.items()}

####################################################################################################################################################################################################################################

#Milad Notes: Fixing name.text:
#we do not have any functionality to get the namePart.text, roleTerm.text and role.text
# def parseNameInfo(root):
    names = root.findall('name', ns)
    return {'field_linked_agent': '|'.join(name_data)}
####################################################################################################################################################################################################################################

# def parsePidFromFilename(filename):
####################################################################################################################################################################################################################################

### Milad Note: added the field_resource_type data in the output by adding logic
# def parseTypeOfResource(root):
    # Only accept 'collection' and 'text'; map to capitalized to match Drupal
    xml_tor = root.findall('typeOfResource', ns)
    tors = []
    return {'field_resource_type': '|'.join(tors)}
####################################################################################################################################################################################################################################
  
# def parseGenre(root):
    xml_genres = root.findall('genre',ns)
    print("*********************** {}".format(xml_genres))
    genres = []
    return {'field_genre': '|'.join(genres)}

####################################################################################################################################################################################################################################

# def parseLanguage(root):
    xml_langs = root.findall('language',ns)
    data = {'field_language': []}

    return {key: ','.join(value) for key, value in data.items()}


####################################################################################################################################################################################################################################

# def parsePhysicalDescription(root):
    data = {
    }
    xml_physDesc = root.findall('physicalDescription',ns)

    return {key: ','.join(value) for key, value in data.items()}
####################################################################################################################################################################################################################################

# def parseAbstract(root):
    data = {
    }
    xml_abstract = root.findall('abstract',ns)
    return {key : ','.join(value) for key, value in data.items()}
####################################################################################################################################################################################################################################

# def parseTargetAudience(root):
    xml_ta = root.findall('targetAudience',ns)
####################################################################################################################################################################################################################################

# def parseNote(root):
    data = {

    }
    ###Milad Notes: data added to field_source_note,field_preferred_citation,field_harmful_content_notice, fieldNoteNew fields according to their attributes and tags
    xml_note = root.findall('note',ns)
    return {key : ','.join(value) for key, value in data.items()}
####################################################################################################################################################################################################################################

# def parseSubject(root):
    data = {
    }
        
    for key, value in data.items():
        if key != "field_subject":
            return {key : '|'.join(value)}
        else: 
            return {key : '--'.join(value)}
####################################################################################################################################################################################################################################

#### Milad note: Add pars location logic
# def parseLocation(root):
    data = {"field_physical_location": [],
            "field_institution_web_site": [], 
            # "field_oclc_symbol": [],
            "field_sublocation": [],
            "field_shelf_location": []
            }
    for location in root.findall('location', ns):
        continue
    return {key : ','.join(value) for key, value in data.items()}
####################################################################################################################################################################################################################################

# def parseAccessCondition(root):
    data = {
    }
    for accessCondition in root.findall('accessCondition',ns):
            continue
    return {key : '|'.join(value) for key, value in data.items()}


### Milad note: Parse name must be mapped currectly
# def parseName(root):

### Milad note: Parse RecordInf must be mapped currectly
# def parsRecordInfo(root):

### Milad note: Parse extention must be mapped currectly
# def parsExtention(root):

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
    # xml_data.update(parsePart(root))
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