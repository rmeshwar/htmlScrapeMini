import requests
from bs4 import BeautifulSoup
import pandas as pd

def unm_faculty_list_json(url, department_filter, sheet_name):
    """
    Fetches and processes faculty list from a JSON source.
    """
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        faculty_list = [
            {"First Name": member["firstName"].strip(), "Last Name": member["lastName"].strip(), "Email": "", "Error": ""}
            for member in data["faculty"]
            if department_filter in member.get("departments", [])
        ]
    else:
        faculty_list = []
    return pd.DataFrame(faculty_list), sheet_name


def upstate_faculty_list_html(url, sheet_name):
    """
    Fetches and processes faculty list from an HTML source, filtering only items with an empID.
    """
    response = requests.get(url)
    faculty_list = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        for li in soup.find_all('li'):
            a_tag = li.find('a')

            # Check if <a> tag exists and contains 'href' with 'empID'
            if a_tag and 'href' in a_tag.attrs and 'empID=' in a_tag['href']:
                emp_id = a_tag['href'].split('empID=')[1]
                email = f"{emp_id}@upstate.edu"

                # Extract full name and split into first and last names
                full_name = a_tag.get_text(strip=True).split(', ')[0]  # Remove any titles or credentials
                name_parts = full_name.split()
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''  # Handle multiple last names

                faculty_list.append({
                    "First Name": first_name.strip(),
                    "Last Name": last_name.strip(),
                    "Email": email,
                    "Error": ""
                })
    else:
        print(f"Failed to fetch data from URL: {url}")

    return pd.DataFrame(faculty_list), sheet_name

def westchester_faculty_list_html(url, sheet_name):
    """
    Fetches and processes faculty list from an HTML source at Westchester Medical Center,
    including only items with specific qualifications and adjusting name handling.
    """
    response = requests.get(url)
    faculty_list = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Define qualifications to look for in the text
        qualifications = ["MD", "FASA", "DO", "MBA", "PhD"]

        for p in soup.find_all('p'):
            # Check for the presence of any qualification in the paragraph's text
            if any(qual in p.get_text() for qual in qualifications):
                strong_tag = p.find('strong')
                if strong_tag:
                    full_name_text = strong_tag.get_text(strip=True).split(',')[0]  # Exclude any titles or credentials
                    name_parts = full_name_text.split()

                    # Assign the first two words as the first name (if present) and the rest as the last name
                    if len(name_parts) > 2:
                        first_name = ' '.join(name_parts[:2])
                        last_name = ' '.join(name_parts[2:])
                    else:
                        first_name = name_parts[0] if name_parts else ''
                        last_name = name_parts[1] if len(name_parts) > 1 else ''

                    faculty_list.append({
                        "First Name": first_name.strip(),
                        "Last Name": last_name.strip(),
                        "Email": "",
                        "Error": ""
                    })
    else:
        print(f"Failed to fetch data from URL: {url}")

    return pd.DataFrame(faculty_list), sheet_name




# URLs and handlers for each site
sites_info = [
    {"handler": unm_faculty_list_json, "url": "https://hsc.unm.edu/directory/index.json", "department_filter": "SOM - Anesthesiology", "sheet_name": "UNM Anesthesiology"},
    {"handler": upstate_faculty_list_html, "url": "https://www.upstate.edu/anesthesiology/about-us/faculty.php", "sheet_name": "Upstate Anesthesiology"},
    {"handler": westchester_faculty_list_html, "url": "https://www.westchestermedicalcenter.org/anesthesiology-residency-program", "sheet_name": "Westchester Anesthesiology"}
]

# Initialize an Excel writer
with pd.ExcelWriter('faculty_lists.xlsx', engine='openpyxl') as writer:
    for site in sites_info:
        if 'department_filter' in site:
            df, sheet_name = site['handler'](site["url"], site["department_filter"], site["sheet_name"])
        else:
            df, sheet_name = site['handler'](site["url"], site["sheet_name"])
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Faculty lists have been saved to 'faculty_lists.xlsx'.")
