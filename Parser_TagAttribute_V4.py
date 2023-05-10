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
import argparse

####################################### Default Variables #######################################
allTags = [] #NEW (All Tags)
allAtrrib = [] #NEW (All Attributes)
clearTags = {} #NEW (Unique TagNames with the number of repitation in a dictionary)
clearAttribs = {} #NEW (Unique Attribute with the number of repitation in a dictionary)
att = [] #NEW (Final Unique attributes with frequencies)
tg = [] #NEW (Final Unique Tags)

# create the parser, add an argument for the input directory, parse the command line arguments
parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory')
parser.add_argument('-o', '--output_directory', type=str, help='Path to the input directory')
args = parser.parse_args()

#Date & Time
now = datetime.now()
end = now.strftime("%H:%M:%S")
######################################### Parse each XML #########################################
def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[2]))
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            allTags.append(b.tag.split("}")[1])
            if len(b.attrib) > 0:
                attrib_list = b.attrib
                for k,v in attrib_list.items():
                    allAtrrib.append(k)

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
            parseAll("{}/{}".format(directory,file))
    ## Appending the Attributes which are keys of the clearAttribs to the list of all Attributes which is att
    for clearAttribs_keys,clearAttribs_values in clearAttribs.items():
        att.append([clearAttribs_keys,clearAttribs_values])
        
    ## Appending the Tags which are keys of the clearTags to the list of all Tags which is tg
    for clearTags_keys,clearTags_values in clearTags.items():
        tg.append([clearTags_keys,clearTags_values])

    ## Write to the text file
    with open("{}.txt".format(args.output_directory), 'w') as f:
        f.write("#{} List of attributes and Frequency:\n{} \n \n".format(len(att), att))
        f.write("List of attributes:\n{} \n".format(list(i[0] for i in att)))
        f.write("\n------------------------------------------------------------------------------------------\n \n".format(len(att), list(i[0] for i in att)))
        f.write("#{} List of Tags and Frequency:\n{} \n \n".format(len(tg), tg))
        f.write("List of Tags:\n{} \n \n".format(list(i[0] for i in tg)))



    ## We have the all tags and attributes used in institution by now! Now we can use them tot check for errors:
    ## TEST
    print("#{} List of attributes and Frequency:\n{} \n \n".format(len(att), att))
    print("#{} List of Tags and Frequency:\n{} \n \n".format(len(tg), tg))
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print("clean Tags ------------------------------{}:{}".format(len(clearTags),clearTags))
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print("clean attribs ------------------------------{}:{}".format(len(clearAttribs),clearAttribs))

    ## Print the current time
    print(end)

######################## Final Run ########################
def run():
    directory = args.input_directory
    data = get(directory)
    return data
run()
