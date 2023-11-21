import csv
import json
import os
import pandas as pd
import re
from elasticsearch import Elasticsearch, helpers
import copy  
map1 = {}
keywords_list = ['of', 'is', 'a', 'the', 'per', 'tab', 'syr', 'cap', 'fc', 'caplet', 'oral', 'susp', 'oral', 'inj', 'injection', 'soln', 'solution', 'dose', 'sugar-coated', 'forte', 'dry', 'paed', 'for', 'fC', 'drops', 'powd', 'liqd', 'mouthwash', 'rectal', 'oint', 'cream', 'daily', 'facial', 'moisturizer', 'gel', 'inhaler', 'vaccine', 'infant', 'softgel', 'eye', 'ointment', 'effervescent', 'chewtab', 'active', 'captab', 'dispersible', 'xr-fc', 'plus', 'chewable', 'dose:', 'extra', 'adult', 'mite', 'film-coated', 'softcap', 'soft', 'sachet', 'syrup', 'drag', 'bottle', 'mouthspray', 'toothpaste', 'shampoo', 'diskus', 'serum', 'lotion', 'spray']
def get_forms(products):
    forms_list=[]
    products = sorted(products, key=lambda x: len(x['form']), reverse=True)#Get products in descending order
    for product in products:
        forms_list.append(product['form'])
    return forms_list
def append_keywords_from_form_to_keywords_list(forms_list,drug_name): #Append keywords from form and drugName to keywords to map material
    local_keywords_list = copy.deepcopy(keywords_list)
    
    for current_form in forms_list:
        current_form=current_form.split()
        for word in current_form:
            if word.lower() not in local_keywords_list:
                local_keywords_list.append(word.lower())
    for current_drug in drug_name:
        current_drug=current_drug.split()
        for word in current_drug:
            if word.lower() not in local_keywords_list:
                local_keywords_list.append(word.lower())
    print("keywords list for current line item : ",local_keywords_list)
    return local_keywords_list
def get_material(activeIngredients):#
    string_in_bold = []
    # cleaned_active_ingredients = []
    active_ingredients = []
    # activeIngredientsList = activeIngredients
    # find_string_to_split = re.findall(r'\.\s*<strong>', activeIngredients[0])
    # if(find_string_to_split):
    #     # Split the string using the matches
    #     split_active_ingredients = re.split(r'\.\s*<strong>', activeIngredients[0])
    #     # Combine the split parts with the matches to get the desired result
    #     activeIngredientsList = [split_active_ingredients[0]] + [match + split for match, split in zip(find_string_to_split, split_active_ingredients[1:])]
        
    #     print(activeIngredientsList)
    #for item in activeIngredients:
        # bold_words = re.findall(r'\.?\s*<strong>(.*?)</strong>', item)
    for item in activeIngredients:
        item = item.strip('.')
        item = item.replace('&amp;','&')
        item = item.replace(',','')
        item = item.replace(';','')
        item = item.replace('<sup>','^')
        item = item.replace('</sup>','')
        item = item.replace('<sub>','')
        item = item.replace('</sub>','')
        item = item.replace('<strong>','')
        item = item.replace('</strong>','')
        item = item.replace('<em>','') 
        item = item.replace('</em>','')
        item = item.strip()
            # cleaned_active_ingredients.append(re.sub(r'\.?\s*<strong>.*?</strong>', '', item))
            # if(bold_words):
            #     string_in_bold.extend(bold_words)
            #     # cleaned_active_ingredients.append(re.sub(r'\.?\s*<strong>.*?</strong>', '', item))
            #     item = item.replace('<strong>','')
            #     item = item.replace('</strong>','')
            #     active_ingredients.append(item)
        find_index = item.find(':')
        if(find_index!=-1):
            string_in_bold.append(item[:find_index+1])
        else:
            string_in_bold.append('')
        item = item.strip('.')
        active_ingredients.append(item)
    return string_in_bold,active_ingredients
def get_sub_string_from_mat(activeIngredientsList,local_keywords_list): #Get starting substring from material to be mapped with form and then remove
        mat_to_map_list = []
        material_list = []
        for e,entry in enumerate(activeIngredientsList):
            entry=entry.replace('&amp;','&')
            entry=entry.replace(',','')
            entry=entry.replace(';','')
            entry=entry.strip()
            entry=entry.strip('.')
            raw_mat = ''
            dosage_match_in_mat = re.search('[^\w](\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?g\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\sg\s|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\smL\s|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*\s?\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\sL\s|\samp\s|\spuff\s|\sdose\s|\skCal\s|\sbar\s)[^\w]'," "+ entry +" ")
            con_match_in_mat = re.search('\d+\.?\d*\s?%',entry)# add first conc match or dosage match to keywords
            if(dosage_match_in_mat):
                    dosage_matches = dosage_match_in_mat.group(0).split()
                    for match in dosage_matches:
                        if(match.strip() not in local_keywords_list):
                            local_keywords_list.append(match.strip().lower())
            if(con_match_in_mat):
                    con_matches = con_match_in_mat.group(0).split()
                    for match in con_matches:
                        if(match not in local_keywords_list):
                            local_keywords_list.append(match.strip().lower())
            words_in_mat = entry.split()
            for i, word in enumerate(words_in_mat):
                if word.lower() in local_keywords_list:
                    raw_mat += word + ' '
                else:
                    break
#             raw_mat=raw_mat.strip()
            material_list.append(entry)
            mat_to_map_list.append(raw_mat)
            print("raw material to match form : ",mat_to_map_list)
        return mat_to_map_list,material_list
def isRowUnique(row,element):#check if row with highest count is unique
    c = 0
    for i in range(len(row)):
        if (row[i] == element):
            c += 1
            if c > 1:
                return False
    return True

def clearForms(rows,index):#Remove mapped form
    for j , row in enumerate(rows):
        for i, item in enumerate(row["values"]):
            if(i==index):
                rows[j]["values"][i] = -1
    return rows
    
def map_form_to_mat(forms_list,mat_to_map_form,material_list,drug_name):#map form to material with highest count match
    list_of_dicts = []
    for i in range(len(mat_to_map_form)):
        dictionary = {
            "form": forms_list[i],
            "count": 0,
            "activeIngredient":material_list[i],
            "materialToMapForm":mat_to_map_form[i],
            "drugName":""
        }
        list_of_dicts.append(dictionary)
        # arr = [[0]*len(forms_list)]*len(mat_to_map_form)
    rows =[]
    for j,f in enumerate(mat_to_map_form):
        row = {
                "index": j,
                "values":[]
            }
        # current_entry=list_of_dicts[j]
        for k,a in enumerate(forms_list):
#             a=a.lower()
            count=0
            words_in_form=a.split()
            for word in words_in_form:
                if word.lower() in f.lower():
                    count=count+1
            row["values"].append(count)
            # if(current_entry['count']<count):
            #     current_entry['count']=count
                #current_entry['form']=f
        rows.append(row)
    while len(rows) != 0:
        for row in rows:
            max_element = 0
            max_index = 0
            for i , item in enumerate(row["values"]):
                if max_element <= item:
                    max_element = item
                    max_index = i
            if(isRowUnique(row["values"],max_element)):
                print("match form :",max_index,"activeIngredient :",row["index"],list_of_dicts[row["index"]]["materialToMapForm"], forms_list[max_index])
                list_of_dicts[row["index"]]["form"] = forms_list[max_index]
                rows.remove(row)
                rows = clearForms(rows,max_index) 
    #     list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
#     not_found_index=0
#     for l,item in enumerate(list_of_dicts):
#         if(item['form'] in forms_list):
#             forms_list.remove(item['form'])
#         else:
#             not_found_index=l
#     if(len(forms_list)!=0):
#         list_of_dicts[not_found_index]['form']=forms_list[0] 
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['form']), reverse=True)#sort dictionary by form length
    print("mapped dictionary : ",list_of_dicts)
    if(len(drug_name)>1):
        print("map drug name also to form")
        list_of_dicts = map_drug_name_to_mat_and_form(list_of_dicts,drug_name)
    return list_of_dicts

def map_drug_name_to_mat_and_form(list_of_dicts,drug_name):#map drugName to material and form with highest count match   
    for c in list_of_dicts:
        c['count'] = 0 
    for j,d in enumerate(drug_name):
        for k, current_entry in enumerate(list_of_dicts):
            count=0
            words_in_drug_name= d.split()
            for word in words_in_drug_name:
                if word.lower() in current_entry["form"].lower():
                    count=count+1
            if(current_entry['count']<count):
                current_entry['count']=count
                current_entry['drugName']= d
    # not_found_index=0
    # list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
    # for l,item in enumerate(list_of_dicts):
    #     if(item['drugName'] in drug_name):
    #         drug_name.remove(item['drugName'])
    #     else:
    #         not_found_index=l
    # if(len(drug_name)!=0):
    #     list_of_dicts[not_found_index]['drugName']=drug_name[0]
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)#sort dictionary by drugName length
    print("mapped dictionary with drugName: ",list_of_dicts)
    return list_of_dicts
def map_drug_name_to_mat(drug_name_list,mat_to_map_drug,material_list):#map drugName to material with highest count match
    list_of_dicts = []
    for i in range(len(mat_to_map_drug)):
        dictionary = {
            "drugName": drug_name_list[i],
            "count": 0,
            "activeIngredient":material_list[i],
            "materialToMapDrug":mat_to_map_drug[i]
        }
        list_of_dicts.append(dictionary)
    for j,d in enumerate(drug_name_list):
        for k,a in enumerate(mat_to_map_drug):
#             a=a.lower()
            count=0
            current_entry=list_of_dicts[k]
            words_in_drug_name=d.split()
            for word in words_in_drug_name:
                if word.lower() in a.lower():
                    count=count+1
            if(current_entry['count']<count):
                current_entry['count']=count
                current_entry['drugName']=d
    # list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
    # not_found_index=0
    # for l,item in enumerate(list_of_dicts):
    #     if(item['drugName'] in drug_name_list):
    #         drug_name_list.remove(item['drugName'])
    #     else:
    #         not_found_index=l
    # if(len(drug_name_list)!=0):
    #     list_of_dicts[not_found_index]['drugName']=drug_name_list[0]
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)#sort dictionary by form length
    print("mapped dictionary for drugName and material: ",list_of_dicts)
    return list_of_dicts
def map_drug_name_to_form(drug_name_list,forms_list,mat_to_map_form,material_list):#map drugName to form with highest count match
    list_of_dicts = []
    for i in range(len(forms_list)):
        dictionary = {
            "drugName": drug_name_list[i],
            "count": 0,
            "form":forms_list[i],
            "activeIngredient":material_list[0],#No need to map material as it's only single material
            "materialToMapForm":mat_to_map_form[0]
        }
        list_of_dicts.append(dictionary)
    for j,d in enumerate(drug_name_list):
        for k,f in enumerate(forms_list):
            count=0
            current_entry=list_of_dicts[k]
            words_in_drug_name=d.split()
            for word in words_in_drug_name:
                if word.lower() in f.lower():
                    count=count+1
            if(current_entry['count']<count):
                current_entry['count']=count
                current_entry['drugName']=d
#     list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
#     not_found_index=0
#     for l,item in enumerate(list_of_dicts):
#         if(item['drugName'] in drug_name_list):
#             drug_name_list.remove(item['drugName'])
#         else:
#             not_found_index=l
#     if(len(drug_name_list)!=0):
#         list_of_dicts[not_found_index]['drugName']=drug_name_list[0]
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)#sort dictionary by form length
    print("mapped dictionary for drugName and form: ",list_of_dicts)
    return list_of_dicts
def get_matching_material(current_form,current_drug,list_of_dicts):#get matching material for cuurent form
    matching_mat=''
    material_to_map=''
    for m in list_of_dicts :
        if(len(m.get('drugName'))!=0):#Get mapped material for drugName and form
            if m.get('form') == current_form and m.get('drugName') == current_drug:
                print("match found for drugname with form")
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapForm')
                break
        if(len(current_form) == 0):#Get mapped material for drugName
            if  m.get('drugName') == current_drug:
                print("match found for drugname")
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapDrug')
                break
        if(len(m.get('drugName'))==0):
            if m.get('form') == current_form:#Get mapped material for form
                print("match found for form")
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapForm')
                break
    return matching_mat,material_to_map
def get_dosage_from_packaging(dos_match_from_packaging,con_match_from_packaging,d,con,packaging):
    pattern = r'\([^()]*\)'
    dosage_in_packaging = re.search(pattern, packaging)
    if(dosage_in_packaging):
        dos_match_from_packaging = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?spray|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?puff|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered spray|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\s?DHA',dosage_in_packaging.group(0), re.DOTALL)
        con_match_from_packaging= re.findall('\d+\.?\d*\s?%',dosage_in_packaging.group(0), re.DOTALL)
        print("dosage match from packaging",dos_match_from_packaging)
        if(len(dos_match_from_packaging)!=0):
            d = dos_match_from_packaging[0]
            con = ''
        elif(len(con_match_from_packaging) !=0):
            con = con_match_from_packaging
            d = ''
    return d,con
def remove_substring_in_brackets(packaging):
    # Define the regex pattern to check for substrings within brackets
    pattern = r'\([^()]*\)'  # This pattern matches anything between '(' and ')'

    # Use the re.sub() function repeatedly to remove all occurrences of substrings within brackets
    while re.search(pattern, packaging):
        packaging = re.sub(pattern, '', packaging)

    return packaging 

def extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    mat=mat.strip()
    print("current material:",mat)
    if(len(d)==0 and len(con)==0 ):
        dosage_match = re.findall('[^\w](\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered dose|\d+\.?\d*\/?\d*\.?\d*\s?g\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?IU\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?g|d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?IU\/?\-?\d*\.?\d*\s?mL|d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?puff|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL)[^\w]'," "+mat+ " ", re.DOTALL)
        regex_to_match_mL=re.findall('\d*\.?\d*\s?mL',mat, re.DOTALL)
        con_match = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
        if(len(dosage_match)!=0 and len(con_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(mat.startswith('Per '+regex_to_match_mL[0].strip())):#Per <dosage> then append dosage at last
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                else:
                    result+=m
            result=result.replace(' ','')
            result=result.strip('/')
            result=result.strip('.')
            d=result
            result=''
            for m in con_match:
                result+=m+"/"
                result=result.replace(' ','')
            con=result[:-1]
        elif(len(dosage_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(mat.startswith('Per '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                else:
                    result+=m
            result=result.replace(' ','')
            result=result.strip('/')
            result=result.strip('.')
            d=result
            con=''
            print("dosage match :",d)
        elif(len(con_match)!=0):
            result=''
            for m in con_match:
                result+=m+"/"
                result=result.replace(' ','')
            con=result[:-1]
            d=''
        elif(len(dosage_match)==0 and len(con_match)==0 and len(con)==0):
            d=''
            con=''
    if(len(d)==0 and len(con)==0):
        d=''
        con=''
    format_match=re.findall('\sunit dose vial\s|\sPolyamp inj\s|\ssugar-coated caplet\s|\sForte dry syr\s|\sPaed tab\s|\ssoln for inj\s|\sForte FC caplet\s|\sforte cap\s|\spaed drops\s|\spowd for oral liqd\s|\s powd for oral soln\s|\smouthwash\s|\srectal oint\s|\srectal cream\s|\sDaily Facial Moisturizer\s|\sInjection\s|\sForte gel\s|\sdose inhaler\s|\sdose vaccine\s|\sforte dry syr\s|\sForte dry syr\s|\sForte syr\s|\sforte syr\s|\sdry syr\s|\sinfant drops\s|\soral drops\s|\sOral drops\s|\soral liqd\s|\soral gel\s|\ssoftgel\s|\seye gel\s|\sEye Drops\s|\seye drops\s|\sEye Ointment\s|\stab Dry\s|\seffervescent tab\s|\sEffervescent tab\s|\schewtab\s|\sactive tab\s|\scaptab\s|\sDispersible tab\s|\sXR-FC tab\s|\sPlus tab\s|\ssugar-coated tab\s|\sFC tab\s|\schewable tab\s|\sforte tab\s|\sForte tab\s|\sLutevision Extra tab\s|\sAdult tab\s|\sadult tab\s|\smite tab\s|\sfilm-coated tab\s|\ssoftcap\s|\sForte dry susp\s|\sForte oral susp\s|\soral soln\s|\ssoft cap\s|\sForte susp\s|\spaed susp\s|\sforte liqd\s|\sForte cap\s|\sForte caplet\s|\sforte caplet\s|\sfilm-coated caplet\s|\sFC caplet\s|\sdose: Powd for inj\s|\soral susp\s|\ssachet\s|\sSachet\s|\scaplet\s|\sCaplet\s|\stab\s|\sTab\s|\scap\s|\sCap\s|\ssyrup\s|\ssyr\s|\sSyr\s|\sdrops\s|\ssusp\s|\sliqd\s|\spowd\s|\sdrag\s|\sbottle\s|\sForte\s|\sinj\s|\scream\s|\sCream\s|\soint\s|\smouthspray\s|\stoothpaste\s|\sshampoo\s|\sDiskus\s|\sgel\s|\sSerum\s|\slotion\s|\sLotion\s|\ssoln\s|\sspray\s|\svial\s|\sMDV\s'," "+material_to_map+" ", re.DOTALL)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org) 
    if(len(material_to_map)!=0): # Remove raw string from material
#         material_to_map = re.escape(material_to_map)#This ensures that any special characters are treated as literal characters in the regular expression pattern.
#         std_mat = re.sub(material_to_map,'',std_mat ,flags = re.IGNORECASE) #Ignore case while removing raw_string in material
        std_mat = std_mat.replace(material_to_map,'')
        std_mat = std_mat.strip()
        print("Removed raw string from material :",std_mat,"raw material:",material_to_map)
    dosage_match_in_mat = re.findall('[^\w](\d+\.?\d*\/?\d*\.?\d*\s?mmol\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mmol\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?billion cells\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?billion cells\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?million cells\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?million cells\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mOsm\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?billion cells\/?\-?\d*\.?\d*\s?CFU|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?billion cells|\d+\.?\d*\/?\d*\.?\d*\s?mmol\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered dose|\d+\.?\d*\/?\d*\.?\d*\s?mmol\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?g\/?\-?\d*\.?\d*\s?L|\d+\.?\d*\/?\d*\.?\d*\s?IU\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?g|d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?u\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\d*\.?\d*\s?IU\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?g\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?puff|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\smL\s|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?mmol|\d+\.?\d*\/?\-?\d*\.?\d*\s?million cells|\d+\.?\d*\/?\-?\d*\.?\d*\s?billion cells|\d+\.?\d*\/?\-?\d*\.?\d*\s?CFU|\d+\.?\d*\/?\-?\d*\.?\d*\s?mOsm|\d+\.?\d*\/?\-?\d*\.?\d*\s?AU|\d+\.?\d*\/?\-?\d*\.?\d*\s?MU|\d+\.?\d*\/?\-?\d*\.?\d*\s?L)[^\w]'," " +std_mat+ " ", re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',std_mat, re.DOTALL)
    if(len(dosage_match_in_mat)==0 and len(con_match_in_mat)==0):
        current_mat=mat
        std_mat=re.sub(r'\s+', ' ', std_mat)
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0 and len(con_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.replace('v/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip() 
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
        std_mat=std_mat.strip('/')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    elif(len(con_match_in_mat)!=0):
        current_mat=mat
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.replace('v/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    if(len(format_match)!=0):
        std_mat=std_mat.replace(format_match[0].strip(),'')
        current_std_mat=std_mat
    print("std material : ",current_std_mat)
    return d,con,current_mat,current_std_mat,format_org,std_format
def get_uom_details(std_amount,std_uom):
    unit_price = ''   
    quantity = 1
    uom_dosage = ''
    sub_split = []
    if 'x' in std_uom : 
        split =  std_uom.split('x');        
        if len(split) == 1 : 
            if "one" in map1.keys():
                map1["one"] = map1["one"] + 1
            else :
                map1["one"] = 1
        elif len(split) == 2 :
            if "two" in map1.keys():
                map1["two"] = map1["two"] + 1
            else :
                 map1["two"] = 1
        elif len(split) == 3:
            if "three" in map1.keys():
                map1["three"] = map1["three"] + 1
            else :
                map1["three"] = 1
        elif len(split) == 4:
            if "four" in map1.keys():
                map1["four"] = map1["four"] + 1
            else :
                map1["four"] = 1
        else:
            # print (f"new combination of UOM found ignoring now: index : {index}  {uom} \n")
            if "new_combination" in map1.keys():
                map1["new_combination"] += 1
            else :
                map1["new_combination"] = 1


        first_element = split[0]
        is_only_digits = 1;
        for elem in split:
            if re.search( r'^\d+(\.\d+)?$', elem): 
                elem = int(elem)
                # if not isinstance(elem, str):
                    # print(elem)
                if elem and elem > 0 :
                    quantity *= elem
                    print("quantity:",quantity)
            else:
                is_only_digits = 0;
                if uom_dosage == "":
                    uom_dosage += elem
                else: 
                    uom_dosage += 'x' + elem
        
        if is_only_digits:
            uom_dosage = first_element
        if std_amount and std_amount > 0 :
            unit_price = round(std_amount / quantity,2)
    else:
        if std_uom == "":
            if "empty" in map1.keys():
                map1["empty"] += 1
            else :
                map1["empty"] = 1
        elif re.search( r'^\d+$',std_uom) :
            if "one" in map1.keys():
                map1["one"] += 1
            else :
                map1["one"] = 1
        else: 
            sub_split = re.findall(r'(\d+)([a-z]+)', std_uom)
            if len(sub_split) > 0 :
                unit = sub_split[0][1]
                if "unit" in map1.keys():
                    if unit in map1["unit"].keys():                    
                        map1["unit"][unit] += 1
                    else:
                        map1["unit"][unit] = 1
                else :
                    map1["unit"] = {}
                    map1["unit"][unit] = 1

            else:
                # print (f"unknown format of UOM found ignoring now:{index} {uom}");
                if "unknown" in map1.keys():
                    map1["unknown"] += 1
                else :
                    map1["unknown"] = 1
                std_uom = "";
         
        uom_dosage = std_uom
        if re.search( r'^\d+(\.\d+)?$', std_uom): 
            quantity = float(std_uom)
            if std_amount and std_amount > 0 :
                unit_price = round(std_amount / quantity,2)
        else:
            quantity = 1
            unit_price = std_amount
    return uom_dosage,quantity,unit_price,std_uom
with open('India.csv','w') as file:
    writer = csv.writer(file)
    writer.writerow(["brand","manufacturer","cims_class","material","standard_material","format_original","standard_format","concentration","dosage","uom","uom_dosage","uom_quantity","unit_price","total_amount","atc_code","atc_detail","mdc_code","sub_format","locale","mims_class"])
def read_text_file(file):  
    with open(file) as f:
        data= [json.loads(line) for line in f]    
        brand=[]    
        manufacturer=[]
        cimsClass=[]
        atcCode=[]
        atcDetail=[]
        material=[]
        dosage=[]
        uom=[]
        form=[]
        products=[]
        formater=[]
        concentration=[]
        format_original=[]
        l=[]
        std_material=[]
        mimsClass=[]
        amount=[]
        uom_dosage_list=[]
        uom_quantity_list=[]
        unit_price_list=[]
        for item in data:
            d=''
            con=''
            dosage_match=''
            con_match=''
            dosage_match_in_mat=''
            con_match_in_mat=''
            format_match=''
            format_org=''
            std_format=''
            current_mat=''
            current_std_mat=''
            drug=''
            org_form=''
            std_uom=''
            std_amount=''
            products= item['details']['products']
            activeIngredients=item['details']['activeIngredients']
            drugName=item['drugName']
            # drugName = drugName.replace(',','')
            drugName = drugName.replace('&amp;','&')
            drugName = drugName.replace('<sub>','')
            drugName = drugName.replace('</sub>','')
            drugName = drugName.replace('<em>','')
            drugName = drugName.replace('</em>','')
            drugName = drugName.replace('&quot;','"')
            atc_code_list=item['details']['atcCode']
            atc_list=item['details']['atc']
            manf=item['details']['manufacturer']
            cims_class=item['details']['cimsClass']
            mims_class=''
            drugClassification=item['drugClassification']
            print("=======================================drugName===================================",drugName)
            # if(drugName.find('/')!=-1):
            #     drug_name = (drugName.split('/'))
            # else:
            #     drug_name.append(drugName)
            mat_to_map_list,material_list = get_material(activeIngredients)
            if(len(atc_code_list)!=0):
                atc_code = atc_code_list[0]
            elif(len(atc_code_list)==0):
                atc_code = ''
            if(len(atc_list)!=0):
                atc = atc_list[0]
                atc = atc.replace(';','')
                atc = atc.replace(',','')
                atc = atc.replace('</n>','')
                atc = atc.replace('<n>','')
                atc = atc.replace('  ',' ')
                atc = atc.strip('.')
            elif(len(atc_list)==0):
                atc = ''
            if(len(products)==0):
                # for drug in drug_name:
                    if(len(material_list)!=0):
                                for e,entry in enumerate(material_list):
                                    brand.append(drugName)        
                                    manufacturer.append(manf)
                                    cimsClass.append(cims_class)
                                    mimsClass.append(mims_class)
                                    atcCode.append(atc_code)
                                    atcDetail.append(atc)
                                    uom.append('')
                                    uom_dosage_list.append('')
                                    uom_quantity_list.append(1)
                                    unit_price_list.append('')
                                    amount.append('')
                                    d = ''
                                    con = ''
                                    format_org = ''
                                    std_format = ''
                                    std_mat = entry
                                    mat = entry
                                    dos = ""
                                    c = ""
                                    dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
                                    dos = dos.replace(' ','')
                                    dos = dos.replace(',','')
                                    c = c.replace(' ','')
                                    c = c.replace(',','')
                                    dosage.append(dos)
                                    concentration.append(c)
                                    format_original.append(format_org)
                                    formater.append(std_format)
                                    material.append(current_mat)
                                    std_material.append(current_std_mat)
                    elif(len(material_list)==0):
                            if(drugClassification=='Generic'):
                                    current_mat = drugName
                                    current_std_mat = drugName
                                    drugName = ''
                            concentration.append('')
                            dosage.append('')
                            material.append(current_mat)
                            std_material.append(current_std_mat)
                            brand.append(drugName)        
                            manufacturer.append(manf)
                            cimsClass.append(cims_class)
                            mimsClass.append(mims_class)
                            atcCode.append(atc_code)
                            atcDetail.append(atc)
                            format_original.append('')
                            formater.append('')
                            uom.append('')
                            uom_dosage_list.append('')
                            uom_quantity_list.append(1)
                            unit_price_list.append('')
                            amount.append('')
                            d=''
                            con=''
                            format_org=''
                            std_format=''
            elif(len(products)!=0): 
                # for drug in drug_name:        
                    # print("current drug is:",drug)
                    for product in products:
                        packaging= product['packaging']
                        org_form= product['form']
                        # form=org_form
                        replaced=packaging.replace('&#39;s','')
                        decode_x=replaced.replace('&#215;','x')
                        l=decode_x.split(';')
                        for i in l:
                            i=i.replace(',','')
                            i=i.replace(';','')
                            form = org_form
                            pattern = re.compile(re.escape(drugName), re.IGNORECASE)
                            form = pattern.sub('', form)
                            form = form.strip()
                            format_org = form
                            std_format=search(form)
                            index=i.find('(')
                            if(index!=-1):
                                string = i[:index-1]
                                s = i.find('x')
                                x_first_occ = i[s+1:]
                                l_index = i.find('INR')
                                amt = i[index+1:l_index-1]
                                std_amount = amt.replace(',','')
                                std_amount = float(std_amount)
                                if(s!=-1):
                                    per = i.find('%')
                                    x_second_occ = x_first_occ.find('x')  
                                    if(per!=-1):
                                        con = i[:per+1]
                                        con = con.replace(' ','')
                                        std_uom = (i[s+2:index-1])
                                        d = ''
                                    elif(per==-1):
                                        con=''
                                        if(x_second_occ!=-1):
                                            index = x_first_occ.find('(')
                                            l_index = x_first_occ.find('INR')
                                            std_uom = x_first_occ[x_second_occ+2:index]
                                            d = i[:s]
                                            d = d.replace(' ','')
                                        elif(x_second_occ==-1):
                                            d = i[:s]
                                            d = d.replace(' ','')
                                            std_uom = i[s+2:index-1]
                                else:
                                    std_uom = string
                                    d = ''
                                    con = ''
                            elif(index==-1):
                                s = i.find('x')
                                if(s!=-1):
                                    per=i.find('%')
                                    std_uom = i[s+2:]
                                    if(per!=-1):
                                        con = i[:per+1]
                                        con = con.replace(' ','')
                                        d = ''
                                    elif(per==-1):
                                        d = i[:s]
                                        d = d.replace(' ','')
                                        con=''
                                else:
                                    std_uom = i
                                    d = ''
                                    con = ''
                                std_amount = ''
                            std_uom = std_uom.replace("'s","")
                            std_uom = std_uom.replace(' ','')
                            uom_dosage,quantity,unit_price,std_uom = get_uom_details(std_amount,std_uom)
                            # std_amount = str(std_amount)
                            if(len(material_list)!=0):
                                    if(len(material_list) > 1):
                                        for e,entry in enumerate(material_list):
                                            match_found = mat_to_map_list[e].find(form)
                                            print("matched_material :",match_found,"material to map form : " ,mat_to_map_list)
                                            if(match_found!=-1):
                                                brand.append(drugName)        
                                                manufacturer.append(manf)
                                                cimsClass.append(cims_class)
                                                mimsClass.append(mims_class)
                                                atcCode.append(atc_code)
                                                atcDetail.append(atc)
                                                std_uom=std_uom.replace("'s",'')
                                                std_uom=std_uom.strip()
                                                uom.append(std_uom)
                                                uom_dosage_list.append(uom_dosage)
                                                uom_quantity_list.append(quantity)
                                                unit_price_list.append(unit_price)
                                                amount.append(std_amount)
                                                mat = material_list[e]
                                                std_mat = material_list[e]
                                                dos = ""
                                                c = ""
                                                dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
                                                dos = dos.replace(' ','')
                                                dos = dos.replace(',','')
                                                c = c.replace(' ','')
                                                c = c.replace(',','')
                                                dosage.append(dos)
                                                concentration.append(c)
                                                format_original.append(format_org)
                                                formater.append(std_format)
                                                material.append(current_mat)
                                                std_material.append(current_std_mat)
                                            else:
                                                print("Match not found for form",drugName)
                                    else:
                                        entry = material_list[0]
                                        brand.append(drugName)        
                                        manufacturer.append(manf)
                                        cimsClass.append(cims_class)
                                        mimsClass.append(mims_class)
                                        atcCode.append(atc_code)
                                        atcDetail.append(atc)
                                        std_uom=std_uom.replace("'s",'')
                                        std_uom=std_uom.strip()
                                        uom.append(std_uom)
                                        uom_dosage_list.append(uom_dosage)
                                        uom_quantity_list.append(quantity)
                                        unit_price_list.append(unit_price)
                                        amount.append(std_amount)
                                        mat=entry
                                        std_mat=entry
                                        dos = ""
                                        c = ""
                                        dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[0],format_org,std_format,format_match)
                                        dos = dos.replace(' ','')
                                        dos = dos.replace(',','')
                                        c = c.replace(' ','')
                                        c = c.replace(',','')
                                        dosage.append(dos)
                                        concentration.append(c)
                                        format_original.append(format_org)
                                        formater.append(std_format)
                                        material.append(current_mat)
                                        std_material.append(current_std_mat)
                            elif(len(material_list)==0):
                                    if(drugClassification=='Generic'):
                                        current_mat = drugName
                                        current_std_mat = drugName
                                        drugName = ''
                                    material.append(current_mat)
                                    d=d.replace(',','')
                                    d=d.replace(' ','')
                                    con=con.replace(' ','')
                                    con=con.replace(',','')
                                    dosage.append(d)
                                    concentration.append(con)
                                    std_material.append(current_std_mat)
                                    brand.append(drugName)        
                                    manufacturer.append(manf)
                                    cimsClass.append(cims_class)
                                    mimsClass.append(mims_class)
                                    atcCode.append(atc_code)
                                    atcDetail.append(atc)
                                    std_uom=std_uom.replace("'s",'')
                                    std_uom=std_uom.strip()
                                    uom.append(std_uom)
                                    uom_dosage_list.append(uom_dosage)
                                    uom_quantity_list.append(quantity)
                                    unit_price_list.append(unit_price)
                                    amount.append(std_amount)
                                    format_original.append(format_org)
                                    formater.append(std_format)
    file = open('India.csv', 'a', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(zip(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,uom_dosage_list,uom_quantity_list,unit_price_list,amount,atcCode,atcDetail,[""]* len(brand),[""]* len(brand),["en_IN"]* len(brand),mimsClass))      
def search(form):
        es = Elasticsearch("http://admin:admin@localhost:9200/", ca_certs=False, verify_certs=False)
        query = {
	       "query": {
	       "multi_match" : {
	       "query":  form,
	       "type":       "most_fields",
	       "fields": ["format"],
	       "fuzziness": "AUTO"
	       }
	      }
	     }
        resp = es.search(index="format_index", body=query)
        if len(resp['hits']['hits']) != 0:
            doc = resp['hits']['hits'][0]
            standard_format = doc['_source']['format']
            return standard_format
for file in os.listdir():
    if file.startswith("mims_"):
        read_text_file(file)                            
