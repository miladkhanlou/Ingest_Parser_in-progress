
def xml2workbench(root, data_frame):
    result = {}
    path_list = []  # list of paths
    pathName = []
    first_elem = []
    result_dict_temp = {}  # the paths with the text in them with the name of paths, it will be empty out in every iteration (purpose is only for comparison with master csv)
    result_dict_final = {}

    for event, elem in root:
        for child in elem:
            first_elem.append(child.tag)

    try:
        for event, elem in root:
            if event == 'start' and elem != first_elem[0]:
                WriteAttributes = []
                attributes = elem.attrib
                if len(attributes) > 0:
                    for key, value in attributes.items():
                        WriteAttributes.append([key, value])  # write as a list as we go into each attribute
                    pathName.append("{} [{}]".format(elem.tag.split("}")[1], ", ".join("@{} = '{}'".format(a[0], a[1]) for a in WriteAttributes)))

                if len(elem.attrib) == 0:
                    pathName.append("{}".format(elem.tag.split("}")[1], elem.attrib))

                path = '/'.join(pathName)
                path_list.append(path)

                if path in path_list and elem.text is not None and elem.text.strip() != "":
                    result_dict_temp.setdefault(path, [])
                    result_dict_final.setdefault(path, [])
                    if elem.text.strip() not in result_dict_temp[path]:  # Check for duplicate values
                        result_dict_temp[path].append(elem.text.strip())
                else:
                    continue

            elif event == 'start' and elem.tag == first_elem[0]:
                print("Error happened with '{}' tag | Event = {}".format(elem.tag.split("}")[-1], event))
                result_dict_temp = {}
                raise StopIteration

            elif event == 'end' and elem.tag != first_elem[0]:
                pathName.pop()

            elif event == 'end' and elem.tag == first_elem[0]:
                pathName.pop()

                dict_values = {}
                for key, value_list in result_dict_temp.items():
                    concatenated_string = '--'.join(value_list)
                    dict_values[key] = concatenated_string

                for key, value in dict_values.items():
                    result_dict_final[key].append(value)

                result_dict_temp = {}
                first_elem.pop(0)

    except StopIteration:
        pass

    result_dict_final = {final_key: '|'.join(final_value) for final_key, final_value in result_dict_final.items()}
    print("\n<<< Final Dictionary >>>\n{}\n".format(result_dict_final))
    return compare_and_write(result_dict_final, data_frame)