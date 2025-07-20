#!/usr/bin/env python

import requests
import time
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
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
PLOT_FILE = "signatures_plot.png"

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
    # On vérifie que le count existe et est un entier
    if count is None or not isinstance(count, int):
        print("Erreur : le nombre de signatures n'est pas valide.")
        return
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "signatures"])
        writer.writerow([timestamp, count])


def plot_data_2():
    # Dans ce deuxième cas, on utilise pandas pour lire le fichier CSV. On créé deux plots (un haut un bas, partageant les X) : un pour le nombre de signatures, et un pour l'évolution du nombre de signatures.
    df = pd.read_csv(CSV_FILE, sep=",")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['signatures'] = df['signatures'].astype(int)
    # On récupère la dernière date et le dernier compte pour le header du graphique
    last_date = df['timestamp'].max() # format : 2025-07-18T15:10:03.294914
    last_count = df['signatures'].max()
    # On extrait le jour, le mois et l'année, ainsi que l'heure et minutes (sans secondes et décimales)
    last_date_str = last_date.strftime("%d/%m/%Y")  # Format jour/mois/année
    last_time_str = last_date.strftime("%H:%M")  # Format heure:minute
    last_count_str = f"{last_count:,}"  # Format avec des virgules pour les milliers
    title = f"Nombre de signatures\n(dernière mise à jour : {last_date_str} à {last_time_str} : {last_count_str} signatures)"


    # On ajoute une colonne pour l'évolution du nombre de signatures, une colonne pour le temps écoulé et une colonne pour le nombre de signaturs par minute
    df['evolution'] = df['signatures'].diff().fillna(0)
    df['time_elapsed'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
    # On calcule time_elapsed_since_last_point
    df['time_elapsed_since_last_point'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    # On calcule le nombre de signatures par minute
    df['signatures_per_seconde_since_last_point'] = df['evolution'] / (df['time_elapsed_since_last_point']).replace(0, pd.NA)  # Remplacez 0 par NaN pour éviter la division par zéro
    # On trace les deux graphiques
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10, 8), sharex=True)
    # Premier graphique : nombre de signatures
    ax1.plot(df['timestamp'], df['signatures'], marker='o', color='blue')
    ax1.set_title(title)
    ax1.set_ylabel("Signatures")
    ax1.grid(True)
    # Y from 0 à max + 10%
    ax1.set_ylim(0, df['signatures'].max() * 1.1)
    # # Add vertical text below each point, grey background
    # show_labels = False  # Si True, on affiche les labels, sinon non
    # if show_labels:
    #     for i, row in df.iterrows():
    #         y = row['signatures'] - 0.05 * df['signatures'].max()  # Positionner le texte un peu en dessous du point
    #         # On aligne sur le point
    #         ax1.text(row['timestamp'], y, f"{row['signatures']}", ha='center', va='top', rotation=-90, fontsize=8, bbox=dict(facecolor='lightgrey', alpha=1))
    # show_last_label = True  # Si True, on affiche le dernier label, sinon non
    # if show_last_label:
    #     last_row = df.iloc[-1]
    #     y = last_row['signatures'] - 0.05 * df['signatures'].max()
    #     ax1.text(last_row['timestamp'], y, f"{last_row['signatures']}", ha='center', va='top', rotation=-90, fontsize=8, bbox=dict(facecolor='lightgrey', alpha=1))
    
    # Y labels: nombres entiers (pas de notation scientifique)
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
    ax1.ticklabel_format(axis='y', style='plain')


    
    # Deuxième graphique : évolution du nombre de signatures (signatures par minute depuis le dernier point)
    # Ajout de la colonne timestamp_start pour le graphique, afin de tracer le début du rectangle
    df['timestamp_start'] = df['timestamp'] - pd.to_timedelta(df['time_elapsed_since_last_point'], unit='s')
    df['bar_width'] = df['time_elapsed_since_last_point']
    # Filter out NaN values for signatures_per_seconde_since_last_point
    df = df.dropna(subset=['signatures_per_seconde_since_last_point']).reset_index(drop=True)
    ax2.bar(df['timestamp_start'], df['signatures_per_seconde_since_last_point'], width=df['timestamp'] - df['timestamp_start'], color='orange', alpha=0.7, align='edge')

    ax2.set_title("Nouvelles signatures par seconde")
    ax2.set_xlabel("Date et heure")
    ax2.set_ylabel("Signatures par seconde")
    ax2.grid(True)
    # Y from 0 to max + 10%
    ax2.set_ylim(0, df['signatures_per_seconde_since_last_point'].max() * 1.1)

    plt.tight_layout()
    plt.savefig(PLOT_FILE)
    plt.close()






now = datetime.now().isoformat()
count = get_signature_count(URL)
save_data(now, count)
print(f"{now} - Signatures: {count}")

if count is not None:
    plot_data_2()
    print(f"Data saved to {CSV_FILE} and plot saved to {PLOT_FILE}")
