import re
import collections
import pandas as pd
from abbr import address_abbrev_street_suffix,us_state_to_abbrev

address_keep_list = []
def check_footer_and_notknow_data(data,footer_list,not_know_list,is_longest_address):
    global address_keep_list
    keep_domain_id = []
    address_notknow_keep = []
    for footer_list_data in footer_list:
        if footer_list_data == data['Raw_Address'] and data['Address Location'] == "Footer":
            address_keep_list.append(data['New_Address'])
            keep_domain_id.append(data['Bisnow_Company_UUID'])
            is_longest_address = "Same Addreess"
    for not_know_list_data in not_know_list:
        if not_know_list_data == data['Raw_Address'] and data['Address Location'] == "Not Known":
            address_notknow_keep.append(data['New_Address'])
            is_longest_address = "Not Footer Same Addreess"
    return is_longest_address

def check_footer_and_page_type(data,get_address,is_longest_address,address_and_page_type,raw_address_list):
    if "CONTACT" == data['Page Type']: 
        max_length_value = max(get_address,key=len)
        if max_length_value == data['New_Address']:
            is_longest_address = "Same Addreess"
    else:
        all_value_list = []
        Raw_Address = []
        for address_data in get_address:
            check_footer_or_not = [d[address_data] for d in address_and_page_type if address_data in d]
        footer_list = []
        not_know_list = []
        for dictionary in check_footer_or_not:
            for key,value in dictionary.items():
                all_value_list.append(key)
                if value == 'Footer':
                    footer_list.append(key)
                elif value == 'Not Known':
                    not_know_list.append(key)
        footer_result = {}
        for value in footer_list:
            if value in footer_result:
                footer_result[value].append(value)
            else:
                footer_result[value] = [value]
        for all_value in all_value_list:
            if all_value == data['Raw_Address']:
                Raw_Address.append(all_value)
        if len(Raw_Address) >  1 and all(elem == Raw_Address[0] for elem in Raw_Address):
            footer_lists = []
            not_know_lists = []
            for da in Raw_Address:
                check_footer_or_not = [d[da] for d in raw_address_list if da in d]
            for dictionary in check_footer_or_not:
                for key,value in dictionary.items():
                    if value == "Footer":
                        footer_lists.append(key)
                    elif value == "Not Known":
                        not_know_lists.append(key)
            is_longest_address = check_footer_and_notknow_data(data,footer_lists,not_know_lists,is_longest_address)
        else:
            is_longest_address = check_footer_and_notknow_data(data,footer_list,not_know_list,is_longest_address)
    return is_longest_address

def add_new_address_column(load_exceldata):
    duplicates_id_list = []
    id_and_adderess_list = []
    address_and_page_type = []
    not_footer_same_adderess_id = []
    same_duplicate_address_id = []
    domain_name_list = []
    keep_address_list = []
    delete_address_list  = []
    company_website = []
    address_data_list = []
    raw_address = []
    keep_domain_name_list = []
    Duplicate_Value_list = []
    Keep_Address_Count = []
    new_address_list = []

    us_state_to_abbrev_dict = {value: key for key, value in us_state_to_abbrev.items()}
    combine_dict = {}
    combine_dict.update(us_state_to_abbrev_dict)
    combine_dict.update(address_abbrev_street_suffix)

    for index,adreess_data in load_exceldata.iterrows():

        if type(adreess_data["Raw_Address"]) != float:
            address_string = adreess_data["Raw_Address"]

            for key, value in combine_dict.items():
                address_string = re.sub(r'\b' + re.escape(key) + r'\b', value, address_string, flags=re.IGNORECASE)
            address_data_list.append({adreess_data["Raw_Address"]:re.sub(r'\W', '', address_string).lower()})

        get_address = ""
        if type(adreess_data["Raw_Address"]) != float:
            get_address = [d[adreess_data["Raw_Address"]] for d in address_data_list if adreess_data["Raw_Address"] in d]
            
            get_address = list(set(get_address))
            for address in get_address:
                get_address = address
            if not get_address:
                get_address = re.sub(r'\W', '',adreess_data["Raw_Address"]).lower()
            new_address_list.append(get_address)
        else:
            new_address_list.append(get_address)
    load_exceldata['New_Address'] = new_address_list
        
    for index,data in load_exceldata.iterrows():
        id_and_adderess_list.append({data['Bisnow_Company_UUID']:data['New_Address']})
        address_and_page_type.append({data['New_Address']:{data['Raw_Address']:data['Address Location']}})
        raw_address.append({data['Raw_Address']:{data['Raw_Address']:data['Address Location']}})
        duplicates_id_list.append(data['Bisnow_Company_UUID'])

    id_list = [item for item, count in collections.Counter(duplicates_id_list).items() if count > 1]
    check_value = []
    is_longest_address =  ""
    for index,data in load_exceldata.iterrows():
        if data['Bisnow_Company_UUID'] in id_list:
            get_address = [d[data["Bisnow_Company_UUID"]] for d in id_and_adderess_list if data["Bisnow_Company_UUID"] in d]
            if all(elem == get_address[0] for elem in get_address):
                if len(get_address) > 1:
                    if all(len(get_address[0]) == len(s) for s in get_address):
                        is_longest_address = check_footer_and_page_type(data,get_address,is_longest_address,address_and_page_type,raw_address)       
                else:
                    is_longest_address = True
            else:
                value_dict = {}
                for value in get_address:
                    if value in value_dict:
                        value_dict[value].append(value)
                    else:
                        value_dict[value] = [value]
                unique_lists = [values for values in value_dict.values() if len(values) == 1]
                duplicate_lists = [values for values in value_dict.values() if len(values) > 1]
                if unique_lists:
                    for unique_lists_data in unique_lists:
                        if all(elem == unique_lists_data[0] for elem in unique_lists_data):
                            if len(unique_lists_data) > 1:
                                if all(len(unique_lists_data[0]) == len(s) for s in unique_lists_data):
                                    is_longest_address  = check_footer_and_page_type(data,unique_lists_data,is_longest_address,address_and_page_type,raw_address)
                                else:
                                    is_longest_address = True
                            else:
                                is_longest_address = True
                        else:
                            is_longest_address = True
                if duplicate_lists:
                    for duplicate_lists_data in duplicate_lists:
                        if all(elem == duplicate_lists_data[0] for elem in duplicate_lists_data):
                            if len(duplicate_lists_data) > 1:
                                if all(len(duplicate_lists_data[0]) == len(s) for s in duplicate_lists_data):
                                    is_longest_address  = check_footer_and_page_type(data,duplicate_lists_data,is_longest_address,address_and_page_type,raw_address)
                                else:
                                    is_longest_address = True
                            else:
                                is_longest_address = True
                        else:
                            is_longest_address = True
        else:
            is_longest_address = True
        check_value.append(is_longest_address)
    load_exceldata['Duplicate_Value'] = check_value
    unique_data = {}
    global address_keep_list
    new_addess_and_company_website= []
    defalut_new_address_list = []
    not_footer_new_addess_and_company_website = []
    not_footer_defalut_new_address_list = []
    duplicate_address_list = []
    for index,data in load_exceldata.iterrows():
        for i,j in data.items():
            unique_data[i] = j

        if data["Duplicate_Value"] == True:
            unique_data['Duplicate_Value'] = "Keep"
            Duplicate_Value_list.append("Keep")
       
        if data["Duplicate_Value"] == "Same Addreess":
            defalut_value = True
            if data['New_Address'] not in same_duplicate_address_id  and defalut_value == True:
                unique_data['Duplicate_Value'] = "Keep"
                Duplicate_Value_list.append("Keep")
                domain_name_list.append(data['Bisnow_Company_UUID'])
                same_duplicate_address_id.append(data['New_Address'])
                company_website.append(data['Company_Website'])
                new_addess_and_company_website.append({data['New_Address']:data['Company_Website']})
                defalut_value = False
            else: 
                # if data['Company_Website'] not in company_website and defalut_value == True:
                #     unique_data['Duplicate_Value'] = "Keep"
                #     Duplicate_Value_list.append("Keep")
                #     same_duplicate_address_id.append(data['New_Address'])
                #     new_addess_and_company_website.append({data['New_Address']:data['Company_Website']})
                #     defalut_value = False
                #     company_website.append(data['Company_Website'])
                # else:
                unique_new_address = []
                for a in new_addess_and_company_website:
                    for k,j in a.items():
                        if k == data['New_Address'] and j != data['Company_Website'] and k not in unique_new_address:
                            unique_new_address.append({k:data['Company_Website']})
                if unique_new_address:
                    for l in unique_new_address:
                        for q,m in l.items():
                            if data['New_Address'] == q and  data['Company_Website']  == m and q not in defalut_new_address_list:
                                defalut_new_address_list.append(q)
                                unique_data['Duplicate_Value'] = "Keep"
                                Duplicate_Value_list.append("Keep")
                            else:
                                unique_data['Duplicate_Value'] = "Delete"
                                Duplicate_Value_list.append("Delete")
                else:
                    unique_data['Duplicate_Value'] = "Delete"
                    Duplicate_Value_list.append("Delete")
                    
        if data["Duplicate_Value"]  == "Not Footer Same Addreess":
            not_footer_same_adderess_id.append(data['New_Address'])
            id_list = [item for item, count in collections.Counter(not_footer_same_adderess_id).items() if count > 1]
            defalut_value = True
            if data['New_Address'] in id_list and  defalut_value == True and  data['New_Address'] not in  address_keep_list and data['New_Address'] not in duplicate_address_list:
                duplicate_address_list.append(data['New_Address'])
                unique_data['Duplicate_Value'] =  "Keep"
                Duplicate_Value_list.append("Keep")
                not_footer_new_addess_and_company_website.append({data['New_Address']:data['Company_Website']})
                defalut_value = False
            else:
                unique_new_address = []
                for a in not_footer_new_addess_and_company_website:
                    for k,j in a.items():
                        if k == data['New_Address'] and j != data['Company_Website'] and k not in not_footer_new_addess_and_company_website:
                            unique_new_address.append({k:data['Company_Website']})
                if unique_new_address:
                    for l in unique_new_address:
                        for q,m in l.items():
                            if data['New_Address'] == q and  data['Company_Website']  == m and q not in not_footer_defalut_new_address_list:
                                not_footer_defalut_new_address_list.append(q)
                                unique_data['Duplicate_Value'] = "Keep"
                                Duplicate_Value_list.append("Keep")
                            else:
                                unique_data['Duplicate_Value'] = "Delete"
                                Duplicate_Value_list.append("Delete")
                else:
                    unique_data['Duplicate_Value'] = "Delete"
                    Duplicate_Value_list.append("Delete")
        keep_domain_name_list.append({'Company_Website':unique_data['Company_Website'],"Duplicate_Value":unique_data['Duplicate_Value']})

        if unique_data['Duplicate_Value'] == "Keep":
            keep_address_list.append(unique_data['Company_Website'])
        else:
            delete_address_list.append(unique_data['Company_Website'])

    
    for keep_domain_name in keep_domain_name_list:
        if keep_domain_name['Duplicate_Value'] == "Keep":
            Keep_Address_Count.append(keep_address_list.count(keep_domain_name['Company_Website']))
        else:
            Keep_Address_Count.append(keep_address_list.count(keep_domain_name['Company_Website']))
    
    load_exceldata['Duplicate_Value'] = Duplicate_Value_list
    load_exceldata['Keep_Address_Count'] = Keep_Address_Count
    
    new_address_list = []
    check_value = []
    Duplicate_Value_list = []
    keep_domain_name_list = []
    duplicates_id_list = []
    id_and_adderess_list = []
    address_and_page_type = []
    address_keep_list = [] 
    not_footer_same_adderess_id = []
    same_duplicate_address_id = []
    domain_name_list = []
    keep_address_list = []
    delete_address_list  = []
    company_website = []
    address_data_list = []
    Keep_Address_Count  = []
    raw_address = []
    
    return pd.DataFrame(load_exceldata)

# load_excel = pd.read_excel("C:\\Users\\mayur\\Downloads\\address\\address\\Incorrect_Company_Data_Output_22-06-2023_AD_1_PENDING_OutPut.xlsx")
# df = pd.DataFrame(add_new_address_column(load_excel))
# df.to_excel("Incorrect_OutPut_data.xlsx",index=False)





    
