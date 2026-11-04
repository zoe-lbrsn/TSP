import time
import random
import tkinter as tk
import numpy as np

from tsp_graph_init import Graph, Affichage, Route

class TP_ACO:

    '''
    chaque fourmi construit un tour complet en choississanrt le prochaine ville au hasard 
    mais en favorisant les villes proches ET les chemins phéromonés par d'anciennes fourmis.
    Les tours sontévalués et les bons tour vont être phéromonés (bcp) et les moins biens peu.
    Les phéromones s'évaporent avec le temps, donc les tours les moins bons vont disparaitre.
    On essaie aussi d'éviter avec ca les minima locaux, car les tours moins bons vont disparaitre 
    et donc les fourmis vont explorer d'autres chemins.

    '''

    def __init__(self, graph, affichage, nb_fourmis=None, alpha=1.0, beta=3.0,
                 rho=0.1, Q=100.0, tau0=1.0, nb_iterations=200, pause=0.05):
    
        self.graph = graph                  # objet Graph (lieux + matrice des distances)
        self.affichage = affichage          # objet Affichage (fenêtre tkinter)
        self.nb_lieux = len(graph.liste_lieux)

        # Nombre de fourmis : par défaut autant que de villes
        
        #paramètres variables pour les maths 
        self.alpha = alpha                  # poids de la phéromone
        self.beta = beta                    # poids de la distance (heuristique) --> nous on pense prendre nearest neighbor
        self.rho = rho                      # taux d'évaporation (entre 0 et 1)
        self.Q = Q                          # quantité de parfum déposée par une fourmi
        self.tau0 = tau0                    # phéromone initiale
        self.nb_iterations = nb_iterations
        self.pause = pause                  # pause pour voir l'animation

        # Structures de données
        # Matrice des distances : déjà calculée par Graph par Zoé, je récup
        if self.graph.matrice_od is None:
            self.graph.calcul_matrice_cout_od()
        self.distances = self.graph.matrice_od

        #Matrice des phéromones : même petite valeur partout pour l'instant
        #(0 sur la diagonale)
        self.pheromones = np.full((self.nb_lieux, self.nb_lieux), self.tau0) #taux0 c'est le taux de base de phéromones qu'on met partout
        np.fill_diagonal(self.pheromones, 0.0)

        # Visibilité c'est la fourmi qui voit le prochain lieu
        # Visibilité = 1 / distance (plus c'est proche, plus c'est attirant)
        # On met 0 sur la diagonale pour éviter la division par zéro
        self.visibilite = np.zeros((self.nb_lieux, self.nb_lieux))
        for i in range(self.nb_lieux):
            for j in range(self.nb_lieux):
                if i != j and self.distances[i, j] > 0:
                    self.visibilite[i, j] = 1.0 / self.distances[i, j]
