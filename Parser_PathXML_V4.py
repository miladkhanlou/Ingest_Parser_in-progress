#!/usr/bin/env python3

# Todo: add usage here

import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re



ns = {'':'http://www.loc.gov/mods/v3'}
mods_to_vocab = {
    'corporate': 'corporate_body',
    'personal': 'person',
    'conference': 'conference'
}
class XmlSet(object):
    def __init__(self):
        self.docs = []
        self.headers = set()
    def add(self, doc):
        # Add a parsed document/row with its headers
        self.docs.append(doc)
        self.headers.update(doc.keys())
    def print(self,fp):
        ## Write out to CSV file
        tmp = list(self.headers)
        tmp.sort()
        writer = csv.DictWriter(fp, fieldnames=tmp)
        writer.writeheader()
        for doc in self.docs:
            writer.writerow(doc)
    def input_directory(self, directory):
        files = listdir(directory)
        files.sort()
        for filename in files:
            if filename.endswith(".xml"):
                print("parsing {} \n---------------------------------------------------".format(filename))
                self.add(parse_mods(directory + sep + filename))

        
# 1 ##################################################################################### FINDING MISSING XML PATHS INSIDE THE XML MASTER #########################################################################################

def parseAll(root):
    # root = ET.iterparse(filename, events=('start', 'end'))
    pathName = []
    data = { 'xmlPaths': []}
    for a,b in root:
        print(b)
        if a == 'start':
            if len(elem.attrib) > 0:
                pathName.append("{} {}= '{}'".format(elem.tag.split("}")[1], list(elem.attrielem.keys())[0], list(elem.attrielem.values())[0]))
                yield '/'.join(pathName)
                data['xmlPaths'].append(pathName)
            if len(elem.attrib) == 0:
                pathName.append("{}".format(elem.tag.split("}")[1], elem.attrib))
                yield '/'.join(pathName)
                data['xmlPaths'].append(pathName)
        else:
            pathName.pop()
            
    return {key : '|'.join(value) for key, value in data.items()}
#     print(pathName)
# with open('testi.txt', 'w') as t:
#     for i in parseAll('MyTestXML.xml'):
#         t.write(i + '\n')
        

# 2 ##################################################################################### FINDING MISSING XML PATHS INSIDE THE XML MASTER #########################################################################################

# def parseOriginInfo(filename):
#     tree = ET.parse(filename)
#     root = tree.getroot()
#     paths= []
#     for items in root.findall('originInfo', ns):
#         if len(items.attrib)>0:
#            Originaltext = items.tag.split("}")[1] + ' ' + "{}:{}".format(list(items.attrielem.keys())[0],list(items.attrielem.values())[0])
#         else:
#             Originaltext = items.tag.split("}")[1]
#         print("****** {}".format(Originaltext))

#         for childs in items:
#             if len(childs.attrib)>0:
#                 text = Originaltext+ '/' +  childs.tag.split("}")[1] + "{}:{}".format(list(childs.attrielem.keys())[0],list(childs.attrielem.values())[0])
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


        

    


def parse_mods(filename):
    root = ET.iterparse(filename, events=('start', 'end'))
    xml_data = {}
    xml_data.update(parseAll(root))
    return xml_data
    
def main():
    data = XmlSet()
    directory = 'Data'
    data.input_directory(directory)
    # output_filename = 'Test_Missing.csv'
    # with open(output_filename, 'w', encoding="utf-8") as csv:
    #     data.print(csv)
main()