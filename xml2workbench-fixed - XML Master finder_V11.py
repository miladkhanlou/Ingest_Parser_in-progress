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

def parseAll(filename):
    pathName = []
    print("Parsing ---------------------------------------- {}".format(filename.split('/')[1]))
    root = ET.iterparse(filename, events=('start', 'end'))
    for a,b in root:
        if a == 'start':
            if len(b.attrib) > 0:
                pathName.append('{}[@{}="{}"]'.format(b.tag.split("}")[1], list(b.attrib.keys())[0], list(b.attrib.values())[0]))
                yield '/'.join(pathName)
            if len(b.attrib) == 0:
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)
        else:
            pathName.pop()
    for i in pathName:
        paths.append(i)
    return(pathName)

#####Logic for duplicated results ######################################################################################
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
    
##########################################################################################
def run():
    directory = 'Data'
    data = get(directory)
    return data
run()
