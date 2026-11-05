"""Le notre avant que Claude ne s'en mêle"""
import time
import random
import csv
import tkinter as tk
import numpy as np
import pandas as pd

# ==============================================================================
# 1. CONSTANTES GLOBALES
# ==============================================================================
LARGEUR = 800
HAUTEUR = 600
NB_LIEUX = 10


# ==============================================================================
# 2. CLASSES DE BASE (GRAPHE ET INTERFACE)
# ==============================================================================
class LIEU:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def distance(self, autre_lieu):
        """Distance euclidienne entre deux lieux."""
        return ((self.x - autre_lieu.x) ** 2 + (self.y - autre_lieu.y) ** 2) ** 0.5


class Route:
    """Représente un chemin/circuit fermé dans le problème du voyageur de commerce."""
    def __init__(self, liste_lieux):
        self.ordre = list(range(1, len(liste_lieux)))
        random.shuffle(self.ordre)
        self.ordre.insert(0, 0)
        self.ordre.append(0)


class Graph:
    matrice_od = None

    def __init__(self, liste_lieux=None):
        self.liste_lieux = liste_lieux if liste_lieux is not None else []
        self.matrice_od = None

        if not self.liste_lieux:
            self.generer_lieux_aleatoires(NB_LIEUX)

        if self.liste_lieux:
            self.calcul_matrice_cout_od()

    def generer_lieux_aleatoires(self, nb_lieux):
        """Génère aléatoirement des lieux dans le cadre (LARGEUR x HAUTEUR)."""
        marge = 40
        self.liste_lieux = [
            LIEU(
                random.uniform(marge, LARGEUR - marge),
                random.uniform(marge, HAUTEUR - marge),
                name=f"LIEU_{i}"
            )
            for i in range(nb_lieux)
        ]

    def calcul_matrice_cout_od(self):
        """Calcule la matrice de distances (OD) entre chaque lieu du graphe."""
        nb = len(self.liste_lieux)
        self.matrice_od = np.zeros((nb, nb))
        for i, lieu1 in enumerate(self.liste_lieux):
            for j, lieu2 in enumerate(self.liste_lieux):
                if i != j:
                    self.matrice_od[i, j] = lieu1.distance(lieu2)
        return self.matrice_od

    def plus_proche_voisin(self, idx_lieu, visites=None):
        """Renvoie l'index du plus proche voisin non visité."""
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
        """Lit un fichier CSV et charge la liste des lieux."""
        self.liste_lieux = []
        try:
            df = pd.read_csv(fichier_csv)
            for i, row in df.iterrows():
                nom = str(row['nom']) if 'nom' in df.columns else f"LIEU_{i}"
                x = float(row['x'])
                y = float(row['y'])
                self.liste_lieux.append(LIEU(x, y, nom))
            self.calcul_matrice_cout_od()
        except Exception as e:
            print(f"Erreur lors du chargement du fichier CSV {fichier_csv} : {e}")

    def calcul_distance_route(self, route) -> float:
        """Calcule la distance totale d'une route (circuit fermé)."""
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

        self.fourmis_lancees = False
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

        self.master.bind('<Escape>', self.quitter)
        self.master.bind('<m>', self.pheromones)
        self.master.bind('<M>', self.pheromones)

    def quitter(self, event=None):
        self.master.destroy()
        self.master.quit()

    def pheromones(self, event=None):
        if not self.fourmis_lancees:
            self.fourmis_lancees = True
            self.afficher_details = True
        else:
            self.afficher_details = not self.afficher_details

    def mettre_a_jour_texte(self, iteration, best_distance, iteration_trouvee):
        texte = f"Iteration en cours: {iteration} | Meilleure distance: {best_distance:.2f} trouvée à l'itération: {iteration_trouvee}"
        self.info_label.config(text=texte)

    def dessiner_lieux(self, liste_lieux):
        rayon = 15
        for index, lieu in enumerate(liste_lieux):
            x, y = lieu.x, lieu.y
            self.canvas.create_oval(
                x - rayon, y - rayon, x + rayon, y + rayon,
                fill='plum',
                outline='black'
            )
            self.canvas.create_text(
                x, y,
                text=str(index),
                font=('Arial', 10, 'bold')
            )

    def dessiner_meilleure_route(self, route_ordre, liste_lieux):
        if not route_ordre or len(route_ordre) < 2:
            return

        for i in range(len(route_ordre) - 1):
            index_lieu1 = route_ordre[i]
            index_lieu2 = route_ordre[i + 1]

            l1 = liste_lieux[index_lieu1]
            l2 = liste_lieux[index_lieu2]

            self.canvas.create_line(
                l1.x, l1.y, l2.x, l2.y,
                fill='purple',
                width=2
            )

            if i < len(route_ordre) - 1:
                self.canvas.create_text(
                    l1.x, l1.y - 25,
                    text=f"Ordre: {i}", fill="black", font=('Arial', 8)
                )

    def dessiner_pheromones(self, matrice_pheromones, liste_lieux, seuil=0.2):
        nb_lieux = len(liste_lieux)

        for i in range(nb_lieux):
            for j in range(i + 1, nb_lieux):
                niveau_pheromone = matrice_pheromones[i][j]

                if niveau_pheromone > seuil:
                    l1 = liste_lieux[i]
                    l2 = liste_lieux[j]
                    epaisseur = max(1, int(niveau_pheromone * 8))
                    self.canvas.create_line(
                        l1.x, l1.y, l2.x, l2.y,
                        fill='lightgray',
                        width=epaisseur
                    )

    def rafraichir(self, liste_lieux, meilleure_route_ordre=None, matrice_pheromones=None):
        self.canvas.delete("all")

        if self.afficher_details and matrice_pheromones is not None:
            self.dessiner_pheromones(matrice_pheromones, liste_lieux)

        if meilleure_route_ordre is not None:
            self.dessiner_meilleure_route(meilleure_route_ordre, liste_lieux)

        self.dessiner_lieux(liste_lieux)
        self.master.update()


# ==============================================================================
# 3. ALGORITHME ACO (COLONIE DE FOURMIS)
# ==============================================================================
class TP_ACO:
    """
    Algorithme d'optimisation par colonie de fourmis (ACO) pour le TSP.
    """
    def __init__(self, graph, affichage, nb_fourmis=None, alpha=1.0, beta=2.5,
                 rho=0.06, Q=100.0, tau0=1.0, nb_iterations=300, pause=0.05):

        self.graph = graph
        self.affichage = affichage
        self.nb_lieux = len(graph.liste_lieux)
        self.nb_fourmis = nb_fourmis if nb_fourmis is not None else self.nb_lieux

        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.tau0 = tau0
        self.nb_iterations = nb_iterations
        self.pause = pause

        if self.graph.matrice_od is None:
            self.graph.calcul_matrice_cout_od()
        self.distances = self.graph.matrice_od

        self.pheromones = np.full((self.nb_lieux, self.nb_lieux), self.tau0)
        np.fill_diagonal(self.pheromones, 0.0)

        self.visibilite = np.zeros((self.nb_lieux, self.nb_lieux))
        for i in range(self.nb_lieux):
            for j in range(self.nb_lieux):
                if i != j and self.distances[i, j] > 0:
                    self.visibilite[i, j] = 1.0 / self.distances[i, j]

        self.meilleure_route = None
        self.meilleure_distance = float('inf')
        self.iteration_trouvee = 0

    def initialiser_plus_proche_voisin(self):
        """Initialise la première solution via l'heuristique du plus proche voisin."""
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

    def choisir_prochaine_ville(self, ville_actuelle, non_visitees):
        poids = []
        for j in non_visitees:
            p = (self.pheromones[ville_actuelle, j] ** self.alpha) * (self.visibilite[ville_actuelle, j] ** self.beta)
            poids.append(p)

        total = sum(poids)
        if total == 0:
            return random.choice(non_visitees)

        probas = [p / total for p in poids]
        return random.choices(non_visitees, weights=probas, k=1)[0]

    def construire_route(self):
        ordre = [0]
        non_visitees = list(range(1, self.nb_lieux))

        while len(non_visitees) > 0:
            ville_actuelle = ordre[-1]
            suivante = self.choisir_prochaine_ville(ville_actuelle, non_visitees)
            ordre.append(suivante)
            non_visitees.remove(suivante)

        ordre.append(0)

        route = Route(self.graph.liste_lieux)
        route.ordre = ordre
        return route

    def evaporer(self):
        self.pheromones = self.pheromones * (1.0 - self.rho)

    def deposer(self, route, distance):
        depot = self.Q / distance
        for k in range(len(route.ordre) - 1):
            a = route.ordre[k]
            b = route.ordre[k + 1]
            self.pheromones[a, b] += depot
            self.pheromones[b, a] += depot

    def matrice_pheromones_normalisee(self):
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

    def resoudre(self):
        self.affichage.afficher_details = True

        try:
            for iteration in range(1, self.nb_iterations + 1):
                routes = []
                distances_routes = []
                for fourmi in range(self.nb_fourmis):
                    route = self.construire_route()
                    distance = self.graph.calcul_distance_route(route)
                    routes.append(route)
                    distances_routes.append(distance)

                indice_meilleure = distances_routes.index(min(distances_routes))
                if distances_routes[indice_meilleure] < self.meilleure_distance:
                    self.meilleure_distance = distances_routes[indice_meilleure]
                    self.meilleure_route = routes[indice_meilleure]
                    self.iteration_trouvee = iteration

                self.evaporer()
                for k in range(self.nb_fourmis):
                    self.deposer(routes[k], distances_routes[k])

                self.mettre_a_jour_affichage(iteration)
                time.sleep(self.pause)

                if iteration - self.iteration_trouvee >= 500:
                    break

            self.affichage.afficher_details = False
            self.affichage.mettre_a_jour_texte(
                self.nb_iterations, self.meilleure_distance, self.iteration_trouvee
            )
            self.affichage.rafraichir(
                self.graph.liste_lieux,
                self.meilleure_route.ordre
            )

        except tk.TclError:
            print("Fenêtre fermée, arrêt de l'algorithme.")

        return self.meilleure_route, self.meilleure_distance


# ==============================================================================
# 4. FONCTION PRINCIPALE (MAIN)
# ==============================================================================
def construire_route_plus_proche_voisin(graphe: Graph) -> Route:
    nb_lieux = len(graphe.liste_lieux)
    visites = {0}
    ordre_nn = [0]
    courant = 0

    while len(visites) < nb_lieux:
        suivant = graphe.plus_proche_voisin(courant, visites)
        ordre_nn.append(suivant)
        visites.add(suivant)
        courant = suivant

    ordre_nn.append(0)

    route = Route(graphe.liste_lieux)
    route.ordre = ordre_nn
    return route


def main():
    root = tk.Tk()

    # 1. Initialisation du Graphe
    graphe = Graph()
    
    # Remarque : si tu as un fichier CSV (ex: graph_20.csv), tu peux le charger ici :
    graphe.charger_graph("graph_1000.csv")

    # 2. Initialisation de l'affichage Tkinter
    affichage = Affichage(root, group_name="6")

    # 3. Calcul & Affichage de l'initialisation Plus Proche Voisin
    route_nn = construire_route_plus_proche_voisin(graphe)
    dist_nn = graphe.calcul_distance_route(route_nn)

    affichage.rafraichir(
        liste_lieux=graphe.liste_lieux,
        meilleure_route_ordre=route_nn.ordre
    )
    affichage.info_label.config(
        text=f"[Plus Proche Voisin] Distance : {dist_nn:.2f} px | Appuie sur [ESPACE] pour lancer ACO"
    )

    # 4. Lancement de l'ACO via la touche ESPACE
    def démarrer_aco(event=None):
        root.unbind('<space>')
        affichage.afficher_details = True

        solveur_aco = TP_ACO(
            graph=graphe,
            affichage=affichage,
            nb_fourmis=len(graphe.liste_lieux),
            nb_iterations=200,
            pause=0.03
        )
        
        meilleur_ordre, meilleure_dist = solveur_aco.resoudre()

        affichage.info_label.config(
            text=f"ACO Terminé ! Distance finale : {meilleure_dist:.2f} px (NN : {dist_nn:.2f} px) | Touche [M] : Phéromones | [ESC] : Quitter"
        )

    root.bind('<space>', démarrer_aco)
    root.mainloop()


if __name__ == "__main__":
    main()