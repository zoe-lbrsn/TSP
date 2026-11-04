import csv
import random
import numpy as np
import pandas as pd

# Constantes globales requises par la consigne
LARGEUR = 800
HAUTEUR = 600
NB_LIEUX = 10


class Graph:
    # Variables de classe si nécessaire
    matrice_od = None

    def __init__(self, liste_lieux=None):
        self.liste_lieux = liste_lieux if liste_lieux is not None else []
        self.matrice_od = None

        # Si aucune liste n'est fournie au départ, on en génère une aléatoirement
        if not self.liste_lieux:
            self.generer_lieux_aleatoires(NB_LIEUX)

        # Calcul automatique de la matrice OD si des lieux sont présents
        if self.liste_lieux:
            self.calcul_matrice_cout_od()

    def generer_lieux_aleatoires(self, nb_lieux):
        """Génère aléatoirement des lieux dans le cadre (LARGEUR x HAUTEUR)."""
        from tsp_graph_init import Lieu
        marge = 40
        self.liste_lieux = [
            Lieu(
                random.uniform(marge, LARGEUR - marge),
                random.uniform(marge, HAUTEUR - marge),
                nom=f"Lieu_{i}"
            )
            for i in range(nb_lieux)
        ]

    def calcul_matrice_cout_od(self):
        """Calcule la matrice de distances (OD) entre chaque lieu du graphe
        et stocke le résultat dans la variable self.matrice_od.
        """
        nb = len(self.liste_lieux)
        self.matrice_od = np.zeros((nb, nb))
        for i, lieu1 in enumerate(self.liste_lieux):
            for j, lieu2 in enumerate(self.liste_lieux):
                if i != j:
                    # Utilise la méthode distance_vers de la classe Lieu
                    self.matrice_od[i, j] = lieu1.distance_vers(lieu2)
        return self.matrice_od

    def plus_proche_voisin(self, idx_lieu, visites=None):
        """
        Renvoie l'index du plus proche voisin pour un lieu donné (idx_lieu).
        Permet d'exclure les lieux déjà visités via l'ensemble 'visites'.
        """
        if self.matrice_od is None:
            self.calcul_matrice_cout_od()

        closest_index = None
        closest_distance = float('inf')
        nb_lieux = len(self.liste_lieux)

        for i in range(nb_lieux):
            if i != idx_lieu:
                if visites is not None and i in visites:
                    continue
                distance = self.matrice_od[idx_lieu, i]
                if distance < closest_distance:
                    closest_distance = distance
                    closest_index = i

        return closest_index

    def charger_graph(self, fichier_csv):
        """
        Lit un fichier CSV contenant les coordonnées des lieux et met à jour
        la liste des lieux ainsi que la matrice de coût OD.
        """
        from tsp_graph_init import Lieu
        self.liste_lieux = []
        try:
            df = pd.read_csv(fichier_csv)
            for i, row in df.iterrows():
                nom = str(row['nom']) if 'nom' in df.columns else f"Lieu_{i}"
                x = float(row['x'])
                y = float(row['y'])
                self.liste_lieux.append(Lieu(x, y, nom))
            # Mise à jour de la matrice OD après le chargement
            self.calcul_matrice_cout_od()
        except Exception as e:
            print(f"Erreur lors du chargement du fichier CSV {fichier_csv} : {e}")

    def calcul_distance_route(self, route) -> float:
        """
        Calcule la distance totale d'une route (circuit fermé)
        en utilisant la matrice de distances self.matrice_od.
        """
        if self.matrice_od is None:
            self.calcul_matrice_cout_od()

        distance_totale = 0.0
        ordre = route.ordre

        for i in range(len(ordre) - 1):
            u = ordre[i]
            v = ordre[i + 1]
            distance_totale += self.matrice_od[u, v]

        return distance_totale