#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath
import pandas as pd

# ns = {'':'http://www.loc.gov/mods/v3'}
# mods_to_vocab = {
#     'corporate': 'corporate_body',
#     'personal': 'person',
#     'conference': 'conference'
# }
paths = []
listAtrib = ['displayLabel', 'authority', 'keyDate', 'type', 'encoding', '{http://www.w3.org/1999/xlink}href', 'mimetype', 'point', 'collection', 'qualifier', 'timestamp', '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', 'usage', 'authorityURI', 'lang', 'unit', 'version', 'ID'] 
listTag = ['mods', 'titleInfo', 'title', 'name', 'namePart', 'role', 'roleTerm', 'originInfo', 'publisher', 'dateIssued', 'subject', 'topic', 'typeOfResource', 'relatedItem', 'location', 'url', 'physicalLocation', 'holdingSimple', 'copyInformation', 'shelfLocator', 'accessCondition', 'recordInfo', 'recordOrigin', 'recordCreationDate', 'recordChangeDate', 'languageOfCataloging', 'languageTerm', 'part', 'detail', 'caption', 'number', 'nonSort', 'abstract', 'place', 'placeTerm', 'dateCaptured', 'physicalDescription', 'form', 'extent', 'internetMediaType', 'digitalOrigin', 'language', 'subLocation', 'note', 'identifier', 'recordContentSource', 'extension', 'CONTENTdmData', 'alias', 'pointer', 'dmGetItemInfo', 'dateCreated', 'geographic', 'imageBitDepth', 'digitizedBy', 'cataloger', 'extentArchival', 'colorMode', 'imageResolution', 'edition', 'frameSize', 'creditLine', 'genre', 'partNumber', 'partName', 'hiddenDescription', 'collectionSource', 'hardwareSoftware', 'description', 'affiliation', 'cartographics', 'coordinates', 'imageManipulation', 'subTitle', 'temporal', 'hierarchicalGeographic', 'continent', 'country', 'province', 'region', 'county', 'city', 'citySection', 'fileSize', 'digitalReproduction', 'publicationStatus', 'ASERLsubmission', 'findingAidURL', 'dateOther', 'list', 'transcript', 'occupation'] 
errors = [] #Attribute and Tag Errors
############################################################
Tag_errors = [] #We can have 2 columns for errors
Attrib_errors = [] #We can have 2 columns for errors
############################################################
###### FIXING NOT GETTING ALL THE ATTRIBUTES BECAUSE OF THE WAY I WRITEN THE CODE INCOMPELETE ######
def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[1])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            attribs = [] 
            atribValues = []
            WriteAttributes  = []
            attrbutes = b.attrib
            if len(attrbutes) > 0:
                for i,j in attrbutes.items():
                    attribs.append(i)     #Fixing not printing all the attributes
                    atribValues.append(j)    #Fixing not printing all the attributes Values
                    WriteAttributes.append([i,j]) #write as a list as we go into each attribute

                ### 1) check for any miss-speling in tags and attributes
                    if i not in listAtrib:
                        errors.append(i) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Attrib_errors
                    if b.tag.split("}")[1] not in listTag:
                        errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                    else:
                        continue
        ### 2) Print the xmlPath                
                pathName.append("{} [{}]".format(b.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes))) #USED JOIN INSTEAD OF FORMAT
                yield '/'.join(pathName)
            if len(b.attrib) == 0:
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)
        else:
            pathName.pop()
    for i in pathName:
        paths.append(i)
    return(pathName)
##########################################################################################
pathsToWrite= {}

def toList(ntpath):
    for i in parseAll(ntpath):
        paths.append(i)
    check = set()
    for p in paths:
        key = p
        if p not in check:
            check.add(p)
            pathsToWrite[key] = 1
        else:
            pathsToWrite[key] += 1
    return pathsToWrite

##########################################################################################
def get(directory):
    xml_paths = {
        "Repeated": [],
        "errors": [],
        "XMLPath": [] 
    }
    pathError = []
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            toList("Tests/DataTestXML/{}".format(file))

    for k,v in pathsToWrite.items():
        xml_paths["Repeated"].append(v)
        xml_paths["XMLPath"].append(k)

    # for errs in errors:
    #     for xmls in xml_paths['XMLPath']:
    #         if errs in xmls:
    #             error_check.append("{} --> {}".format(xmls, errs))
    #             # xml_paths['errors'].append(errs)
    #         else:
    #             continue
    #             xml_paths['errors'].append("NONE")
    errors2 = ', '.join(str(errs) for errs in errors)

    for xmls in xml_paths['XMLPath']:
        x = ''
        for errs in errors:
            if errs in xmls:
                x = errs
        xml_paths['errors'].append(x)


    print(len(xml_paths['XMLPath']))
    print(len(xml_paths['errors']))
    print(xml_paths['errors'])




    DF = pd.DataFrame(xml_paths)
    sorted = DF.sort_values("Repeated", ascending=False)
    sorted.to_csv("output_Test.csv", index=False)

#We have the all tags and attributes used in institution by now! Now we can use them to check for errors #############################################################################

    ##TEST###
    print("Number of all xml Paths ------------------------------ {}".format(len(paths)))
    print("Number of all Unique Paths ------------------------------{}".format(len(pathsToWrite)))
    
##########################################################################################
def run():
    directory = 'Tests/DataTestXML'
    data = get(directory)
    return data
run()
