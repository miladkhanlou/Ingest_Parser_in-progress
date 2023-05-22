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

####################################### Global Variables #######################################
paths = [] #paths that will be written
errors = [] #Attribute and Tag Errors
Tag_errors = [] #We can have 2 columns for errors
Attrib_errors = [] #We can have 2 columns for errors





# create the parser, add an argument for the input directory, parse the command line arguments
parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
parser.add_argument('-iat', '--at_directory', type=str, help='Path for getting attributes and tags', required=True)
parser.add_argument('-oat', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file', required=False)
parser.add_argument('-oa', '--output_attribs', type=str, help='Path to the output attributelist text file', required=False)
parser.add_argument('-ot', '--output_tags', type=str, help='Path to the output tag list text file', required=False)
parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)
parser.add_argument('-p', '--output_path', type=str, help='Path to the output csv containing only paths and frequency', required=False)

args = parser.parse_args()

#<<<<<<<<<<<<<<<<< PART I: Parse xmls and get attribute and tags and write to text file >>>>>>>>>>>>>>>>>>>>>#
#****************** OPTION 1 | Parse xmls and get all the tags and attributes ******************#

#2. Triger the function to get and Write the unique tags and attributes to csv
def MODs(directory):
    modsPaths = []
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            modsPaths.append("{directory}/{file_name}".format(directory =directory, file_name= file))

    return modsPaths


# 1. Parse each XML 
allTags = [] #NEW (All Tags)
allAtrrib = [] #NEW (All Attributes)
uniqueTag_Dict = {} #NEW (Unique TagNames with the number of repitation in a dictionary)
uniqueAttrib_Dict = {} #NEW (Unique Attribute with the number of repitation in a dictionary)
uniqueTag = [] #NEW (Name of the unique attributes)
uniqueAttrib = [] #NEW (Name of the unique Unique Tags)

def MOD_Parse(mods):
    print("Parsing the source MODS ---------------------------------------- {}".format(mods.split('/')[-1]))
    root = ET.iterparse(mods, events=('start', 'end'))
    #Get all the attribute and tags
    for a,b in root:
        if a == 'start':
            allTags.append(b.tag.split("}")[1])
            if len(b.attrib) > 0:
                attrib_list = b.attrib
                for k,v in attrib_list.items():
                    allAtrrib.append(k)

def unique_tag_attrib():
    ##uniqueTag_Dict = {Attribute_Name : Number of repitation}
    tagCheck = []
    for TGs in allTags:
        key = TGs
        if TGs not in tagCheck:
            tagCheck.append(TGs)
            uniqueTag_Dict[key] = 0
        else:
            uniqueTag_Dict[key] += 1

    ##uniqueAttrib_Dict = {Attribute_Name : Number of repitation}
    attribCheck = []
    for att in allAtrrib:
        keys = att
        if att not in attribCheck:
            attribCheck.append(att)
            uniqueAttrib_Dict[keys] = 0
        else:
            uniqueAttrib_Dict[keys] += 1

    #lists of attribute names and Tag names for error processing
    for each in uniqueAttrib_Dict.keys():
        uniqueAttrib.append(each)
    for Tags in uniqueTag_Dict.keys():
        uniqueTag.append(Tags)

def dataToCsv():
    data = {
        'atributes': [],
        'atributes frequency' : [],
        'tags': [],
        'tags frequency': []
    }
    
    for att,tg in uniqueAttrib_Dict.items():
        data['atributes'].append(att)
        data['atributes frequency'].append(tg)
    
    for atts,tgs in uniqueTag_Dict.items():
        data['tags'].append(atts)
        data['tags frequency'].append(tgs)

    #fill the columns with less number of rows with empty string
    if len(data['atributes']) != len(data['tags']):
        differnce = len(data['tags']) - len(data['atributes'])
        for insert in range(differnce):
            data['atributes'].append("NONE")
            data['atributes frequency'].append(" ")

    #to write attribute and tags to csv
    df_attTG = pd.DataFrame(data)
    df_attTG.to_csv("{}.csv".format(args.output_attribsTags), index=0)

    #to write attribute csv
    df_attTG = pd.DataFrame({'atributes': data['atributes'],'atributes frequency': data['atributes frequency']})
    df_attTG.to_csv("{}.csv".format(args.output_attribs), index=0)

    #to write tags csv
    df_attTG = pd.DataFrame({'tags': data['tags'],'tags frequency': data['tags frequency']})
    df_attTG.to_csv("{}.csv".format(args.output_tags), index=0)


#<<<<<<<<<<<<<<<<<  Part II: Get the XML Path , check for spelling and errors in each xml path according to Part1 >>>>>>>>>>>>>>>>>>>>>#
def xml_dir(Pathdirectory):
    #Write this as function like load xml mods
    xmlPaths = []
    files = listdir(Pathdirectory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            xmlPaths.append("{directory}/{file_name}".format(directory =Pathdirectory, file_name= file))
    return xmlPaths

######## Parse and get all the paths and errors ########
def parseAll(filename):
    for paths in filename:
        pathName = []
        print("Parsing ---------------------------------------- {}".format(paths.split('/')[-1])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
        root = ET.iterparse(paths, events=('start', 'end'))
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

                ### A1) check for any miss-speling in tags and attributes
                        if i not in uniqueAttrib:
                            # errors.append(', '.join("{}".format(a[0]) for a in WriteAttributes)) #USED JOIN INSTEAD OF FORMAT
                            errors.append(i) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Attrib_errors
                        if b.tag.split("}")[1] not in uniqueTag:
                            errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                        else:
                            continue
                ### A2) Print the xmlPath                
                    pathName.append("{} [{}]".format(b.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes))) #USED JOIN INSTEAD OF FORMAT
                    yield '/'.join(pathName)

                if len(b.attrib) == 0:
                ### B1) Print the xmlPath                
                    pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                    yield '/'.join(pathName)

                ### B2) check for any miss-speling in tags(No attributes as these are tags with no attrib)               
                    if b.tag.split("}")[1] not in uniqueTag:
                        errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                    else:
                        continue
            else:
                pathName.pop()

        allPaths = []
        for Xpaths in pathName:
            allPaths.append(Xpaths)

    return(allPaths)

######## unique Paths ########
def PathRepeatCheck(ntpath):
    pathsAndCounts= {}
    check = set()
    for p in ntpath:
        if p not in check:
            check.add(p)
            pathsAndCounts[p] = 1
        else:
            pathsAndCounts[p] += 1

    return pathsAndCounts

######## unique errors ########
def ErrorRepeatCheck():
    uniqueErrors = []
    #b. Handeling Duplicated Errors in attributes and tags
    for err in errors:
        if err not in uniqueErrors:
            uniqueErrors.append(err)
        else:
            continue

    return uniqueErrors

######## write to csv ########
def toCSV(allPaths, allErrors):
#Output to csv separate function
    xml_paths = {   
        "Repeated": [],
        "errors": [],
        "XMLPath": [] 
    }

    ## WRITING 'COUNTER', 'DUPLICATIONS' TO COLUMNS ##
    for k,v in allPaths.items():
        xml_paths["Repeated"].append(v)
        xml_paths["XMLPath"].append(k)

    ## WRITING 'ERRORS' TO A COLUMN ACCORDING TO EACH ROW IN xml_paths ##
    for xmls in xml_paths['XMLPath']:
        x = []
        for errs in allErrors:
            if errs in xmls:
                x.append(errs)
        xml_paths['errors'].append(", ".join(xs for xs in x))

    ## TEST:
    print(len(xml_paths['XMLPath']))
    print(len(xml_paths['errors']))
    print(xml_paths['errors'])
    print("Number of all xml Paths ------------------------------ {}".format(len(paths)))
    print("Number of all Unique Paths ------------------------------{}".format(len(allPaths)))

    ## WRITE XML PATHS, ERROR REPORT TO CSV
    DF = pd.DataFrame(xml_paths)
    sorted = DF.sort_values("Repeated", ascending=False)
    sorted.to_csv("{}.csv".format(args.output_directory), index=False)

    ## WRITE ONLY XML PATHS TO CSV 
    DFxmls = pd.DataFrame({"XMLPath": xml_paths["XMLPath"], 'Repeated': xml_paths['Repeated']})
    sorted = DFxmls.sort_values("Repeated", ascending=False)
    sorted.to_csv("{}.csv".format(args.output_path), index=False)

######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def main():
    directory = args.at_directory #get all the tgas and attributes
    sourceMODs = MODs(directory)
    GetUniques = unique_tag_attrib()
    to_csv = dataToCsv()
    Pathdirectory = args.input_directory #get xpaths and check each one with attribute and tags
    data = xml_dir(Pathdirectory) #By now we have two lists of tags and attributes
    parseTo = parseAll(data)
    getUniquesPaths = PathRepeatCheck(parseTo)
    getUniqueErrors = ErrorRepeatCheck()
    writeToCSV = toCSV(getUniquesPaths, getUniqueErrors)

main()

##For just getting taggs and attributes:
# >>>python3 The\ Parser2.py -iat <location of source MODs> -oat <output csv location>

##For getting only tags or only attributes:
# >>>python3 The\ Parser2.py -iat Data/TheParser_Test/Source -ot Output/testTag
# >>>python3 The\ Parser2.py -iat Data/TheParser_Test/Source -oa Output/testAtt

##For getting xml paths, error report
# >>>python3 The\ Parser2.py -at <location of source MODs> -ot <output csv location> -i <location of target MODs> -o <output final report csv location>

##For getting xml paths
# >>>python3 The\ Parser2.py -iat Data/TheParser_Test/Source -i Data/TheParser_Test/tryon -p Output/TryonTest
