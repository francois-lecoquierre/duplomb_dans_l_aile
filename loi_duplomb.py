#!/usr/bin/env python

import requests
import time
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
from datetime import timedelta
import pandas as pd

now_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# active_dir="/Users/francois_leco/Documents/test/petition"
# os.chdir(active_dir)
URL = "https://petitions.assemblee-nationale.fr/initiatives/i-3014"
CSV_FILE = "signatures.tsv"

# archive_folder = "archive"
# if not os.path.exists(archive_folder):
#     os.makedirs(archive_folder)
# csv_archive_file = os.path.join(archive_folder, f"signatures_{now_string.replace(':', '-')}.tsv")
# plot_archive_file = os.path.join(archive_folder, f"signatures_plot_{now_string.replace(':', '-')}.png")


def get_html_content(url):
    print(f"Récupération du contenu de la page : {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération de la page : {e}")
        return None
    

def get_signature_count(url):
    print(f"Récupération du nombre de signatures depuis : {url}")
    html_content = get_html_content(url)
    # print(html_content)
    # Spot of interesr: <span class="progress__bar__number">194 921</span><span class="progress__bar__total">
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        count_span = soup.find("span", class_="progress__bar__number")
        if count_span:
            count_text = count_span.get_text(strip=True)
            # Remove spaces and convert to integer
            return int(count_text.replace(" ", ""))
        else:
            print("Erreur : impossible de trouver le nombre de signatures dans la page.")
            return None
    else:
        print("Erreur : le contenu de la page est vide ou invalide.")
        return None


def save_data(timestamp, count):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "signatures"])
        writer.writerow([timestamp, count])
    # # Archive the CSV file
    # with open(CSV_FILE, "r") as f:
    #     data = f.read()
    # with open(csv_archive_file, "w") as f:
    #     f.write(data)


now = datetime.now().isoformat()
count = get_signature_count(URL)
save_data(now, count)
print(f"{now} - Signatures: {count}")
