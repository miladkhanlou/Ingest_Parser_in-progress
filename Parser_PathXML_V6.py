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
print("HELLO")
def parseAll(filename):
    print("Hellowwwww {}".format(filename))
    root = ET.iterparse(filename, events=('start', 'end'))
    pathName = []
    pathKeys = []
    pathValues = []
    myPaths = {}
    count = 0

    for a,b in root:
        if a == 'start':
            if len(b.attrib) > 0:
                pathName.append("{} {}='{}' ".format(b.tag.split("}")[1], list(b.attrib.keys())[0], list(b.attrib.values())[0]))
                yield '/'.join(pathName)
                pathKeys.append(pathName)
                pathValues = 0
                if pathName in pathKeys:
                    pathValues = (pathValues+1) 
            if len(b.attrib) == 0:
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)
                pathKeys.append(pathName)
                pathValues = 0
                if pathName in pathKeys:
                    pathValues += 1
        else:
            pathName.pop()
    
    # for key, value in (pathKeys,pathValues):
    #     newKey = key
    #     myPaths[newKey] = value
    return pathKeys
def toList(ntpath):
    paths = []
    pathsToWrite= {}
    for i in parseAll(ntpath):
        paths.append(i)
    check = set() #I used Set isntead of using a list because if I say if x in list, it checks for availibility of a part of its name
    for p in paths:
        key = p
        if '{}'.format(p) not in check:
            check.add(p)
            pathsToWrite[key] = 1
        else:
            pathsToWrite[key] += 1
    # print(pathsToWrite)
    for z,s in pathsToWrite.items():
        print("{}---{}".format(z, s))

toList("Data/MyTestXML1.xml")
    
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
