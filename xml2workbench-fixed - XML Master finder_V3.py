#!/usr/bin/env python3

# Todo: add usage here

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
# class XmlSet(object):
#     def __init__(self):
#         self.docs = []
#         self.headers = set()
#     def add(self, doc):
#         # Add a parsed document/row with its headers
#         self.docs.append(doc)
#         self.headers.update(doc.keys())
#     def print(self,fp):
#         ## Write out to CSV file
#         tmp = list(self.headers)
#         tmp.sort()
#         writer = csv.DictWriter(fp, fieldnames=tmp)
#         writer.writeheader()
#         for doc in self.docs:
#             writer.writerow(doc)
#     def input_directory(self, directory):
#         files = listdir(directory)
#         files.sort()
#         for filename in files:
#             if filename.endswith(".xml"):
#                 print("parsing {} \n---------------------------------------------------".format(filename))
#                 self.add(parse_mods(directory + sep + filename))

        
# 1 ##################################################################################### FINDING MISSING XML PATHS INSIDE THE XML MASTER #########################################################################################

def parseAll(filename):
    root = ET.iterparse(filename, events=('start', 'end'))
    pathName = []
    path = []
    for a,b in root:
        # print(b)
        if a == 'start':
            if len(b.attrib) > 0:
                pathName.append("{} {}= '{}'".format(b.tag.split("}")[1], list(b.attrib.keys())[0], list(b.attrib.values())[0]))
                yield '/'.join(pathName)
                # print("******** {} AND {}".format(pathName, type(pathName)))
                path.append(pathName)
                
            # path.append[pathName[-1]]
            if len(b.attrib) == 0:
                pathName.append("{}".format(b.tag.split("}")[1], b.attrib))
                yield '/'.join(pathName)
                # print("-------- {}".format(pathName))
                # print("-------- {}".format(pathName))
                path.append(pathName)
            # path.append[pathName[-1]]
        else:
            pathName.pop()
    return path

def toList(ntpath):
    paths = []
    for i in parseAll(ntpath):
        paths.append(i)
    with open('xmlPaths/{}.txt'.format(ntpath), 'w') as t:
        t.write(ntpath + '\n')
        for i in paths:
            t.write(i + '\n')

def get(directory):
    files = listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            # XML.append("Data/{}".format(file))
            print("parsing {}----------".format(file))
            toList(file)

def run():
    directory = 'Data'
    data = get(directory)
run()


# 2 ##################################################################################### FINDING MISSING XML PATHS INSIDE THE XML MASTER #########################################################################################

# def parseOriginInfo(filename):
#     tree = ET.parse(filename)
#     root = tree.getroot()
#     paths= []
#     for items in root.findall('originInfo', ns):
#         if len(items.attrib)>0:
#            Originaltext = items.tag.split("}")[1] + ' ' + "{}:{}".format(list(items.attrib.keys())[0],list(items.attrib.values())[0])
#         else:
#             Originaltext = items.tag.split("}")[1]
#         print("****** {}".format(Originaltext))

#         for childs in items:
#             if len(childs.attrib)>0:
#                 text = Originaltext+ '/' +  childs.tag.split("}")[1] + "{}:{}".format(list(childs.attrib.keys())[0],list(childs.attrib.values())[0])
#                 paths.append(text)
#             else:
#                 text = Originaltext + "/"+ childs.tag.split("}")[1]
#             print("++++++ {}".format(text))
#             for children in childs:
#                 if children is not None:
#                     text= text + '/' +childs.tag.split("}")[1] + '/' +children.tag.split("}")[1]
#                     paths.append(text)
#                     text = Originaltext
#                 else:
#                     continue
#             text = Originaltext + '/' + childs.tag.split("}")[1]
#             paths.append(text)

#         print("////// {}".format(text))
#     for i in paths:
#         print(i)
#parseOriginInfo('MyTestXML1.xml')


        

    


# def parse_mods(filename):
#     # Prepare to parse XML
#     root = ET.iterparse(filename, events=('start', 'end'))
#     # root = tree.getroot()
#     xml_data = {}
#     xml_data.update(parseRelatedItem(root))
#     return xml_data
    
# def main():
#     data = XmlSet()
#     directory = 'Data'
#     data.input_directory(directory)
#     output_filename = 'Test_Missing.csv'
#     with open(output_filename, 'w', encoding="utf-8") as csv:
#         data.print(csv)
# main()