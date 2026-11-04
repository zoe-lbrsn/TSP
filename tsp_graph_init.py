import tkinter as tk
import csv
import random
import numpy as np
import pandas as pd


class LIEU:
    def __init__(self, x, y, name):

        self.x = x
        self.y = y
        self.name = name

    def distance(self, autre_lieu): #c'est euclidien donc renvoie qu'un nombre pas un tuple
        return ((self.x - autre_lieu.x)**2 + (self.y - autre_lieu.y)**2)**0.5



class Route: # classe route qui représente un chemin dans le problème du voyageur de commerce avec un ordre de passage par les lieux
    def __init__(self, liste_lieux): # initialisation de la classe Route avec une liste de lieux
        self.ordre = list(range(1, len(liste_lieux))) # création d'une liste d'indices représentant les lieux à visiter (sauf le point de départ et d'arrivée)

        random.shuffle(self.ordre) # mélanger aléatoirement l'ordre des lieux à visiter

        self.ordre.insert(0,0) # insérer le point de départ (indice 0) au début de la liste des lieux à visiter
        self.ordre.append(0) # insérer le point d'arrivée (indice 0) à la fin de la liste des lieux à visiter




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



class Affichage:
    def __init__(self, master, group_name="6"):
        self.master = master
        self.master.title(f"TSP - Groupe {group_name}")

        self.canvas = tk.Canvas(self.master, width=LARGEUR, height=HAUTEUR, bg='white')
        self.canvas.pack()

        self.info_label = tk.Label(
            self.master,
            text='Initialisation du graphe du TSP',
            font=('Arial', 12),
            fg='black'
        )
        self.info_label.pack()

        self.afficher_details = False

        #on écoute le clavier grace à bind
        self.master.bind('<Escape>', self.quitter) #touche "echap" pour quitter
        self.master.bind('<m>', self.pheromones) #'m' pour matrice (espèce de bouffon)
    

    def quitter(self, event=None):
        self.master.destroy() #ferme l'interface graphique complètement
        self.master.quit() #arrête la boucle principale de tkinter
    
    def pheromones(self, event=None):
        #affiche ou désaffiche les détails des phéromones sur le graphe
        self.afficher_details = not self.afficher_details
        print("bascule affichage des détails des phéromones:", self.afficher_details) #faudra relancer un canva dans le main

    def mettre_a_jour_texte(self, iteration, best_distance, iteration_trouvee):
        #mettre à jour le texte en bas de la fenêtre
        texte = f"Iteration en cours: {iteration} | Meilleure distance: {best_distance:.2f} trouvée à l'itération: {iteration_trouvee}"
        self.info_label.config(text=texte)
    
    def dessiner_lieux(self, liste_lieux):
        #dessine les lieux en forme de cercle avec leur numéro au centre
        rayon=15
        for index, lieu in enumerate(liste_lieux):
            x, y = lieu.x, lieu.y

            #cercle qui représente le lieu
            self.canvas.create_oval(
                x - rayon, y - rayon, x + rayon, y + rayon,
                fill='plum', #essayer thistle comme couleur aussi
                outline='black'
            )

            #numéro du lieu au centre du cercle
            self.canvas.create_text(
                x, y,
                text=str(index),
                font=('Arial', 10, 'bold')
            )
    
    def dessiner_meilleure_route(self, route_ordre, liste_lieux):
        #dessine la meilleure route trouvée par l'algorithme et indique l'ordre des lieux visités
        if not route_ordre or len(route_ordre) < 2:
            return
        
        for i in range(len(route_ordre) - 1):
            index_lieu1 = route_ordre[i]
            index_lieu2 = route_ordre[i + 1]

            l1 = liste_lieux[index_lieu1]
            l2 = liste_lieux[index_lieu2]

            #ligne pointillée
            self.canvas.create_line(
                l1.x, l1.y, l2.x, l2.y,
                fill='purple',
                width=2,
                dash=(4, 2)  # ligne pointillée
            )

            #ordre de visite indiquée au dessus du lieu
            #attention, pas besoi pour le dernier point qui boucle sur le départ
            if i < len(route_ordre) - 1:
                self.canvas.create_text(
                    l1.x, l1.y -25,
                    text=f"Ordre: {i}", fill="blue", font=('Arial', 9)
                )
    
    
    def dessiner_pheromones(self, matrice_pheromones, liste_lieux, seuil = 0.1):
        #dessine la matrice des phéromones sous forme de lignes grises
        #L'épaisseur ou l'apparition de la ligne dépend de l'intensité des phéromones

        nb_lieux = len(liste_lieux)

        for i in range(nb_lieux):
            for j in range(i+1, nb_lieux): #pour éviter de dessiner en double
                niveau_pheromone = matrice_pheromones[i][j]

                #N'affiche que les pistes avec suffisemment de phéromones
                if niveau_pheromone > seuil:
                    l1 = liste_lieux[i]
                    l2 = liste_lieux[j]

                    #Plus il y a de phéromones, plus la ligne est épaisse
                    epaisseur = int(min(5, max(1, niveau_pheromone * 100)))  # Limite l'épaisseur à 5
                    self.canvas.create_line(
                        l1.x, l1.y, l2.x, l2.y,
                        fill='lightgray',
                        width=epaisseur
                    )

    
    def rafraichir(self, liste_lieux, meilleure_route_ordre=None, matrice_pheromones=None):
        #Méthode qu'on appelle pour tout redessiner

        #on efface tout le canvas
        self.canvas.delete("all")

        #on dessine les phéromones en arrière-plan si la touche "m" a été pressée
        if self.afficher_details and matrice_pheromones is not None:
            self.dessiner_pheromones(matrice_pheromones, liste_lieux)
        
        #on dessine la route par dessus
        if meilleure_route_ordre is not None:
            self.dessiner_meilleure_route(meilleure_route_ordre, liste_lieux)
        
        #on dessine les lieux par dessus
        self.dessiner_lieux(liste_lieux)

        #on met à jour 
        self.master.update()
        
