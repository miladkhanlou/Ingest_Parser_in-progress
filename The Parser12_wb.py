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

# create the parser, add an argument for the input directory, parse the command line arguments
def process_command_line_arguments():
    parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
    parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-oat', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file', required=False)
    parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)
    parser.add_argument('-ow', '--output_directory_w', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)

    args = parser.parse_args()

    return args

#<<<<<<<<<<<<<<<<< PART I: Parse xmls and get attribute and tags and write to text file >>>>>>>>>>>>>>>>>>>>>#
#****************** OPTION 1 | Parse xmls and get all the tags and attributes ******************#
def csv_to_df(arg):
    print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
    xml2wb_df = pd.DataFrame(data_dict)
    #1) only keep rows we need, delete others
    xml2wb_df = xml2wb_df[xml2wb_df['Needed'] == 'yes']
    
    return xml2wb_df

## get directory as a filename with arg
class xmlSet(object):
    def __init__(self):
        self.docs = []
        self.headers = set()
    def add(self,doc):
        self.docs.append(doc)
        self.headers.update(doc.keys())
    def xmlMods(self, arg,dataframe):
        files = listdir(arg.input_directory)
        files.sort()
        for file in files:
            if file.endswith(".xml"):
                file_path = "{directory}/{file_name}".format(directory=arg.input_directory, file_name=file)
                print("parsing {}".format(file))
                self.add(parse_mods(file_path,dataframe))  # Pass the data dictionary as an argument to the parse_mods function
    def print(self, fp):
        tmp = list(self.headers)
        tmp.sort(key=lambda x: (isinstance(x, float), x))  # Sort by type (float or string) first, then by value
        writer = csv.DictWriter(fp, fieldnames=tmp)
        writer.writeheader()
        for doc in self.docs:
            writer.writerow(doc)

    # def print(self,fp):
    #     ## Write out to CSV file
    #     tmp = list(self.headers)
    #     tmp.sort()
    #     writer = csv.DictWriter(fp, fieldnames=tmp)
    #     writer.writeheader()
    #     for doc in self.docs:
    #         writer.writerow(doc)
## Main parse function
def parse_mods(filename,DataFrame):
    print(filename)
    root = ET.iterparse(filename, events=('start', 'end'))
    print(root)
    #get pids
    data = {}
    pid = getPid(filename)
    data.update({"PID": pid})
    data.update(xml2workbench(root,DataFrame))
    return data

    #get fields with text
    # data.update(xml2workbench(root))

def getPid(file_name):
    string = re.findall(r'[^/]+(?=_MODS)', file_name)[0]
    string = string.replace('_', ':')
    return string

def xml2workbench(root,data_frame):   
    path_list = [] #list of paths
    pathName = []
    field_with_text = {}  #add fields to dictionary
    for Xpaths in list(data_frame["Fields"]):
        field_with_text[Xpaths] = []
    
    result_dict = {} #the paths with the text in them with the name of paths, it will be epty out in every iteration (perpuse is only for comparison with master csv)
    for a,elem in root:
        if a == 'start':
            ## we are creating xml paths in this condition
            attribs = [] 
            atribValues = []
            WriteAttributes  = []
            attributes = elem.attrib
            if len(attributes) > 0:
                for i,j in attributes.items():
                    attribs.append(i)     #Fixing not printing all the attributes
                    atribValues.append(j)    #Fixing not printing all the attributes Values
                    WriteAttributes.append([i,j]) #write as a list as we go into each attribute
                ### A2) Print the xmlPath                
                pathName.append("{} [{}]".format(elem.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes))) #USED JOIN INSTEAD OF FORMAT
                path = '/'.join(pathName)
                path_list.append(path)
            if len(elem.attrib) == 0:
                ### B1) Print the xmlPath                
                pathName.append("{}".format(elem.tag.split("}")[1], elem.attrib))
                path = '/'.join(pathName)
                path_list.append(path)
        else:
            # Retrieve text from the nested XML path that get closed after the final open one
            if path in path_list and elem.text is not None and elem.text.strip() != "":
                result_dict.setdefault(path, [])
                result_dict[path].append(elem.text.strip())
                # print("Text from {}===========> {}".format(path, elem.text.strip()))
            elif elem.text is None:
                continue
            pathName.pop()
            
    print(" <----------------------test result dict--------------------------> ")
    # print(result_dict)
    
    ##compare xml paths we created from the directory of mods to the master csv we parsed before, and write the texts from value of result_dict dictionary to the field defined in master csv        
    Field_from_csv = []
    for paths, values in result_dict.items():
        for Xpaths in list(data_frame["XMLPath"]):
            if paths in Xpaths:
                Field_from_csv = data_frame.loc[data_frame["XMLPath"] == paths, 'Fields']
                fieldName = Field_from_csv.to_string(index=False)
                
                ## Write results in 'dictionary' and 'the same dataframe' ##
                if values is not None:
                    ##Dictionary##
                    for value in values:
                        field_with_text[fieldName].append(value)
                elif values is None:
                    continue
    # print(field_with_text)
    # return field_with_text
    return{key : '|'.join(value) for key, value in field_with_text.items()}


######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def main():
    args = process_command_line_arguments()
    if args.input_csv and args.input_directory and args.output_directory:
    # Run the function to for xml2wirkbencg process (-ii,-o,-c)
        csv_to_dict = csv_to_df(args) #dataframe containing needed fields
        data = xmlSet()
        data.xmlMods(args,csv_to_dict)
        with open(args.output_directory, 'w') as csv:
            data.print(csv)
main()

#Run on LDL_Content data 
#Step1: get the attribute and tags:                 >>> python3 The\ Parser7.py -i Data/LDLContent -oat Output/LDL_Content_attTags_may19 
#Step2: get paths and errors:                       >>> python3 The\ Parser7.py -i Data/LDLContent -o Output/LDLContent_Paths_June -c Output/LDL_Content_attTags_may31.csv
#Step3: run workbench using the csv report:         >>> python3 The\ Parser10.py -i Data/LDLContent -c Output/LDLContent_Paths_may31.csv -o Output/June21_LDLContent_Field_mapping
#For windows: python3 '.\The Parser10.py' -i Data/LDLContent -c Output/LDLContent_Paths_may31.csv -o Output/June22_LDLContent_Field_mapping