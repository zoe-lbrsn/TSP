import numpy as np
import random
import time 
import pandas as pd
import tkinter as tk
import csv 

class Graph :
#Définition des paramètres constants du graphe
    LARGEUR = 800
    HAUTEUR = 600
    NB_LIEUX = 0
    LISTE_LIEUX = []


#Fonction de calcul de la matrice de coût entre les lieux du graphe en utilisant la fonction distance() initialisée dans la class Lieu
    def calculate_matrice_cout_od(self):
        # Calculate or import the distance matrix between each location in the graph
        matrice_od = np.zeros((self.NB_LIEUX, self.NB_LIEUX))
        for i, lieu1 in enumerate(self.liste_lieux):
            for j, lieu2 in enumerate(self.liste_lieux):
                matrice_od[i][j] = lieu1.distance(lieu2)
        return matrice_od

def calcul_distance_route(self, route) -> float:
        #Calcule la distance totale d'une route (circuit traversant tous les lieux).

        distance_totale = 0.0
        ordre = route.ordre

        # Parcours du tableau 'ordre' paire par paire : (v0 -> v1), (v1 -> v2), ..., (vn-1 -> v0)
        for i in range(len(ordre) - 1):
            u = ordre[i]
            v = ordre[i + 1]
            distance_totale += self.matrice_od[u][v]

        return distance_totale


#Fonction de calul du plus proche voisin du point courant en se basant sur la matrice de coût calculée juste avant
def plus_proche_voisin(self, graph, matrice_od, x, y) :
    # Load the graph coordinates from the CSV file
    graph.charger_graph('path/to/csv/file.csv')
    
    # Find the closest neighbor to the current location (x, y) based on the cost matrix
    closest_index = None
    closest_distance = float('inf')
    for i in range(self.NB_LIEUX):
        if i != x:  # Avoid comparing the location with itself
            distance = matrice_od[x][i]
            if distance < closest_distance:
                closest_distance = distance
                closest_index = i
    return closest_index

