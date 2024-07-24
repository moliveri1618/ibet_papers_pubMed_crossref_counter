import requests
import json
import xml.etree.ElementTree as ET
import re




def get_iBET_papers_IDs_from_pubMed(year):

    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=ibet[affiliation]+AND+{year}[pdat]&retmax=1000"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.text
        root = ET.fromstring(data)
        id_list = root.find('IdList')
        ids = id_list.findall('Id')
        id_array = []
        
        for id_element in ids:
            id_array.append(id_element.text)

        print('PUBMED IDs: ' + str(len(id_array)))
        return id_array

    else:
        print("API request failed with status code:", response.status_code)






def get_DOIs_from_pubMed_IDs(current_year):

    #get pudmed IDs
    pubmed_IDs = get_iBET_papers_IDs_from_pubMed(current_year)

    #get pubmed dois using pubmed IDs
    print('Finding PUBMED DOIs ', end='', flush=True)
    DOI_array = []
    for id in pubmed_IDs:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.text
            root = ET.fromstring(data)
            elocation_id = root.find(".//Item[@Name='ELocationID']").text
            if elocation_id is not None: # if none just skip
                doi_value = elocation_id.split(' ')[1]  # Split by space and get the second part
                DOI_array.append(doi_value)
                print('.', end='', flush=True)
            else:
                 print("ELocationID is None for this item")
        else:
            print("API request failed with status code:", response.status_code)

    print('')
    print('PUBMED DOIs:', len(DOI_array))
    return DOI_array, len(DOI_array)


def get_DOIs_from_crossref(year):
    until_year = year + 1

    url = f"https://api.crossref.org/works?query.affiliation=iBET&filter=from-pub-date:{year},until-pub-date:{until_year}&rows=1000" #"https://api.crossref.org/works?query.affiliation=iBET&filter=from-pub-date:2022"  #https://api.crossref.org/works?query.author=iBET #https://api.crossref.org/works?query=iBET
    response = requests.get(url)
    DOIs = []

    if response.status_code == 200:
        json_data = response.json()
        for i in range(len(json_data['message']['items'])):
            DOIs.append(json_data['message']['items'][i]['DOI'])
            #print(json_data['message']['items'][i]['DOI'])

        print('CROSSREF DOIs: ' + str(len(DOIs)))
        return DOIs, len(DOIs)
    else:
        print("API request failed with status code:", response.status_code)
        return None, 0
    


def concat_remove_duplicates_arrays(pubmed_DOIs, crossref_DOIs):
    
    # Convert arrays to sets
    pubmed_DOIs_set = set(pubmed_DOIs)
    crossref_DOIs_set = set(crossref_DOIs)

    # Get unique DOIs by performing set union
    unique_DOIs = pubmed_DOIs_set.union(crossref_DOIs_set)

    # Convert the set back to a list if needed
    unique_DOIs_list = list(unique_DOIs)

    print('Total DOIs without duplicates: ', len(unique_DOIs_list))

    return unique_DOIs_list



def get_papers_info_from_DOIs(DOIs):

    print('Finding data for each DOIs ', end='', flush=True)

    res = []
    for DOI in DOIs:
        base_url = f"https://doi.org/{DOI}"
        headers = {
            "Accept": "text/bibliography; style=bibtex"
        }
        response = requests.get(base_url, headers=headers)

        if response.status_code == 200:
            response_text = response.content.decode('utf-8') 
        else:
            print(str(DOI) + ' not found')

        print('.', end='', flush=True)
        res.append(API_data_to_json([response_text.strip()]))

    print('\n')
    return res



def API_data_to_json(papers_data):

    parsed_papers = []

    # Regular expression patterns to extract different fields
    field_patterns = {
        "title": r"title=\{([^}]+)\}",
        "volume": r"volume=\{([^}]+)\}",
        "ISSN": r"ISSN=\{([^}]+)\}",
        "url": r"url=\{([^}]+)\}",
        "number": r"number=\{([^}]+)\}",
        "journal": r"journal=\{([^}]+)\}",
        "publisher": r"publisher=\{([^}]+)\}",
        "author": r"author=\{([^}]+)\}",
        "year": r"year=\{([^}]+)\}",
        "month": r"month=\{([^}]+)\}",
        "pages": r"pages=\{([^}]+)\}"
    }

    for paper in papers_data:
        paper_text = paper.replace("Ãª", "ê")
        paper_data = {}

        for field, pattern in field_patterns.items():
            match = re.search(pattern, paper_text)
            if match:
                paper_data[field] = match.group(1)

        parsed_papers.append(paper_data)

    json_data = json.dumps(parsed_papers, indent=4)
    parsed_json_data = json.loads(json_data)

    return parsed_json_data



def find_ibet_papers_for_specific_year(year):

    print(f"----------- FINDING PAPERS OF IBET FOR THE YEAR {year}-----------")

    # get DOI using PUBMED API
    pubmed_DOIs, n_pubmed = get_DOIs_from_pubMed_IDs(year)

    #get DOI using crossref API
    crossref_DOIs, n_crossref = get_DOIs_from_crossref(year)

    #concat & remove duplicates between pubmed and crossref DOIs array
    DOIs_list = concat_remove_duplicates_arrays(pubmed_DOIs, crossref_DOIs)

    #get papers data from DOI
    papers_data = get_papers_info_from_DOIs(DOIs_list)

    return papers_data, n_pubmed, n_crossref


def export_data_to_pdf(papers):
    try:
        formatted_data = json.dumps(papers, indent=4)
        with open('output.txt', 'w') as file:
            file.write(formatted_data)

        print("Data exported to output.txt")
        return 1 

    except Exception as e:
        print(f"Failed to export data: {e}")
        return 0 