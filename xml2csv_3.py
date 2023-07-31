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

def process_command_line_arguments():
    parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
    subparsers = parser.add_subparsers(title='Modes', dest='mode', required=True, help='Choose a mode')

    # Build Attributes Tags (BAT): Mode for the first set of arguments
    BAT_parser = subparsers.add_parser('BAT', help='Build Attributes Tags')
    BAT_parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    BAT_parser.add_argument('-oat', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file', required=False)

    # Check Attributes Tags(CAT): Mode for the second set of arguments
    CAT_parser = subparsers.add_parser('CAT', help='Check Attributes Tags')
    CAT_parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)

    # Build Xpaths (BXP): Mode for the second set of arguments
    CAT_parser = subparsers.add_parser('BXP', help='Build Xpaths')
    CAT_parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)

    # Build Xpaths and Check Attributes Tags (CBX): Mode for the second set of arguments
    CAT_parser = subparsers.add_parser('CBX', help='Build xpath, check tags and attributes')
    CAT_parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)

    # xml2wb
    xml2wb_parser = subparsers.add_parser('xml2wb', help='Xml to metadata')
    xml2wb_parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    xml2wb_parser.add_argument('-cc', '--input_clear_csv', type=str, help='Path to the input directory', required=False)
    CAT_parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency and error reports', required=False)

    args = parser.parse_args()

    return args

#Get the directory for part 1 and 2:
def MODs(arg, dataframe):
    files = listdir(arg.input_directory)
    files.sort()

    for file in files:
        if file.endswith(".xml"):
            file_path = "{directory}/{file_name}".format(directory=arg.input_directory, file_name=file)
            print("parsing {}".format(file))
            
            # for argument part2:
            if arg.input_csv:
                root = ET.iterparse(file_path, events=('start', 'end'))
                result = xml_parse(root, dataframe, arg)
                yield result
            else:
                yield file_path

def unique_tag_attrib(allTags,allAtrrib):
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

def uniqData_to_dict(arg):
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
    return toCSV(data,arg)


##### Part II: Get the XML Path , check for spelling and errors in each xml path according to Part1 #####
def get_csv(arg):
    print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
    return data_dict

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
    # print(">>> Uniqe paths collected ------------{}".format(pathsAndCounts))
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

    # print(">>> Unique errors collected ------------{}\n\n".format(uniqueErrors))
    return uniqueErrors

def paths_to_dict(allPaths, allErrors, arg):
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
    return toCSV(xml_paths,arg)

def toCSV(dictionary, arg):
    ## WRITE XML PATHS, ERROR REPORT TO CSV
    DF = pd.DataFrame(dictionary)
    if arg.input_csv is not None:
        sorted = DF.sort_values("Repeated", ascending=False)
        sorted.to_csv("{}.csv".format(arg.output_directory), index=False)
        print("A csv file containing unique LDL xml paths, saved in this directory --> {directory}.csv".format(directory = arg.output_directory))
    else:
        DF.to_csv("{}.csv".format(arg.output_attribsTags), index=0)
        print("An attribute/Tag csv file saved in this directory --> {directory}.csv".format(directory = arg.output_attribsTags))

###### Part III: start the xml2workbench process  ######
#a. load and clean the reference csv containing field names: 
def csv_to_df(arg):
    # print("Reading the input csv, containing Attributes and Tags in LDL collections------------------")
    df_attribTags = pd.read_csv(arg.input_clear_csv)
    columnNames = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in columnNames:
        data_dict[columns] = list(df_attribTags[columns])
    xml2wb_df = pd.DataFrame(data_dict)
    #only keep rows we need, delete others
    xml2wb_df = xml2wb_df[xml2wb_df['Needed'] == 'yes']
    return xml2wb_df

#b. Define the class
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
                self.add(xml2wb_parse_mods(file_path,dataframe,arg))  # Pass the data dictionary as an argument to the parse_mods function
    def print(self, fp):
        tmp = list(self.headers)
        tmp.sort(key=lambda x: (isinstance(x, float), x))  # Sort by type (float or string) first, then by value
        writer = csv.DictWriter(fp, fieldnames=tmp)
        writer.writeheader()
        #docs are two dictionaries in a list of self.docs
        for doc in self.docs:
            for key, value in doc.items():
                if isinstance(value, list): #check to see if object belongs to data type List
                    if len(value) == 0:
                        doc[key] = ""  # Empty list becomes an empty string
                    else:
                        doc[key] = value[0]  # Take the first element from the list
            writer.writerow(doc)

##c. Main parse function
def xml2wb_parse_mods(filename,DataFrame,arg):
    root = ET.iterparse(filename, events=('start', 'end'))
    #get pid names
    data = {}
    pid = getPid(filename)
    data.update({"PID": pid})
    data.update(xml_parse(root,DataFrame,arg))
    return data

def getPid(file_name):
    string = re.findall(r'[^/]+(?=_MODS)', file_name)[0]
    string = string.replace('_', ':')
    return string

def xml_parse(root,data_frame, arg):  
    pathName = [] #list of path created in each iteration
    path_list = [] #list of paths after creation
    first_elem = [] #list of first elemet in each iteration
    result_dict_temp = {} #the paths with the text in them with the name of paths, it will be epty out in every iteration (perpuse is only for comparison with master csv)
    result_dict_final = {} #final paths and values that will be used for comparison with master CSV
    for event,elem in root:
        for child in elem:
            first_elem.append(child.tag)
        if event == 'start' and elem != first_elem[0]:
            allTags.append(event.tag.split("}")[1])
            WriteAttributes  = []
            attributes = elem.attrib
            if len(attributes) > 0:
                attrib_list = event.attrib
                for k,v in attrib_list.items():
                    allAtrrib.append(k)

                for Key,value in attributes.items():
                    WriteAttributes.append([Key,value]) #write as a list as we go into each attribute
                    
                    if arg.input_csv and 'atributes' in data_frame.keys():
                    ### A1) check for any miss-speling in tags and attributes
                        if Key not in data_frame["atributes"]:
                            # errors.append(', '.join("{}".format(a[0]) for a in WriteAttributes)) #USED JOIN INSTEAD OF FORMAT
                            errors.append(Key) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Attrib_errors
                        if elem.tag.split("}")[1] not in data_frame["tags"]:
                            errors.append(elem.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                        else:
                            continue
                    else:
                        continue
                pathName.append("{} [{}]".format(elem.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes))) #USED JOIN INSTEAD OF FORMAT

            if len(elem.attrib) == 0:
                pathName.append("{}".format(elem.tag.split("}")[1], elem.attrib))
                
                if arg.input_csv and 'atributes' in data_frame.keys():
                    if elem.tag.split("}")[1] not in data_frame["tags"]:
                        errors.append(elem.tag.split("}")[1]) #If we want to have 2 columns for errors for TAGS AND ATTRIBUTES, We can APPEND TO Tag_errors
                    else:
                        continue
            path = '/'.join(pathName)
            path_list.append(path)

            # Retrieve text from the nested XML path that get closed after the final open one
            if arg.input_clear_csv and elem.text is not None and elem.text.strip() != "":
                result_dict_temp.setdefault(path, [])
                result_dict_final.setdefault(path, [])
                if elem.text.strip() not in result_dict_temp[path]:  # Check for duplicate values
                    result_dict_temp[path].append(elem.text.strip())
            else:
                continue
            
        #Special Condition when end start is first element in the children: [now it is always true, NEEDS WORK TO SAY ONLY in CHILDS SEE "The Parser16+.py for code"]            
        elif event== 'end' and elem.tag != first_elem[0]:
            pathName.pop()
            
        elif arg.input_clear_csv and event == 'start' and elem.tag == first_elem[0]:
            result_dict_temp = {}
            break
        
        ## concatinate the result of each temporary dictionary an append to dict_values dictionary ONE EACH ITERATION:
        elif arg.input_clear_csv and event== 'end' and elem.tag == first_elem[0]:
            # print("\n*** END THE LOOP FROM START TO END OF FIRDT ELEMENT *** First Tag to start:{} ------ *TAG LOOP* ---> {}".format(first_elem[0].split("}")[-1], result_dict_temp))
            pathName.pop()
            dict_values= {} 
            for keys, list_values in result_dict_temp.items():
                concatenated_string = '--'.join(list_values)
                dict_values[keys] = concatenated_string
                
            ## append to final
            for Key,value in dict_values.items():
                result_dict_final[Key].append(value)

            ## Empty out the temp dict and first element(to get ready for the next loop)
            result_dict_temp = {}
            first_elem.pop(0)

    #for step2
    if arg.input_csv:
        return path_list
    
    #xml2wb
    if arg.input_clear_csv:
        result_dict_final =  {final_key : '|'.join(final_value) for final_key, final_value in result_dict_final.items()}
        # print("\n<<< Final Dictionary >>>\n{}\n".format(result_dict_final))
        return compare_and_write(result_dict_final, data_frame)
    

    
def compare_and_write(final_Dict, data_frame):
    field_with_text = {}  #add fields to dictionary
    for Xpaths in list(data_frame["Fields"]):
        field_with_text[Xpaths] = []
    ##compare xml paths we created from the directory of mods to the master csv we parsed before, and write the texts from value of result_dict dictionary to the field defined in master csv        
    Field_from_csv = []
    for paths, values in final_Dict.items():
        for Xpaths in list(data_frame["XMLPath"]):
            if paths in Xpaths:
                Field_from_csv = data_frame.loc[data_frame["XMLPath"] == paths, 'Fields']
                fieldName = Field_from_csv.to_string(index=False)
                ## Write results in 'dictionary' and 'the same dataframe' ##
                if values is not None:
                    ##Dictionary##
                    if fieldName in field_with_text:
                        field_with_text[fieldName].append(values)
                    else:
                        continue
                elif values is None:
                    continue

    # Delete Null fields:
    for k in field_with_text:
        if k == "nan":
            del field_with_text[k]

    # print("\n<<< Final result with values>>>\n{}\n".format({key: value for key, value in field_with_text.items() if value}))
    return field_with_text
    # return{key : '|'.join(value) for key, value in field_with_text.items()}


######################## Final Run: Get Attributes and Tag list | Get xml Paths | Found errors with comparing attribute & tags with xml paths  ########################
def main():
    args = process_command_line_arguments()
    if args.input_directory and args.output_attribsTags:
    # Run the function to get and write the unique tags and attributes (-i,-oat)
        sourceMODs = MODs(args,dataframe=None)
        attribTags2csv = uniqData_to_dict(args)

    elif args.input_directory and args.output_directory and args.input_csv:
    # Run the function to get XML paths, check for errors, and write to CSV (-i,-o,-c)
        inputCSV = get_csv(args)
        sourceMODs = MODs(args, inputCSV)
        for sourceMOD in sourceMODs:
            getUniquesPaths = PathRepeatCheck(sourceMOD)
            getUniqueErrors = ErrorRepeatCheck()
        writeToCSV = paths_to_dict(getUniquesPaths, getUniqueErrors, args)

    elif args.input_clear_csv and args.input_directory and args.output_directory:
    # Run the function to for xml2wirkbencg process (-ii,-o,-cc)
        #reads the RDFs one more time, if the xml paths where in the the list of xml paths write to the correct fields and text
        csv_to_dict = csv_to_df(args) #dataframe containing needed fields
        data = xmlSet()
        data.xmlMods(args,csv_to_dict)
        with open(args.output_directory, 'w') as csv:
            data.print(csv)
main()





#####Run on LDL_Content data#####
#Step1: get the attribute and tags:
####for mac: >>> python3 The\xml2csv.py -i Data/LDLContent -oat Output/Output/LDL_Content_attTags_July
####For windows: >>>python3 '.\xml2csv_2.py' -i Data/LDLContent -oat Output/Output/LDL_Content_attTags_July

#Step2: get paths and errors:
####for mac: >>> python3 The\xml2csv.py -i Data/LDLContent -c Output/LDL_Content_attTags_July.csv -o Output/LDL_Content_Paths_July
####For windows: >>>python3 '.\xml2csv.py' -i Data/LDLContent -c Output/LDL_Content_attTags_July.csv -o Output/LDL_Content_Paths_July

#Step3: run workbench using the csv report:
####for mac: >>> python3 The\xml2csv.py -i Data/LDLContent -cc Output/LDL_Parser_edited.csv -o Output/June28_LDLContent_Field_mapping.csv
####For windows: >>>python3 '.\xml2csv.py' -i Data/LDLContent -cc Output/LDL_Parser_edited.csv -o Output/July21_LDLContent_Field_mapping_tests.csv