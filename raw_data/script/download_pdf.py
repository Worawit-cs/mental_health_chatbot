'''
This module is use for download pdf if you have source(URL) in .txt file use with input redirection directed by Wit
'''
import os
import requests
from ...path import get_path
BASE_DIR,PATH = get_path()
PDF_SOURCE = os.path.join(BASE_DIR, PATH["PDF_SOURCE"])
PATH_RAW_SOURCE_DATA = f"{PDF_SOURCE}/university_students_mental_health_OA_links.txt"
all_links = []
with open(PATH_RAW_SOURCE_DATA, "r") as file:
    for link in file:
        link = link.strip()
        if "https" in link and "pdf" in link:
            all_links.append(link)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36"
}
out_dir = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/raw_data/pdf_data"
for link in all_links:
    response = requests.get(link,headers=headers)
    if response.status_code == 200:
        file_path = os.path.join(out_dir,os.path.basename(link))
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: Success")
    else:
        print("Downloaded: Failed")