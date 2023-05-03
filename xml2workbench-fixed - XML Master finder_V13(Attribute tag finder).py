###Attribute and Tag finder for all the collections
#===================================================#
############################################ Imports ############################################
import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath
import pandas as pd
from datetime import datetime

####################################### Default Variables #######################################
allTags = [] #NEW (All Tags)
allAtrrib = [] #NEW (All Attributes)
clearTags = {} #NEW (Unique TagNames with the number of repitation in a dictionary)
clearAttribs = {} #NEW (Unique Attribute with the number of repitation in a dictionary)
att = [] #NEW (Final Unique attributes)
tg = [] #NEW (Final Unique Tags)

#Date & Time
now = datetime.now()
end = now.strftime("%H:%M:%S")
######################################### Parse each XML #########################################
def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[1]))
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            allTags.append(b.tag.split("}")[1])
            if len(b.attrib) > 0:
                allAtrrib.append(list(b.attrib.keys())[0])

    ##clear tags = {Attribute_Name : Number of repitation}
    tagCheck = []
    for TGs in allTags:
        key = TGs
        if TGs not in tagCheck:
            tagCheck.append(TGs)
            clearTags[key] = 0
        else:
            clearTags[key] += 1

    ##clear attributes = {Attribute_Name : Number of repitation}
    attribCheck = []
    for att in allAtrrib:
        keys = att
        if att not in attribCheck:
            attribCheck.append(att)
            clearAttribs[keys] = 0
        else:
            clearAttribs[keys] += 1

######################## From running the function to Write the results ########################
def get(directory):
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            parseAll("Tests/DataTest/{}".format(file))
    ## Appending the Attributes which are keys of the clearAttribs to the list of all Attributes which is att
    for clearAttribs_keys,clearAttribs_values in clearAttribs.items():
        att.append([clearAttribs_keys,clearAttribs_values])

    ## Appending the Tags which are keys of the clearTags to the list of all Tags which is tg
    for clearTags_keys,clearTags_values in clearTags.items():
        tg.append([clearTags_keys,clearTags_values])

    ## Write to the text file
    with open("Output/Tag_Attribute-{}.txt".format(end), 'w') as f:
        f.write("#{} ATTRIBUTES --> {} \n \n".format(len(att), att))
        f.write("#{} TAGS --> {} \n".format(len(tg), tg))


    ## We have the all tags and attributes used in institution by now! Now we can use them tot check for errors:
    ## TEST
    print("#{} ATTRIBUTES --> {} \n".format(len(att), att))
    print("#{} TAGS --> {} \n".format(len(tg), tg))
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print("clean Tags ------------------------------{}".format(len(clearTags)))
    print(clearTags)
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print("clean attribs ------------------------------{}".format(len(clearAttribs)))
    print(clearAttribs)

    ## Print the current time
    print(end)

######################## Final Run ########################
def run():
    directory = 'Tests/DataTest/'
    data = get(directory)
    return data
run()
