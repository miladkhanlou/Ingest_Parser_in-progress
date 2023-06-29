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

#2. Triger the function to get and Write the unique tags and attributes to csv
def MODs(arg):
    modsPaths = []
    files = listdir(arg.input_directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            modsPaths.append("{directory}/{file_name}".format(directory = arg.input_directory, file_name= file))
    return modsPaths


# 1. Parse each XML 
allTags = [] #NEW (All Tags)
allAtrrib = [] #NEW (All Attributes)
uniqueTag_Dict = {} #NEW (Unique TagNames with the number of repitation in a dictionary)
uniqueAttrib_Dict = {} #NEW (Unique Attribute with the number of repitation in a dictionary)
uniqueTag = [] #NEW (Name of the unique attributes)
uniqueAttrib = [] #NEW (Name of the unique Unique Tags)

def MOD_Parse(mods):
    for mod in mods:
        print("Parsing the source MODs for tags/Attributes---------------------------------------- {}".format(mod.split('/')[-1]))
        root = ET.iterparse(mod, events=('start', 'end'))
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


def dataToCsv(arg):
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
    df_attTG.to_csv("{}.csv".format(arg.output_attribsTags), index=0)
    print("An attribute/Tag csv file saved in this directory: {directory}.csv".format(directory = arg))

#<<<<<<<<<<<<<<<<<  Part II: Get the XML Path , check for spelling and errors in each xml path according to Part1 >>>>>>>>>>>>>>>>>>>>>#
def inpute_csv(arg):
    print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
    # print(data_dict)
    return data_dict

######## Parse and get all the paths and errors ########
def parseAll(mods,csv_input):
    print("Parsing MODs...")
    for mod in mods:
        pathName = []
        print("Parsing Target Mods to get xml paths, and error check ---------------------------------------- {}".format(mod.split('/')[-1])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
        root = ET.iterparse(mod, events=('start', 'end'))
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
                        if 'atributes' in csv_input.keys():
                    ### A1) check for any miss-speling in tags and attributes
                            if i not in csv_input["atributes"]:
                                # errors.append(', '.join("{}".format(a[0]) for a in WriteAttributes)) #USED JOIN INSTEAD OF FORMAT
                                errors.append(i) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Attrib_errors
                            if b.tag.split("}")[1] not in csv_input["tags"]:
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

                    if 'atributes' in csv_input.keys():
                ### B2) check for any miss-speling in tags(No attributes as these are tags with no attrib)               
                        if b.tag.split("}")[1] not in csv_input["tags"]:
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
    print("Uniqe paths collected ------------")
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

    print("Unique errors collected ------------")
    return uniqueErrors

######## write to csv ########
def toCSV(allPaths, allErrors, arg):
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

    ## WRITE XML PATHS, ERROR REPORT TO CSV
    DF = pd.DataFrame(xml_paths)
    sorted = DF.sort_values("Repeated", ascending=False)
    sorted.to_csv("{}.csv".format(arg.output_directory), index=False)
    print("A csv file containing unique LDL xml paths, saved in this directory: {directory}.csv".format(directory = arg))




######################## start the xml2workbench process  ########################
def dict_to_df(fromCSV):
    print("Starting the xml to workbench process")
    # print("output of inpute_csv would be a dictionary containing the columns and rows:\n-columns: {keys}".format(keys = list(fromCSV.keys())))
    xml2wb_df = pd.DataFrame(fromCSV)
    #1) only keep rows we need, delete others
    xml2wb_df = xml2wb_df[xml2wb_df['Needed'] == 'yes']
    # print(xml2wb_df)

    return xml2wb_df

def xml2workbench(DataFrame, mods):   
    path_list = [] #list of paths
    pathName = []
    field_with_text = {
        "PID" : []
    }  #Final dictionary
    for Xpaths in list(DataFrame["Fields"]):
        field_with_text[Xpaths] = []
    # print(field_with_text)
    for mod in mods:
        result_dict = {} #the paths with the text in them with the name of paths, it will be epty out in every iteration (perpuse is only for comparison with master csv)

        #Get the PID field:
        string = re.findall(r'[^/]+(?=_MODS)', mod)[0]
        field_with_text["PID"].append(string.replace('_', ':'))
        
        print("Parsing Target Mods to get xml paths ---------------------------------------- {}".format(mod.split('/')[-1])) ## IF FOLDER WITHIN FOLDER => CHANGE THE INDEX NUMBER
        root = ET.iterparse(mod, events=('start', 'end'))
        
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
                
        # print(" <----------------------test result dict--------------------------> ")
        # print(result_dict)
        
        ###compare xml paths we created from the directory of mods to the master csv we parsed before, and write the texts from value of result_dict dictionary to the field defined in master csv        
        Field_from_csv = []
        for paths, values in result_dict.items():
            for Xpaths in list(DataFrame["XMLPath"]):
                if paths in Xpaths:
                    Field_from_csv = DataFrame.loc[DataFrame["XMLPath"] == paths, 'Fields']
                    fieldName = Field_from_csv.to_string(index=False)
                    
                    ## Write results in 'dictionary' and 'the same dataframe' ##
                    if values is not None:
                        ##Dictionary##
                        for value in values:
                            field_with_text[fieldName].append(value)
                    elif values is None:
                        continue
        print({key : '|'.join(value) for key, value in field_with_text.items()})

        # data = {key : '|'.join(value) for key, value in field_with_text.items()}
    print("****DATA****")
    # print(len(data['field_subject_topic']))

    ### by the end of this step, all the texts, which are in a particular xml path are written into a specific field according to the field name, defined in the master csv from librarians!
    ##Join the values into a string:
    # for key, val in field_with_text.items():
    #     joined_string = ' | '.join(str(item) for item in val)
    #     field_with_text[key] = joined_string


    print(" <------------------------------------------------test Dictionary---------------------------------------------------- ")
    # print(field_with_text)

    # index = list(range(len(field_with_text.keys())))
    # field_with_text_ToDF = pd.DataFrame(field_with_text,index= index)
    # print(field_with_text_ToDF)

    # print(" <------------------------------------------------test Dictionary---------------------------------------------------- ")
    # print(field_with_text)
    # print("{} >>> {}".format("Field_2",field_with_text["Field_2"]))
    # test = "PID NAME IS ================ "
    # print(test + field_with_text["PID"])


    
######################## start the xml2workbench process  ########################
#write the fields to a csv
def output_CSV2WB(df, arg):
    path = arg.output_directory
    print(path)
    print(df)
    # df.to_csv("{}.csv".format(arg.output_directory), index=False)
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(df.keys())
        writer.writerow(df.values())

######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def main():
    args = process_command_line_arguments()
    if args.input_directory and args.output_attribsTags:
    # Run the function to get and write the unique tags and attributes (-i,-oat)
        sourceMODs = MODs(args)
        getAttributeTags = MOD_Parse(sourceMODs)
        GetUniques = unique_tag_attrib()
        attribTags2csv = dataToCsv(args)

    # elif args.input_directory and args.output_directory and args.input_csv:
    # # Run the function to get XML paths, check for errors, and write to CSV (-i,-o,-c)
    #     sourceMODs = MODs(args)
    #     imputcsv = inpute_csv(args)
    #     parseTo = parseAll(sourceMODs,imputcsv)
    #     getUniquesPaths = PathRepeatCheck(parseTo)
    #     getUniqueErrors = ErrorRepeatCheck()
    #     writeToCSV = toCSV(getUniquesPaths, getUniqueErrors, args)

    elif args.input_csv and args.input_directory and args.output_directory:
    # Run the function to for xml2wirkbencg process (-ii,-o,-c)
        #if the 'Do we need' column was no, delete the row
        #reads the RDFs one more time, if the xml paths where in the the list of xml paths write to the correct fields
        sourceMODs = MODs(args)
        csv_to_dict = inpute_csv(args)
        transform = dict_to_df(csv_to_dict) 
        xml2wb_process = xml2workbench(transform,sourceMODs)
        # output = output_CSV2WB(xml2wb_process, args)

main()

#Run on LDL_Content data 
#Step1: get the attribute and tags:                 >>> python3 The\ Parser7.py -i Data/LDLContent -oat Output/LDL_Content_attTags_may19 
#Step2: get paths and errors:                       >>> python3 The\ Parser7.py -i Data/LDLContent -o Output/LDLContent_Paths_June -c Output/LDL_Content_attTags_may31.csv
#Step3: run workbench using the csv report:         >>> python3 The\ Parser10.py -i Data/LDLContent -c Output/LDLContent_Paths_may31.csv -o Output/June21_LDLContent_Field_mapping
#For windows: python3 '.\The Parser10.py' -i Data/LDLContent -c Output/LDLContent_Paths_may31.csv -o Output/June22_LDLContent_Field_mapping