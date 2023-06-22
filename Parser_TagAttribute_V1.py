#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath
import pandas as pd

ns = {'':'http://www.loc.gov/mods/v3'}
mods_to_vocab = {
    'corporate': 'corporate_body',
    'personal': 'person',
    'conference': 'conference'
}
paths = []
allTags = [] #NEW
allAtrrib = [] #NEW
def parseAll(filename):
    pathName = []
    # print("Parsing ---------------------------------------- {}".format(filename.split('/')[1]))
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            allTags.append(elem.tag.split("}")[1])
            if len(elem.attrib) > 0:
                allAtrrielem.append(list(elem.attrielem.keys())[0])
                pathName.append('{}[@{}="{}"]'.format(elem.tag.split("}")[1], list(elem.attrielem.keys())[0], list(elem.attrielem.values())[0]))
                yield '/'.join(pathName)
            if len(elem.attrib) == 0:
                pathName.append("{}".format(elem.tag.split("}")[1], elem.attrib))
                yield '/'.join(pathName)
        else:
            pathName.pop()
    for i in pathName:
        paths.append(i)
    return(pathName)

#####Logic for duplicated results ######################################################################################
pathsToWrite= {}
clearTags = {} #NEW
clearAttribs = {} #NEW

def toList(ntpath):
    ## PathToWrite = {XMLPath : Number of repitation}
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

########################################################## NEW ##########################################################
###WE CAN NOT USE THIS METHOD BECAUSE IT WILL NOT BE THE SOURCE OF TRUTH, AS IT WILL CHECK TO GET THE TAG AND ATTRIBUTE LIST AS A SOURCE FIRST!
    ##clearTags = {Tag_Name : Number of repitation}
    tagCheck = []
    for TGs in allTags:
        key = TGs
        if TGs not in tagCheck:
            tagCheck.append(TGs)
            clearTags[key] = 0
        else:
            clearTags[key] += 1

    ##clearAttribs = {Attribute_Name : Number of repitation}
    attribCheck = []
    for att in allAtrrib:
        keys = att
        if att not in attribCheck:
            attribCheck.append(att)
            clearAttribs[keys] = 0
        else:
            clearAttribs[keys] += 1
###HOWEVER, WE CAN EITHER CREATE LISTS CONTAINING ALL THE TAGS AND ATTRIBUTES IN XML FILES AND LET THE CODE CHECK THE 'MODS' WITH THOSE
###OR WE CAN HAVE A SEPARATE XML SHEET AS A SOURCE OF TRUTH AND RUN THE ATRIBUTE AND TAG CHECKER ON THOSE >>> SOMETHING LIKE:

# for repeated in xml_paths["XMLPath"]:
#     for T in clearTags:
#         if T not in repeated:
#             count += 1
#             print("{} {}".format(count,repeated))
#######################################################################################################################

#From running the function to Write the results ##########################################################################
def get(directory):
    xml_paths = {
        "Repeated": [],
        "XMLPath": []
    }
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            toList("Data/{}".format(file))

    for k,v in pathsToWrite.items():
        xml_paths["Repeated"].append(v)
        xml_paths["XMLPath"].append(k)

    DF = pd.DataFrame(xml_paths)
    sorted = DF.sort_values("Repeated", ascending=False)
    sorted.to_csv("output.csv", index=False)

    ##TEST###
    for a,b in pathsToWrite.items():
        print("{} , {}".format(a,b))
    print("Number of all xml Paths ------------------------------ {}".format(len(paths)))
    print("Number of all Unique Paths ------------------------------{}".format(len(pathsToWrite)))

    print("clear Tags ------------------------------{}".format(len(clearTags)))
    print(clearTags)
    print("\n")
    print("clear attribs ------------------------------{}".format(len(clearAttribs)))
    print(clearAttribs)


##########################################################################################
def run():
    directory = 'Data'
    data = get(directory)
    return data
run()
