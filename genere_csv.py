import csv
import random

def generer_csv_points(nom_fichier, nombre_de_points):
    with open(nom_fichier, mode='w', newline='') as fichier:
        writer = csv.writer(fichier)
        writer.writerow(['x', 'y'])
        
        for _ in range(nombre_de_points):
            # x limité à 800 (largeur) et y limité à 600 (hauteur)
            x = random.uniform(0, 800)
            y = random.uniform(0, 600)
            writer.writerow([x, y])
            
    print(f"Le fichier '{nom_fichier}' a été créé avec {nombre_de_points} points (fenêtre 800x600).")

# Exemple pour 50 points :
generer_csv_points('graph_30.csv', 30)