import xml.etree.ElementTree as ET
import csv
from os import listdir
import re
import pandas as pd
import argparse

######################################################################## PART I: Get unique Tags and Attributes ########################################################################
paths_counts = {}
check = set()
paths = []                  # Paths that will be written
errors = []                 # Attribute and Tag Errors
Tag_errors = []             # We can have 2 columns for errors
Attrib_errors = []          # We can have 2 columns for errors
all_tags = []               # All Tags
all_atrrib = []             # All Attributes
unique_tag_dict = {}         # Unique TagNames with the number of repetition in a dictionary
unique_attrib_dict = {}      # Unique Attribute with the number of repetition in a dictionary

def process_command_line_arguments():
    parser = argparse.ArgumentParser(description='Attribute and Tag finder for all the collections')
    parser.add_argument('-i', '--input_directory', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-oat', '--output_attribsTags', type=str, help='Path to the output attribute and tag list text file', required=False)
    parser.add_argument('-c', '--input_csv', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-cc', '--input_clear_csv', type=str, help='Path to the input directory', required=False)
    parser.add_argument('-o', '--output_directory', type=str, help='Path to the output csv containing paths, frequency, and error reports', required=False)
    parser.add_argument('-ow', '--output_directory_w', type=str, help='Path to the output csv containing paths, frequency, and error reports', required=False)
    args = parser.parse_args()
    return args

# Get the directory for part 1 and 2:
def MODs(arg, dataframe):
    files = listdir(arg.input_directory)
    files.sort()
    for file in files:
        if file.endswith(".xml"):
            file_path = "{directory}/{file_name}".format(directory=arg.input_directory, file_name=file)
            print("parsing {} ...".format(file))
            root = ET.iterparse(file_path, events=('start', 'end'))
            result = xml_parse(root, dataframe, arg)
            yield result

def unique_tag_attrib(tags, attributes):
    # unique_tag_dict = {tag_Name : Number of repetition}
    tagCheck = []
    for TGs in tags:
        key = TGs
        if TGs not in tagCheck:
            tagCheck.append(TGs)
            unique_tag_dict[key] = 0
        else:
            unique_tag_dict[key] += 1

    # unique_attrib_dict = {Attribute_Name : Number of repetition}
    attrib_check = []
    for att in attributes:
        keys = att
        if att not in attrib_check:
            attrib_check.append(att)
            unique_attrib_dict[keys] = 0
        else:
            unique_attrib_dict[keys] += 1

def uniq_data_to_dict(arg):
    data = {
        'atributes': [],
        'atributes frequency': [],
        'tags': [],
        'tags frequency': []
    }

    for att, duplicates in unique_attrib_dict.items():
        data['atributes'].append(att)
        data['atributes frequency'].append(duplicates)

    for atts, duplicates in unique_tag_dict.items():
        data['tags'].append(atts)
        data['tags frequency'].append(duplicates)

    # Fill the columns with less number of rows with an empty string
    if len(data['atributes']) != len(data['tags']):
        difference = len(data['tags']) - len(data['atributes'])
        for num in range(abs(difference)):
            if data['atributes'] < data['tags']:
                data['atributes'].append("NONE")
                data['atributes frequency'].append(" ")
            if data['tags'] < data['atributes']:
                data['tags'].append("NONE")
                data['tags frequency'].append(" ")

    return to_csv(data, arg)

##### Part II: Get the XML Path, check for spelling and errors in each xml path according to Part 1 #####
def get_csv(arg,argument):
    df_attribTags = pd.read_csv(arg)
    column_names = df_attribTags.columns.tolist()
    data_dict =  {}
    for columns in column_names:
        data_dict[columns] = list(df_attribTags[columns])

    if argument.input_clear_csv:
        xml2wb_df = pd.DataFrame(data_dict)
        xml2wb_df = xml2wb_df[xml2wb_df['Needed'] == 'yes']
        return xml2wb_df
    elif argument.input_csv:    
        return data_dict

def Path_repeat_check(ntpath):
    # unique Paths
    for p in ntpath:
        if p not in check:
            check.add(p)
            paths_counts[p] = 1
        else:
            paths_counts[p] += 1
    return paths_counts

def error_repeat_check():
    unique_errors = []
    for err in errors:
        if err not in unique_errors:
            unique_errors.append(err)
        else:
            continue
    return unique_errors

def paths_to_dict(all_paths, all_errors, arg):
    xml_paths = {
        "Repeated": [],
        "errors": [],
        "XMLPath": []
    }

    # WRITING 'COUNTER', 'DUPLICATIONS' TO COLUMNS
    for k, v in all_paths.items():
        xml_paths["Repeated"].append(v)
        xml_paths["XMLPath"].append(k)

    # WRITING 'ERRORS' TO A COLUMN ACCORDING TO EACH ROW IN xml_paths
    for xmls in xml_paths['XMLPath']:
        x = []
        for errs in all_errors:
            if errs in xmls:
                x.append(errs)
        xml_paths['errors'].append(", ".join(xs for xs in x))
    return to_csv(xml_paths, arg)

def to_csv(dictionary, arg):
    DF = pd.DataFrame(dictionary)
    if arg.input_csv is not None:
        sorted_df = DF.sort_values("XMLPath", ascending=True)
        sorted_df.to_csv("{}.csv".format(arg.output_directory), index=False)
        print("<<< A csv file containing unique LDL xml paths, saved in this directory : {directory}.csv >>>".format(directory=arg.output_directory))
    else:
        DF.to_csv("{}.csv".format(arg.output_attribsTags), index=0)
        print("<<< An attribute/Tag csv file saved in this directory : {directory}.csv >>>".format(directory=arg.output_attribsTags))

###### Part III: Start the xml2workbench process  #####
class xmlSet(object):
    def __init__(self):
        self.docs = []
        self.headers = set()

    def add(self, doc):
        self.docs.append(doc)
        self.headers.update(doc.keys())

    def xmlMods(self, arg, dataframe):
        files = listdir(arg.input_directory)
        files.sort()
        for file in files:
            if file.endswith(".xml"):
                file_path = "{directory}/{file_name}".format(directory=arg.input_directory, file_name=file)
                print("parsing {}\n-----------------------------------".format(file))
                self.add(xml2wb_parse_mods(file_path, dataframe, arg))
                # return xml2wb_parse_mods(file_path, dataframe, arg)

    def print(self, fp):
        tmp = list(self.headers)
        tmp.sort(key=lambda x: (isinstance(x, float), x))
        writer = csv.DictWriter(fp, fieldnames=tmp)
        writer.writeheader()
        for doc in self.docs:
            for key, value in doc.items():
                if isinstance(value, list):
                    if len(value) == 0:
                        doc[key] = ""
                    else:
                        doc[key] = value[0]
            writer.writerow(doc)

def xml2wb_parse_mods(filename, dataframe, arg):
    root = ET.iterparse(filename, events=('start', 'end'))
    data = {}
    pid = getPid(filename)
    data.update({"PID": pid})
    data.update(xml_parse(root, dataframe, arg))
    return data

def getPid(file_name):
    string = re.findall(r'[^/]+(?=_MODS)', file_name)[0]
    string = string.replace('_', ':')
    return string

def xml_parse(root, dataframe, arg):
    all_generated_paths = {}
    path_name = [] 
    path_list = [] 
    first_elem = [] 
    result_dict_temp = {} 
    result_dict_final = {}
    paths_with_multiple_att = []

    for event, elem in root:
        for child in elem:
            first_elem.append(child.tag)
        if event == 'start' and elem != first_elem[0]:
            all_tags.append(elem.tag.split("}")[1])
            Write_Attributes = []
            attributes = elem.attrib
            if len(attributes) > 0:
                for k, v in attributes.items():
                    all_atrrib.append(k)

                if arg.input_csv or arg.input_clear_csv:
                    for Keys, Values in attributes.items():
                        Write_Attributes.append([Keys, Values])
                        if arg.input_csv and 'atributes' in dataframe.keys():
                            if Keys not in dataframe["atributes"]:
                                errors.append(Keys)
                            if elem.tag.split("}")[1] not in dataframe["tags"]:
                                errors.append(elem.tag.split("}")[1])
                            else:
                                continue
                        else:
                            continue
                    if len(attributes) > 1:
                        all_generated_paths = {}
                        for i in Write_Attributes:
                            path_name.append("{} [@{}= '{}']".format(elem.tag.split("}")[1],i[0], i[1]))
                            path = '/'.join(path_name)
                            path_name.pop()
                            path_list.append(path)
                            all_generated_paths[path] = i[1]
                        path_name.append("{} [{}]".format(elem.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in Write_Attributes)))
                        path = '/'.join(path_name)
                        path_list.append(path)
                        all_generated_paths[path] = []

                    elif len(attributes) == 1:
                        path_name.append("{} [{}]".format(elem.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in Write_Attributes)))
                        path = '/'.join(path_name)
                        path_list.append(path)

            if len(attributes) == 0:
                path_name.append("{}".format(elem.tag.split("}")[1], elem.attrib))
                path = '/'.join(path_name)
                path_list.append(path)
                
                if arg.input_csv and 'atributes' in dataframe.keys():
                    if elem.tag.split("}")[1] not in dataframe["tags"]:
                        errors.append(elem.tag.split("}")[1])
                    else:
                        continue
            #appending text to the temporary dictionary: (tag.text or attribute value)       
            if arg.input_clear_csv and elem.text is not None and elem.text.strip() != "":
                if len(all_generated_paths) > 0:
                    for index,paths in enumerate(all_generated_paths):
                        result_dict_temp.setdefault(paths, [])
                        result_dict_final.setdefault(paths, [])
                        if index == len(all_generated_paths) - 1: #This is for the path includes all the attributes in one xpath
                            if elem.text.strip() not in result_dict_temp[paths]: 
                                result_dict_temp[paths].append(elem.text.strip())
                        else: #This is for different permutations of the xpath with different attributes
                            if paths in list(dataframe["XMLPath"]):
                                Field_from_csv = dataframe.loc[dataframe["XMLPath"] == paths, 'att_needed']
                                Field_from_csv = Field_from_csv.to_string(index=False)
                                if Field_from_csv == "yes": #it means if we needed to write attribute's value to (append the attribute value to the value of all_generated_paths dict)
                                    result_dict_temp[paths].append(all_generated_paths[paths])
                                    print("{}-------------------> {}".format(paths, result_dict_temp[paths]))
                                    print("====================================================================================================================================================================")
                    all_generated_paths = [] #reset for the next multiple attribute path

                elif len(all_generated_paths) == 0: #This is for the paths that does not have multiple 
                    result_dict_temp.setdefault(path, [])
                    result_dict_final.setdefault(path, [])
                    if elem.text.strip() not in result_dict_temp[path]: 
                        result_dict_temp[path].append(elem.text.strip())
                    # else:
                    #     result_dict_temp[path].append("")
            else:
                continue

        elif (arg.input_csv) and event== 'end':
            path_name.pop()
            
        elif (arg.input_clear_csv) and event== 'end' and elem.tag != first_elem[0]:
            path_name.pop()

        elif arg.input_clear_csv and event == 'start' and elem.tag == first_elem[0]:
            result_dict_temp = {}
            break

        elif arg.input_clear_csv and event == 'end' and elem.tag == first_elem[0]:
            path_name.pop()
            dict_values = {}
            for keys, list_values in result_dict_temp.items():
                concatenated_string = '--'.join(list_values)
                dict_values[keys] = concatenated_string

            for Key, value in dict_values.items():
                result_dict_final[Key].append(value)

            result_dict_temp = {}
            first_elem.pop(0)

    if dataframe is None and not arg.input_csv:
        return unique_tag_attrib(all_tags, all_atrrib)

    if arg.input_csv:
        return path_list

    if arg.input_clear_csv:
        result_dict_final = {final_key: '|'.join(final_value) for final_key, final_value in result_dict_final.items()}
        return compare_and_write(result_dict_final, dataframe)

def compare_and_write(final_Dict, data_frame):
    field_with_text = {}
    for field_names in list(data_frame["Fields"]):
        field_with_text[field_names] = []
    Field_from_csv = []
    for paths, values in final_Dict.items():
        if paths in list(data_frame["XMLPath"]):
            Field_from_csv = data_frame.loc[data_frame["XMLPath"] == paths, 'Fields']
            field_name = Field_from_csv.to_string(index=False)
            if values is not None:
                if field_name in field_with_text:
                    field_with_text[field_name].append(values)
                else: 
                    continue
    for k in field_with_text:
        if k == "nan":
            del field_with_text[k]

    test_result(field_with_text)
    return field_with_text

def test_result(field_with_text):
    print("TEST RESULT(fields with data) IN CSV:\n")
    counter = 1
    for field, string in field_with_text.items():
        if string != []:
            print("{}) key: {} \n value: {}\n".format(counter, field, string))
            counter = counter + 1
########################################################################
def main():
    args = process_command_line_arguments()
    if args.input_directory and args.output_attribsTags:
        sourceMODs = MODs(args,dataframe=None)
        for sourceMOD in sourceMODs:
            attribTags2csv = uniq_data_to_dict(args)

    elif args.input_directory and args.output_directory and args.input_csv:
        inputCSV = get_csv(args.input_csv,args)
        sourceMODs = MODs(args, inputCSV)
        for sourceMOD in sourceMODs:
            get_uniques_paths = Path_repeat_check(sourceMOD)
            get_unique_errors = error_repeat_check()
        writeto_csv = paths_to_dict(get_uniques_paths, get_unique_errors, args)

    elif args.input_clear_csv and args.input_directory and args.output_directory:
        csv_to_dict = get_csv(args.input_clear_csv,args) #dataframe containing needed fields
        data = xmlSet()
        data.xmlMods(args,csv_to_dict)
        with open(args.output_directory, 'w') as csv:
            data.print(csv)
main()


# Modes:
# Mode1: get the attribute and tags:
# for mac: >>> python3 xml2csv_6.py -i Data/LDLContent -oat Output/step1
# For windows: >>>python3 '.\xml2csv_2.py' -i Data/LDLContent -oat Output/LDL_Content_attTags_July
# --------------------------------------------------------------------------------------------------

# Mode2: get paths and errors: 
# for mac: >>> python3 xml2csv_7.py -i Data/LDLContent -c Output/step1.csv -o Output/step2
# for mac: >>> python3 xml2csv_7.py -i Data/LDLContent -c Output/LDL_Content_attTags_July.csv -o Output/step2
# For windows: >>>python3 '.\xml2csv.py' -i Data/LDLContent -c Output/LDL_Content_attTags_July.csv -o Output/LDL_Content_Paths_July
# --------------------------------------------------------------------------------------------------

# Mode3: run workbench using the csv report:
# for mac: >>> python3 xml2csv_7.py -i Data/LDLContent -cc Output/step2_test_xpaths_varietions_master.csv -o Output/step3_test.csv
# For windows: >>>python3 '.\xml2csv.py' -i Data/LDLContent -cc Output/LDL_Parser_edited.csv -o Output/July21_LDLContent_Field_mapping_tests.csv
# mac_test >>> python3 xml2csv_6.py -i Data/LDLContent -cc Output/step2_test_xpaths_varietions_master.csv -o Output/step3_test.csv
# -------------- -------------- -------------- -------------- -------------- -------------- -------------- -------------- -------------- -------------- -------------- --------------

# NOTES:
# Master CSV is an edited csv file using output csv from mode 2 that Librarian should add informations (columns of field name associated with xpath)in the way that:
# 1) If we want a attribute's value be written in a field specified in master, librarian need to specify the path's row in another column called "att_needed" and say yes to that and also mention the name of the field in the filed column as well
# 2) If we want to only get the text, apperantly, the column "att_needed" should not be filled out and either should be No or empty and the field column should be filled out.
# 3) the only paths that are important for us (either for writing the attribute's value or text in the xpath)
# 4) If we want to have attribute's values in the metadata csv file, we need to have a column that value would be yes for the paths that we need attribute mapping (ex. att_need)