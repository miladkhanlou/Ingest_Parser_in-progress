#### WHAT THIS SCRIPT DOES ####
###1.   Attribute and Tag finder for all the collections
###2.   Gets the xml paths of all xmls
###3. write the xml paths, errors in xml paths according to the write tag and attribute

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
paths = [] #paths that will be written
errors = [] #Attribute and Tag Errors
Tag_errors = [] #We can have 2 columns for errors
Attrib_errors = [] #We can have 2 columns for errors

allTags = [] #NEW (All Tags)
allAtrrib = [] #NEW (All Attributes)
clearTags = {} #NEW (Unique TagNames with the number of repitation in a dictionary)
clearAttribs = {} #NEW (Unique Attribute with the number of repitation in a dictionary)
att = [] #NEW (Final Unique attributes with frequencies)
tg = [] #NEW (Final Unique Tags)
TGs = []
ATTs = []
# create the parser, add an argument for the input directory, parse the command line arguments
parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory')
parser.add_argument('-at', '--at_directory', type=str, help='Path for getting attributes and tags')
parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv')
parser.add_argument('-o', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file')

args = parser.parse_args()



#******************** First Part | Parse all the tags and attributes ********************#
################## Parse each XML ##################
def AttTag(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[1]))
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

################## From running the function to Write the results ##################
def write(directory):
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            AttTag("{}/{}".format(directory,file))
    ## Appending the Attributes and frequencey of duplication which are keys and values to a nested list called 'att'
    for clearAttribs_keys,clearAttribs_values in clearAttribs.items():
        att.append([clearAttribs_keys,clearAttribs_values])

    ## Appending the Tags and frequencey of duplication which are keys and values to a nested list called 'tg'
    for clearTags_keys,clearTags_values in clearTags.items():
        tg.append([clearTags_keys,clearTags_values])
    for each in att:
        ATTs.append(each[0])
    for Tags in tg:
        TGs.append(Tags[0])
    print("attribs: {}".format(ATTs))
    print("tags{}".format(TGs))
    

#********** Extra: Info about tags and attributes in each Institution **********#
def tag_attribsInfo(toCSV):
    with open("{}.txt".format(args.output_directory), 'w') as f:
        f.write("#{} List of attributes and Frequency:\n{} \n \n".format(len(att), att))
        f.write("List of attributes:\n{} \n".format(list(i[0] for i in att)))
        f.write("\n------------------------------------------------------------------------------------------\n \n".format(len(att), list(i[0] for i in att)))
        f.write("#{} List of Tags and Frequency:\n{} \n \n".format(len(tg), tg))
        f.write("List of Tags:\n{} \n \n".format(list(i[0] for i in tg)))



#********** Part Two | Get the XML Path and check for spelling and errors in each xml path **********#
def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[2])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            attribs = [] 
            atribValues = []
            WriteAttributes  = []
            attributes = b.attrib
            if len(attributes) > 0:
                for i,j in attributes.items():
                    attribs.append(i)     #Fixing not printing all the attributes
                    atribValues.append(j)    #Fixing not printing all the attributes Values
                    WriteAttributes.append([i,j]) #write as a list as we go into each attribute

            ### 1) check for any miss-speling in tags and attributes
                    if attributes not in ATTs:
                        errors.append(a) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Attrib_errors
                    if b.tag.split("}")[1] not in TGs:
                        errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                    else:
                        continue
            ### 2) Print the xmlPath                
                pathName.append("{} [{}]".format(b.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes))) #USED JOIN INSTEAD OF FORMAT
                yield '/'.join(pathName)

            if len(b.attrib) == 0:
            ### 1) Print the xmlPath                
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)

            ### 2) check for any miss-speling in tags(No attributes as these are tags with no attrib)               
                if b.tag.split("}")[1] not in TGs:
                    errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                else:
                    continue
        else:
            pathName.pop()
    return(pathName)

################## only write the unique Paths to a dictionary ##################
pathsToWrite= {}
## DUPLICATION HANDELING AND COUNT INTO A DICTIONARY ##
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

################## WRITING 'ERRORS', 'COUNTER', 'DUPLICATIONS' TO COLUMNS ##################
def get(Pathdirectory):
    xml_paths = {
        "Repeated": [],
        "errors": [],
        "XMLPath": [] 
    }
    files = listdir(Pathdirectory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            toList("{}/{}".format(Pathdirectory, file))
    ## WRITING 'COUNTER', 'DUPLICATIONS' TO COLUMNS ##
    for k,v in pathsToWrite.items():
        xml_paths["Repeated"].append(v)
        xml_paths["XMLPath"].append(k)

    ## WRITING 'ERRORS' TO A COLUMN ACCORDING TO EACH ROW IN xml_paths ##
    for xmls in xml_paths['XMLPath']:
        x = ''
        for errs in errors:
            if errs in xmls:
                x = errs
        xml_paths['errors'].append(x)

    ## TEST:
    print(len(xml_paths['XMLPath']))
    print(len(xml_paths['errors']))
    print(xml_paths['errors'])
    print("Number of all xml Paths ------------------------------ {}".format(len(paths)))
    print("Number of all Unique Paths ------------------------------{}".format(len(pathsToWrite)))

    ## WRITE TO CSV
    DF = pd.DataFrame(xml_paths)
    sorted = DF.sort_values("Repeated", ascending=False)
    sorted.to_csv("{}.csv".format(args.output_directory), index=False)

######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def run():
    directory = args.at_directory #get all the tgas and attributes
    data = write(directory) #By now we have two lists of tags and attributes
    Pathdirectory = args.input_directory #get xpaths and check each one with attribute and tags
    run = get(Pathdirectory)
    return run
run()


