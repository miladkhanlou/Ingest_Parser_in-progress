#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath

ns = {'':'http://www.loc.gov/mods/v3'}
mods_to_vocab = {
    'corporate': 'corporate_body',
    'personal': 'person',
    'conference': 'conference'
}

def parseAll(filename):

    root = ET.iterparse(filename, events=('start', 'end'))
    pathName = []
    path = {}
    count= 0
    print("starting the paths")

    for a,b in root:
        if a == 'start':
            if len(b.attrib) > 0:
                pathName.append("{} {}= '{}'".format(b.tag.split("}")[1], list(b.attrib.keys())[0], list(b.attrib.values())[0]))
                yield '/'.join(pathName)
                path.keys().append(pathName)
                path.values().append(0)
                if pathName in path.keys():
                    path.values(path.values + 1)
            if len(b.attrib) == 0:
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)
                path.keys().append(pathName)
                path.values().append(0)
                if pathName in path.keys():
                    path.values(path.values + 1)        
        else:
            pathName.pop()
    print(path)
parseAll('Data/MyTestXML1')
    
# def get(directory):
#     files = listdir(directory)
#     files.sort()
#     for file in files:
#         if file.endswith(".xml"):
#             print("parsing Data/{}----------".format(file))
#             parseAll("Data/{}".format(file))

# def run():
#     directory = 'Data'
#     data = get(directory)
# run()
