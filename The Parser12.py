#### What to expect ####
###1  Find unique attributes and tags in directory containing xml files
###2  A metadata containing all the possible Xpaths in xml files, alongside of number of repitition and field assosiated with every path.
###3  To get the final metadata for ingesting to LDL, we will parse into the xml files one more time and get paths, then we'll compare those paths to paths in previous step and will create another csv with the right field name and text within new xpath we parsed


import xml.etree.ElementTree as ET
import csv
from lxml import etree
from os import listdir, sep, path
import re
import ntpath
import pandas as pd
from datetime import datetime
import argparse

def process_command_line_arguments():
    parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
    parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-oat', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file', required=False)
    parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-cc', '--input_clear_csv', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)
    parser.add_argument('-ow', '--output_directory_w', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)
    args = parser.parse_args()
    return args

#Get the directory for part 1 and 2:
def MODs(arg):
    modsPaths = []
    files = listdir(arg.input_directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            modsPaths.append("{directory}/{file_name}".format(directory = arg.input_directory, file_name= file))
    return modsPaths

######################################################################## PART I: Gget unique Tags and Attributes ########################################################################
paths = []                  #paths that will be written
errors = []                 #Attribute and Tag Errors
Tag_errors = []             #We can have 2 columns for errors
Attrib_errors = []          #We can have 2 columns for errors
allTags = []                # All Tags)
allAtrrib = []              #(All Attributes)
uniqueTag_Dict = {}         # Unique TagNames with the number of repitation in a dictionary)
uniqueAttrib_Dict = {}      #(Unique Attribute with the number of repitation in a dictionary)
uniqueTag = []              #(Name of the unique attributes)
uniqueAttrib = []           #(Name of the unique Unique Tags)

def MOD_Parse(mods):
    #Get unique attribute and tag
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
    ##uniqueTag_Dict = {tag_Name : Number of repitation}
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



######################################################################## Part II: Get the XML Path , check for spelling and errors in each xml path according to Part1 ########################################################################
def inpute_csv(arg):
    print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
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


def PathRepeatCheck(ntpath):
    # unique Paths 
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

def ErrorRepeatCheck():
    # unique errors 
    uniqueErrors = []
    #bHandeling Duplicated Errors in attributes and tags
    for err in errors:
        if err not in uniqueErrors:
            uniqueErrors.append(err)
        else:
            continue

    print("Unique errors collected ------------")
    return uniqueErrors


def toCSV(allPaths, allErrors, arg):
    # write to csv 
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




######################################################################## Part III: start the xml2workbench process  ########################################################################
def csv_to_df(arg):
    print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_clear_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
    xml2wb_df = pd.DataFrame(data_dict)
    #1) only keep rows we need, delete others
    xml2wb_df = xml2wb_df[xml2wb_df['Needed'] == 'yes']
    
    return xml2wb_df

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

## Main parse function
def parse_mods(filename,DataFrame):
    root = ET.iterparse(filename, events=('start', 'end'))
    #get pid names
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
    test = []
    result_dict = {} #the paths with the text in them with the name of paths, it will be epty out in every iteration (perpuse is only for comparison with master csv)
    for event,elem in root:
        if event == 'start':
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
            # Retrieve text from the nested XML path that get closed after the final open one
            if path in path_list and elem.text is not None and elem.text.strip() != "":
                result_dict.setdefault(path, [])
                result_dict[path].append(elem.text.strip())
            elif elem.text is None:
                continue

        elif event== 'end':
            pathName.pop()
    for i, j in result_dict.items():
        print("{} ----------> {}".format(i,j))
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
                        if fieldName in field_with_text:
                            field_with_text[fieldName].append(value)
                        else:
                            continue
                elif values is None:
                    continue
    for k in field_with_text:
        if k == "nan":
            del field_with_text[k]

    return{key : '|'.join(value) for key, value in field_with_text.items()}



######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def main():
    args = process_command_line_arguments()
    if args.input_directory and args.output_attribsTags:
    # Run the function to get and write the unique tags and attributes (-i,-oat)
        sourceMODs = MODs(args)
        getAttributeTags = MOD_Parse(sourceMODs)
        GetUniques = unique_tag_attrib()
        attribTags2csv = dataToCsv(args)

    elif args.input_directory and args.output_directory and args.input_csv:
    # Run the function to get XML paths, check for errors, and write to CSV (-i,-o,-c)
        sourceMODs = MODs(args)
        inputCSV = inpute_csv(args)
        parseTo = parseAll(sourceMODs,inputCSV)
        getUniquesPaths = PathRepeatCheck(parseTo)
        getUniqueErrors = ErrorRepeatCheck()
        writeToCSV = toCSV(getUniquesPaths, getUniqueErrors, args)

    elif args.input_clear_csv and args.input_directory and args.output_directory:
    # Run the function to for xml2wirkbencg process (-ii,-o,-cc)
        #reads the RDFs one more time, if the xml paths where in the the list of xml paths write to the correct fields and text
        csv_to_dict = csv_to_df(args) #dataframe containing needed fields
        data = xmlSet()
        data.xmlMods(args,csv_to_dict)
        with open(args.output_directory, 'w') as csv:
            data.print(csv)
main()





#Run on LDL_Content data 
#Step1: get the attribute and tags:                 >>> python3 The\ Parser7.py -i Data/LDLContent -oat Output/LDL_Content_attTags_may19 
#Step2: get paths and errors:                       >>> python3 The\ Parser7.py -i Data/LDLContent -o Output/LDLContent_Paths_June -c Output/LDL_Content_attTags_may31.csv
#Step3: run workbench using the csv report:         >>> python3 The\ Parser12.py -i Data/LDLContent -cc Output/LDL_Parser_edited.csv -o Output/June28_LDLContent_Field_mapping.csv
#For windows: python3 '.\The Parser10.py' -i Data/LDLContent -cc Output/LDLContent_Paths_may31.csv -o Output/June22_LDLContent_Field_mapping