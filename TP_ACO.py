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

    def initialiser_plus_proche_voisin(self):
        """
        Heuristique du plus proche voisin : depuis le lieu 0, on va toujours
        vers le lieu non visité le plus proche, puis on revient en 0.
        Cette route sert de première "meilleure route" avant les fourmis.
        """
        ordre = [0]
        visites = {0}
        ville = 0
        while len(visites) < self.nb_lieux:
            suivante = self.graph.plus_proche_voisin(ville, visites)
            ordre.append(suivante)
            visites.add(suivante)
            ville = suivante
        ordre.append(0)

        route = Route(self.graph.liste_lieux)
        route.ordre = ordre

        self.meilleure_route = route
        self.meilleure_distance = self.graph.calcul_distance_route(route)
        self.iteration_trouvee = 0

        self.affichage.mettre_a_jour_texte(0, self.meilleure_distance, 0)
        self.affichage.rafraichir(self.graph.liste_lieux, route.ordre)

        

    def __init__(self, graph, affichage, nb_fourmis=None, alpha=1.0, beta=3.0,
                 rho=0.1, Q=100.0, tau0=1.0, nb_iterations=200, pause=0.05):
    
        self.graph = graph                  # objet Graph (lieux + matrice des distances)
        self.affichage = affichage          # objet Affichage (fenêtre tkinter)
        self.nb_lieux = len(graph.liste_lieux)

        # Nombre de fourmis : par défaut autant que de villes
        # Nombre de fourmis : par défaut autant que de villes
        self.nb_fourmis = nb_fourmis if nb_fourmis is not None else self.nb_lieux
        
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
        

        # Meilleure solution globale
        self.meilleure_route = None
        self.meilleure_distance = float('inf')
        self.iteration_trouvee = 0

    # ------------------------------------------------------------------
    # Construction d'un tour par UNE fourmi
    # ------------------------------------------------------------------
    def choisir_prochaine_ville(self, ville_actuelle, non_visitees):
        """
        Règle probabiliste :
            poids(j) = tau(i,j)^alpha * eta(i,j)^beta
            #Envie d’aller en j : plus il y a de parfum et plus c’est proche, plus c’est attirant. Ici η = 1/distance

            proba(j) = poids(j) / somme des poids des villes non visitées
            #On transforme les envies en pourcentages, puis on tire au sort. La fourmi garde donc une part de hasard
            
            En français : "plus il y a de parfum vers j et plus j est proche,
            plus j'ai envie d'y aller".
        """

        poids = []
        for j in non_visitees:
            p = (self.pheromones[ville_actuelle, j] ** self.alpha) * (self.visibilite[ville_actuelle, j] ** self.beta)
            poids.append(p)

        total = sum(poids)
        if total == 0:
            # Cas de sécurité : choix uniforme
            return random.choice(non_visitees)

        probas = [p / total for p in poids]
        # Tirage au sort pondéré par les probabilités
        return random.choices(non_visitees, weights=probas, k=1)[0]


    def construire_route(self):
        """Une fourmi part du lieu 0, visite tous les lieux, puis revient en 0."""
        ordre = [0]
        non_visitees = list(range(1, self.nb_lieux))

        while len(non_visitees) > 0:
            ville_actuelle = ordre[-1]
            suivante = self.choisir_prochaine_ville(ville_actuelle, non_visitees)
            ordre.append(suivante)
            non_visitees.remove(suivante)

        ordre.append(0)  # retour au départ

        # On utilise la classe Route du projet, puis on remplace son ordre
        route = Route(self.graph.liste_lieux)
        route.ordre = ordre
        return route


    # ------------------------------------------------------------------
    # Mise à jour des phéromones
    # ------------------------------------------------------------------
    def evaporer(self):
        """tau <- (1 - rho) * tau   (le parfum s'efface un peu partout)"""
        self.pheromones = self.pheromones * (1.0 - self.rho)


    def deposer(self, route, distance):
        """
        Dépôt : delta = Q / longueur_du_tour
        Un court tour dépose beaucoup de parfum, un long tour peu.
        Le dépôt se fait dans les deux sens (matrice symétrique).
        """
        depot = self.Q / distance
        for k in range(len(route.ordre) - 1):
            a = route.ordre[k]
            b = route.ordre[k + 1]
            self.pheromones[a, b] += depot
            self.pheromones[b, a] += depot


    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def matrice_pheromones_normalisee(self):
        """
        Affichage.dessiner_pheromones utilise un seuil de 0.1 : on ramène donc
        la matrice entre 0 et 1 (la plus forte piste vaut 1) pour que seules
        les pistes importantes soient dessinées.
        """
        maximum = self.pheromones.max()
        if maximum == 0:
            return self.pheromones
        return self.pheromones / maximum

    def mettre_a_jour_affichage(self, iteration):
        self.affichage.mettre_a_jour_texte(
            iteration, self.meilleure_distance, self.iteration_trouvee
        )
        self.affichage.rafraichir(
            self.graph.liste_lieux,
            self.meilleure_route.ordre,
            self.matrice_pheromones_normalisee()
        )


    # ------------------------------------------------------------------
    # Étape 3 : boucle principale
    # ------------------------------------------------------------------
    def resoudre(self):
        # On affiche les phéromones dès le départ (la touche 'm' permet de les masquer)
        self.affichage.afficher_details = True

        try:
            for iteration in range(1, self.nb_iterations + 1):

                # 1. Construction : chaque fourmi fait un tour complet
                routes = []
                distances_routes = []
                for fourmi in range(self.nb_fourmis):
                    route = self.construire_route()
                    distance = self.graph.calcul_distance_route(route)
                    routes.append(route)
                    distances_routes.append(distance)

                # 2. Évaluation : meilleur de l'itération, puis meilleur global
                indice_meilleure = distances_routes.index(min(distances_routes))
                if distances_routes[indice_meilleure] < self.meilleure_distance:
                    self.meilleure_distance = distances_routes[indice_meilleure]
                    self.meilleure_route = routes[indice_meilleure]
                    self.iteration_trouvee = iteration

                # 3. Phéromones : évaporation puis dépôt de toutes les fourmis
                self.evaporer()
                for k in range(self.nb_fourmis):
                    self.deposer(routes[k], distances_routes[k])

                # 4. Mise à jour de la fenêtre à chaque itération
                self.mettre_a_jour_affichage(iteration)
                time.sleep(self.pause)

        except tk.TclError:
            # La fenêtre a été fermée (touche Echap) : on arrête proprement
            print("Fenêtre fermée, arrêt de l'algorithme.")

        return self.meilleure_route, self.meilleure_distance
