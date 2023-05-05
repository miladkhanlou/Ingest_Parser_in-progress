#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath
import pandas as pd
import argparse


####################################### Default Variables #######################################

#Source of truth to find misspellings and typos for Tests/LDLContent (at the final stage we are gpoing to read from txt file instead of copy and pasting the Tags and Attributes):
listAtrib = ['displayLabel', 'authority', 'type', 'keyDate', 'authorityURI', 'valueURI', '{http://www.w3.org/1999/xlink}href', 'qualifier']
listTag = ['mods', 'titleInfo', 'title', 'name', 'namePart', 'role', 'roleTerm', 'originInfo', 'publisher', 'dateIssued', 'subject', 'topic', 'typeOfResource', 'relatedItem', 'location', 'url', 'physicalLocation', 'holdingSimple', 'copyInformation', 'shelfLocator', 'accessCondition', 'recordInfo', 'recordOrigin', 'recordCreationDate', 'recordChangeDate', 'languageOfCataloging', 'languageTerm', 'part', 'detail', 'caption', 'number', 'nonSort', 'abstract'] 

paths = [] #paths that will be written
errors = [] #Attribute and Tag Errors
Tag_errors = [] #We can have 2 columns for errors
Attrib_errors = [] #We can have 2 columns for errors

####################################### Get unique Paths with frequency of them #######################################

def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[2])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            attribs = [] 
            atribValues = []
            WriteAttributes  = []
            attrbutes = b.attrib
            tagInXML = b.tag
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
            ### 1) Print the xmlPath                
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)

            ### 2) check for any miss-speling in tags(No attributes as these are tags with no attrib)               
                if b.tag.split("}")[1] not in listTag:
                    errors.append(b.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                else:
                    continue
        else:
            pathName.pop()
    return(pathName)

####################################### only write the unique Paths to a dictionary #######################################
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

####################################### WRITING 'ERRORS', 'COUNTER', 'DUPLICATIONS' TO COLUMNS #######################################

def get(directory):
    xml_paths = {
        "Repeated": [],
        "errors": [],
        "XMLPath": [] 
    }
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            toList("{}/{}".format(directory, file))
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
    sorted.to_csv("Output/csv/output_{}.csv".format(directory.split('/')[-1]), index=False)

####################################### Run according to an input directory #######################################

def run():
    # create the parser, add an argument for the input directory, parse the command line arguments
    parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
    parser.add_argument('input_directory', type=str, help='Path to the input directory')
    args = parser.parse_args()
    directory = args.input_directory
    data = get(directory)
    return data
run()
