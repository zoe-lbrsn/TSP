import random
import multiprocessing as mp
from multiprocessing import shared_memory
import tkinter as tk
import numpy as np
import pandas as pd


#Variables globales
LARGEUR = 800    # taille de la fenêtre en pixels
HAUTEUR = 600
NB_LIEUX = 10    # nombre de villes tirées au hasard quand on n'a pas de fichier csv


class LIEU:
    # une ville, c'est juste des coordonnées et un nom
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name


class Graph:
    # le graphe = la liste des villes + la matrice des distances entre elles
    def __init__(self, liste_lieux=None, fichier_csv=None):
        self.liste_lieux = liste_lieux if liste_lieux is not None else []
        self.coords = None        # tableau numpy des coordonnées (rempli plus bas)
        self.matrice_od = None    # matrice des distances (rempli plus bas)

        # si on nous donne un csv, on le charge
        if fichier_csv:
            self.charger_graph(fichier_csv)
        # si on n'a toujours aucune ville (pas de csv), on en tire au hasard
        if not self.liste_lieux:
            self.generer_lieux_aleatoires(NB_LIEUX)
        # on calcule les distances une fois 
        self.calcul_matrice_cout_od()

    def generer_lieux_aleatoires(self, nb_lieux):
        marge = 40    # pour ne pas avoir de villes collées au bord de la fenêtre
        self.liste_lieux = [
            LIEU(random.uniform(marge, LARGEUR - marge),
                 random.uniform(marge, HAUTEUR - marge), f"LIEU_{i}")
            for i in range(nb_lieux)
        ]
        self.calcul_matrice_cout_od()

    def calcul_matrice_cout_od(self):
        """Matrice des distances calculée en UNE opération numpy (pas de double boucle Python)."""
        # tableau de taille n x 2 : une ligne (x, y) par ville
        self.coords = np.array([[l.x, l.y] for l in self.liste_lieux], dtype=float)
        # on soustrait les coordonnées de toutes les paires de villes d'un coup
        # broadcasting : diff[i, j] = coords[i] - coords[j]
        diff = self.coords[:, None, :] - self.coords[None, :, :]
        # Pythagore : racine de (dx² + dy²) pour chaque paire
        self.matrice_od = np.sqrt((diff ** 2).sum(axis=2))
        return self.matrice_od

    def charger_graph(self, fichier_csv):
        try:
            df = pd.read_csv(fichier_csv)
            # si le csv a une colonne "nom" on la prend, sinon on invente des noms
            noms = df['nom'].astype(str) if 'nom' in df.columns else [f"LIEU_{i}" for i in range(len(df))]
            self.liste_lieux = [LIEU(float(x), float(y), n)
                                for x, y, n in zip(df['x'], df['y'], noms)]
            self.calcul_matrice_cout_od()
        except Exception as e:
            #  on prévient et on vide la liste,
            # le constructeur prendra alors des villes au hasard
            print(f"Erreur lors du chargement du fichier CSV {fichier_csv} : {e}")
            self.liste_lieux = []

    def plus_proche_voisin_tour(self, depart=0):
        """Tour du plus proche voisin (tableau numpy, sans retour au départ)."""
        n = len(self.liste_lieux)
        D = self.matrice_od
        tour = np.empty(n, dtype=np.int64)
        libre = np.ones(n, dtype=bool)    # libre[i] = True si la ville i n'a pas encore été visitée
        tour[0] = depart
        libre[depart] = False
        cur = depart
        for k in range(1, n):
            # on regarde les distances depuis la ville courante, mais on met l'infini
            # sur les villes déjà visitées pour que argmin ne les choisisse jamais
            d = np.where(libre, D[cur], np.inf)
            cur = int(d.argmin())    # la plus proche des villes restantes
            tour[k] = cur
            libre[cur] = False
        return tour

    def longueur_tour(self, tour):
        """Longueur d'un circuit fermé (tour sans répétition du départ)."""
        # np.roll(tour, -1) donne la ville suivante de chaque ville
        # (la dernière retombe sur la première, ça ferme la boucle)
        # puis on additionne toutes les distances ville -> ville suivante
        return float(self.matrice_od[tour, np.roll(tour, -1)].sum())

    def route_fermee(self, tour, depart=0):
        """Circuit explicite : il commence à `depart` et finit par `depart`."""
        # un circuit n'a pas de vrai point de départ, c'est un cercle : on peut le "faire tourner"
        # pour que la ville `depart` se retrouve en première position, sans changer sa longueur
        pos = int(np.where(tour == depart)[0][0])
        ordre = np.roll(tour, -pos)
        # puis on remet le départ à la fin pour que le circuit soit bien fermé
        return np.append(ordre, depart)



class Affichage:
    # tout ce qui concerne la fenêtre tkinter
    def __init__(self, master, group_name="6"):
        self.master = master
        self.master.title(f"TSP - Groupe {group_name}")

        self.canvas = tk.Canvas(self.master, width=LARGEUR, height=HAUTEUR, bg='white')
        self.canvas.pack()
        # la ligne de texte en bas (itération, meilleure distance...)
        self.info_label = tk.Label(self.master, text='Initialisation du graphe du TSP',
                                   font=('Arial', 12), fg='black')
        self.info_label.pack()

        self.afficher_details = False    # True = on dessine aussi les phéromones
        self.calcul_en_cours = False     # True pendant que l'ACO tourne
        self._derniere_scene = None      # dernière image dessinée (pour la redessiner sur demande)
        #  Echap pour quitter (ESPACE est géré dans main)
        self.master.bind('<Escape>', self.quitter)

    def quitter(self, event=None):
        self.master.destroy()
        self.master.quit()

    def pheromones(self, event=None):
        # on inverse : affiché -> caché, caché -> affiché
        self.afficher_details = not self.afficher_details

        if not self.calcul_en_cours and self._derniere_scene is not None:
            self.rafraichir(*self._derniere_scene)

    def mettre_a_jour_texte(self, iteration, best_distance, iteration_trouvee):
        self.info_label.config(
            text=f"Iteration : {iteration} | Meilleure distance : {best_distance:.2f} "
                 f"(trouvée à l'itération {iteration_trouvee})")

    def _vers_canvas(self, coords):
        """Met les points à l'échelle du canvas (utile si le CSV sort de 800x600)."""
        marge = 25
        mini, maxi = coords.min(axis=0), coords.max(axis=0)
        # étendue = largeur et hauteur du nuage de points (le max(...) évite une division par 0)
        etendue = np.maximum(maxi - mini, 1e-9)
        echelle = np.array([LARGEUR - 2 * marge, HAUTEUR - 2 * marge]) / etendue
        # on décale pour que le point le plus à gauche/haut soit à la marge,
        # puis on étire pour remplir toute la fenêtre
        return (coords - mini) * echelle + marge

    def rafraichir(self, coords, tour=None, matrice_pheromones=None, max_aretes=1500, seuil=0.2):
        self._derniere_scene = (coords, tour, matrice_pheromones)
        self.canvas.delete("all")    # on efface tout et on redessine
        pts = self._vers_canvas(coords)
        n = len(pts)

        # Phéromones : uniquement les arêtes fortes, triangle supérieur seulement
        # (la matrice est symétrique, pas besoin de dessiner chaque arête 2 fois)
        if self.afficher_details and matrice_pheromones is not None:
            idx = np.argwhere(np.triu(matrice_pheromones > seuil, 1))
            # s'il y en a trop, on ne garde que les 1500 plus fortes sinon tkinter rame
            if len(idx) > max_aretes:
                vals = matrice_pheromones[idx[:, 0], idx[:, 1]]
                idx = idx[np.argpartition(vals, -max_aretes)[-max_aretes:]]
            for i, j in idx:
                ep = max(1, int(matrice_pheromones[i, j] * 6))    # plus de phéromones = trait plus épais
                self.canvas.create_line(pts[i, 0], pts[i, 1], pts[j, 0], pts[j, 1],
                                        fill='lightgray', width=ep)

        # Route : UNE seule polyligne (beaucoup plus rapide qu'un segment par arête)
        if tour is not None and len(tour) > 1:
            boucle = np.append(tour, tour[0])    # on rajoute la ville de départ pour fermer le circuit
            flat = pts[boucle].ravel().tolist()  # x1, y1, x2, y2, ... comme tkinter le veut
            self.canvas.create_line(*flat, fill='purple', width=2)

        # Lieux : les cercles rétrécissent quand il y a beaucoup de villes
        rayon = 15 if n <= 60 else (6 if n <= 200 else 3)
        for i, (x, y) in enumerate(pts):
            self.canvas.create_oval(x - rayon, y - rayon, x + rayon, y + rayon,
                                    fill='plum', outline='black')
            if n <= 60:    # les numéros ne sont lisibles que s'il y a peu de villes
                self.canvas.create_text(x, y, text=str(i), font=('Arial', 10, 'bold'))
        # update() laisse tkinter redessiner et traiter les touches pendant qu'on calcule
        self.master.update()

#  2-OPT vectorisé (pour chaque i, on teste tous les j d'un coup)
# si deux arêtes du circuit se croisent, on peut raccourcir le circuit en les
# décroisant. Pour ça on remplace (a->b) et (c->d) par (a->c) et (b->d), ce qui revient
# à retourner le morceau de circuit qui se trouve entre b et c.

def deux_opt(tour, D, max_passes=100):
    tour = tour.copy()    # on travaille sur une copie pour ne pas modifier l'original
    n = len(tour)
    if n < 5:    # trop petit pour que ça serve à quelque chose
        return tour
    for _ in range(max_passes):
        ameliore = False
        for i in range(n - 2):
            a, b = tour[i], tour[i + 1]    # première arête : a -> b
            # js = toutes les positions possibles pour la deuxième arête (c -> d)
            # on commence à i + 2 pour ne pas prendre une arête collée à la première
            # et si i = 0 on s'arrête avant la dernière ville, sinon on prendrait l'arête qui reboucle
            fin = n - 1 if i == 0 else n
            js = np.arange(i + 2, fin)
            if js.size == 0:
                continue
            c = tour[js]
            d = tour[(js + 1) % n]    # le % n sert à boucler sur la première ville
            # delta = (longueur des nouvelles arêtes) - (longueur des anciennes)
            # s'il est négatif, l'échange raccourcit le circuit
            delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
            k = int(delta.argmin())    # le meilleur échange possible pour cette position i
            if delta[k] < -1e-9:    # -1e-9 plutôt que 0 pour éviter les erreurs d'arrondi
                j = js[k]
                # on retourne le morceau entre b et c
                tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1].copy()
                ameliore = True
        if not ameliore:    # plus rien à améliorer, on s'arrête
            break
    return tour

class TP_ACO:

    def __init__(self, graph, affichage, nb_fourmis=None, alpha=1.0, beta=3.0,
                 rho=0.1, nb_iterations=500, two_opt=True, patience=200,
                 refresh_every=None, seed=None):
        # alpha = poids des phéromones, beta = poids de la proximité (visibilité)
        # rho = vitesse d'évaporation, patience = nb d'itérations sans progrès avant d'arrêter
        self.graph = graph
        self.affichage = affichage
        self.D = graph.matrice_od
        self.n = len(graph.liste_lieux)

        # Peu de fourmis suffisent, le coût est proportionnel à leur nombre
        self.m = nb_fourmis if nb_fourmis is not None else min(self.n, 30)
        self.alpha = alpha
        self.rho = rho
        self.nb_iterations = nb_iterations
        self.two_opt = two_opt
        self.patience = patience
        # avec beaucoup de villes, redessiner à chaque itération coûte cher : 1 fois sur 5 suffit
        self.refresh_every = refresh_every if refresh_every else (1 if self.n <= 200 else 5)
        self.rng = np.random.default_rng(seed)    # générateur aléatoire (seed fixe = résultats reproductibles)

        # Visibilité beta précalculée une seule fois
        # visibilité = 1 / distance : plus une ville est proche, plus elle attire
        with np.errstate(divide='ignore'): 
            eta = 1.0 / self.D
        np.fill_diagonal(eta, 0.0)
        self.eta_beta = eta ** beta

        # Solution initiale : plus proche voisin (+ 2-opt)
        # ça nous donne un premier "record" correct avant les fourmis
        tour = graph.plus_proche_voisin_tour(0)
        if self.two_opt:
            tour = deux_opt(tour, self.D)
        self.meilleur_tour = tour
        self.meilleure_distance = graph.longueur_tour(tour)
        self.iteration_trouvee = 0

        # les phéromones démarrent au maximum autorisé, ce qui pousse à explorer au début
        self._maj_bornes()
        self.tau = np.full((self.n, self.n), self.tau_max)

    def _maj_bornes(self):
        # MAX-MIN : on borne les phéromones entre tau_min et tau_max
        #  sans max, une arête pourrait prendre toute la place et bloquer l'exploration
        #  sans min, une arête pourrait tomber à 0 et ne plus jamais être essayée
        # tau_max est la valeur vers laquelle tend une arête renforcée à chaque itération
        self.tau_max = 1.0 / (self.rho * self.meilleure_distance)
        self.tau_min = self.tau_max / (2.0 * self.n)

    def construire_tours(self):
        """Toutes les fourmis avancent EN PARALLÈLE : n étapes numpy au lieu de m*n étapes Python."""
        n, m = self.n, self.m
        # choix[i, j] = envie d'aller de i à j = phéromones^alpha * visibilité^beta
        choix = (self.tau ** self.alpha) * self.eta_beta   # calculé 1 fois par itération
        tours = np.empty((m, n), dtype=np.int64)    # une ligne par fourmi
        libre = np.ones((m, n), dtype=bool)         # villes pas encore visitées, par fourmi
        lignes = np.arange(m)

        # chaque fourmi démarre dans une ville au hasard
        cur = self.rng.integers(0, n, size=m)
        tours[:, 0] = cur
        libre[lignes, cur] = False

        for k in range(1, n):
            # poids vers chaque ville, mis à 0 pour celles déjà visitées
            # (le + 1e-300 évite que tout soit nul si les poids sont minuscules)
            w = (choix[cur] + 1e-300) * libre            # poids, 0 pour les villes visitées
            # tirage à la roulette : on cumule les poids, on tire un seuil au hasard,
            # et on prend la première ville dont le cumul dépasse le seuil
            # => une ville a une proba proportionnelle à son poids
            cum = np.cumsum(w, axis=1)
            seuil = (1.0 - self.rng.random(m)) * cum[:, -1]
            cur = (cum < seuil[:, None]).sum(axis=1)     # tirage à la roulette
            tours[:, k] = cur
            libre[lignes, cur] = False
        return tours

    def pheromones_normalisees(self):
        # on ramène tout entre 0 et 1 (le plus fort = 1), c'est juste pour l'affichage
        mx = self.tau.max()
        return self.tau / mx if mx > 0 else self.tau

    def mettre_a_jour_affichage(self, iteration):
        self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
        self.affichage.rafraichir(self.graph.coords, self.meilleur_tour, self.pheromones_normalisees())

    def resoudre(self):
        self.affichage.afficher_details = True
        sans_amelioration = 0    # nb d'itérations de suite sans nouveau record
        iteration = 0
        try:
            for iteration in range(1, self.nb_iterations + 1):
                # les fourmis construisent leurs circuits et on mesure leurs longueurs
                tours = self.construire_tours()
                longueurs = self.D[tours, np.roll(tours, -1, axis=1)].sum(axis=1)

                # on garde la meilleure fourmi de cette itération et on lui passe le 2-opt
                ib = int(longueurs.argmin())
                tour_ib = tours[ib]
                if self.two_opt:
                    tour_ib = deux_opt(tour_ib, self.D)
                dist_ib = self.graph.longueur_tour(tour_ib)

                # si c'est mieux que le record, elle devient le nouveau record
                if dist_ib < self.meilleure_distance - 1e-9:
                    self.meilleure_distance = dist_ib
                    self.meilleur_tour = tour_ib
                    self.iteration_trouvee = iteration
                    self._maj_bornes()    # le record a changé donc les bornes aussi
                    sans_amelioration = 0
                else:
                    sans_amelioration += 1

                # Évaporation + dépôt de la seule meilleure fourmi (alternance itération / globale)
                # évaporation : toutes les phéromones perdent rho %
                self.tau *= (1.0 - self.rho)
                # dépôt : 4 itérations sur 5 c'est la meilleure de l'itération qui dépose,
                # la 5e fois c'est le record global (compromis exploration / exploitation)
                ref, d_ref = ((self.meilleur_tour, self.meilleure_distance)
                              if iteration % 5 == 0 else (tour_ib, dist_ib))
                a, b = ref, np.roll(ref, -1)    # a = villes, b = ville suivante : les arêtes du circuit
                depot = 1.0 / d_ref             # circuit court = gros dépôt
                self.tau[a, b] += depot
                self.tau[b, a] += depot         # dans les deux sens, la matrice est symétrique
                # on remet les valeurs dans les bornes min / max
                np.clip(self.tau, self.tau_min, self.tau_max, out=self.tau)

                # Relance des phéromones si stagnation
                # (on remet tout au max pour repartir explorer)
                if sans_amelioration == self.patience // 2:
                    self.tau[:] = self.tau_max
                # et si ça ne progresse vraiment plus, on arrête
                if sans_amelioration >= self.patience:
                    break

                # on ne redessine pas à chaque itération, ça ralentirait trop
                if iteration % self.refresh_every == 0:
                    self.mettre_a_jour_affichage(iteration)

            # affichage final : juste la meilleure route, sans les phéromones
            # on garde l'état des phéromones choisi avec ESPACE (affichées ou non)
            self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
            self.affichage.rafraichir(self.graph.coords, self.meilleur_tour, self.pheromones_normalisees())
        except tk.TclError:
            # arrive quand on ferme la fenêtre pendant que ça tourne
            print("Fenêtre fermée, arrêt de l'algorithme.")

        return self.meilleur_tour, self.meilleure_distance



def calculer_voisins(coords, D, k):
    """Pour chaque ville, indices de ses k plus proches voisins, triés par distance croissante."""
    n = len(coords)
    k = min(k, n - 1)
    try:

        from scipy.spatial import cKDTree
        _, idx = cKDTree(coords).query(coords, k=k + 1)
        return idx[:, 1:].astype(np.int64)    # on enlève la ville elle-même
    except ImportError:

        M = D + np.diag(np.full(n, np.inf))
        idx = np.argpartition(M, k - 1, axis=1)[:, :k]    # les k plus petits, mais pas triés
        ordre = np.argsort(np.take_along_axis(M, idx, axis=1), axis=1)    # on les trie
        return np.take_along_axis(idx, ordre, axis=1).astype(np.int64)


def deux_opt_voisins(tour, D, cand, max_passes=50):

    tour = tour.copy()
    n = len(tour)
    if n < 5:
        return tour
    pos = np.empty(n, dtype=np.int64)
    pos[tour] = np.arange(n)
    dlb = np.zeros(n, dtype=bool)
    for _ in range(max_passes):
        ameliore = False
        for i in range(n):
            a = tour[i]
            if dlb[a]:
                continue
            c = cand[a]
            j = pos[c]
            trouve = False
            # sens 1 : arête a -> suivant(a)
            b = tour[(i + 1) % n]
            d = tour[(j + 1) % n]
            delta1 = D[a, c] + D[b, d] - D[a, b] - D[c, d]
            # sens 2 : arête précédent(a) -> a
            b2 = tour[(i - 1) % n]
            d2 = tour[(j - 1) % n]
            delta2 = D[a, c] + D[b2, d2] - D[a, b2] - D[c, d2]
            k1, k2 = int(delta1.argmin()), int(delta2.argmin())
            if delta1[k1] <= delta2[k2]:
                delta, k, p1, p2, v = delta1[k1], k1, i, int(j[k1]), (b, d[k1])
            else:
                delta, k, p1, p2, v = delta2[k2], k2, (i - 1) % n, (int(j[k2]) - 1) % n, (b2, d2[k2])
            if delta < -1e-9:
                lo, hi = min(p1, p2) + 1, max(p1, p2)
                seg = tour[lo:hi + 1][::-1].copy()
                tour[lo:hi + 1] = seg
                pos[seg] = np.arange(lo, hi + 1)
                dlb[a] = dlb[c[k]] = dlb[v[0]] = dlb[v[1]] = False
                ameliore = True
            else:
                dlb[a] = True
        if not ameliore:
            break
    return tour


# _G = "variables globales du worker" : chaque processus y range ce dont il a besoin
# (les gros tableaux en mémoire partagée, le nombre de villes, etc.)
_G = {}


def _init_worker(nom_D, nom_eb, nom_tau, n, alpha, cand):
    # appelée UNE fois au démarrage de chaque processus
    # on se branche sur les blocs de mémoire partagée par leur nom : pas de copie,
    # tous les processus lisent les mêmes matrices (D, visibilité, phéromones)
    for cle, nom in (("D", nom_D), ("eb", nom_eb), ("tau", nom_tau)):
        shm = shared_memory.SharedMemory(name=nom)
        _G[cle + "_shm"] = shm    # on garde la référence, sinon la mémoire serait libérée
        _G[cle] = np.ndarray((n, n), dtype=np.float64, buffer=shm.buf)
    _G["n"], _G["alpha"], _G["cand"] = n, alpha, cand


def _travail(args):
    """Construit nb fourmis et renvoie la meilleure route (2-opt éventuel) et sa longueur."""
    # c'est ce que chaque processus exécute à chaque itération
    nb, graine, faire_2opt = args
    n, D = _G["n"], _G["D"]
    rng = np.random.default_rng(graine)    # graine différente par processus, sinon ils feraient tous pareil
    choix = (_G["tau"] ** _G["alpha"]) * _G["eb"]    # envie d'aller de i à j (phéromones * visibilité)

    # les nb fourmis du processus avancent en même temps, ville par ville
    tours = np.empty((nb, n), dtype=np.int64)
    libre = np.ones((nb, n), dtype=bool)
    lignes = np.arange(nb)
    cur = rng.integers(0, n, size=nb)
    tours[:, 0] = cur
    libre[lignes, cur] = False
    for k in range(1, n):
        w = (choix[cur] + 1e-300) * libre    # poids, 0 sur les villes déjà visitées
        cum = np.cumsum(w, axis=1)
        seuil = (1.0 - rng.random(nb)) * cum[:, -1]
        cur = (cum < seuil[:, None]).sum(axis=1)    
        tours[:, k] = cur
        libre[lignes, cur] = False

    # on ne renvoie que la meilleure fourmi de ce processus
    longueurs = D[tours, np.roll(tours, -1, axis=1)].sum(axis=1)
    tour = tours[int(longueurs.argmin())]
    if faire_2opt:   
        tour = deux_opt_voisins(tour, D, _G["cand"])
    return tour, float(D[tour, np.roll(tour, -1)].sum())



class TP_ACO_V2:
    # les fourmis sont réparties entre plusieurs processus
    # (un par coeur) : chacun construit ses fourmis en parallèle des autres
    def __init__(self, graph, affichage, nb_processus=4, fourmis_par_proc=8,
                 alpha=1.0, beta=3.0, rho=0.1, nb_iterations=300,
                 two_opt_every=3, nb_voisins=15, patience=100,
                 refresh_every=None, seed=None):
        # nb_processus * fourmis_par_proc = nombre total de fourmis (4 * 8 = 32 par défaut)
        # two_opt_every = on fait le 2-opt une itération sur 3
        # nb_voisins = taille des listes de voisins utilisées par le 2-opt
        self.graph = graph
        self.affichage = affichage
        self.D = graph.matrice_od
        self.n = len(graph.liste_lieux)
        # nombre de fourmis adapté à la taille du graphe (jamais plus de fourmis que de villes)
        total = min(self.n, max(1, nb_processus) * fourmis_par_proc)
        # en dessous de 100 villes, lancer des processus coûte plus cher que ça ne rapporte
        self.P = 1 if self.n < 100 else max(1, min(nb_processus, total))
        self.fpp = max(1, total // self.P)    # fourmis par processus
        self.alpha, self.rho = alpha, rho
        self.nb_iterations = nb_iterations
        self.two_opt_every = max(1, two_opt_every)
        self.patience = patience
        self.refresh_every = refresh_every if refresh_every else (1 if self.n <= 200 else 5)
        self.rng = np.random.default_rng(seed)

        # visibilité = 1 / distance, puis ^beta, calculée une seule fois
        with np.errstate(divide='ignore'):
            eta = 1.0 / self.D
        np.fill_diagonal(eta, 0.0)
        self.eta_beta = eta ** beta

        self.cand = calculer_voisins(graph.coords, self.D, nb_voisins)

        # première solution : plus proche voisin amélioré par le 2-opt
        tour = deux_opt_voisins(graph.plus_proche_voisin_tour(0), self.D, self.cand)
        self.meilleur_tour = tour
        self.meilleure_distance = graph.longueur_tour(tour)
        self.iteration_trouvee = 0
        self._maj_bornes()
        self.tau = np.full((self.n, self.n), self.tau_max)

    def _maj_bornes(self):
        # bornes MAX-MIN des phéromones (voir l'explication dans l'autre fichier)
        self.tau_max = 1.0 / (self.rho * self.meilleure_distance)
        self.tau_min = self.tau_max / (2.0 * self.n)

    def _memoire_partagee(self):
        # on met les 3 grosses matrices dans de la mémoire partagée pour que les processus
        # les lisent directement, sans qu'on ait à les copier / envoyer à chaque itération
        self._shms = []

        def partager(t):
            shm = shared_memory.SharedMemory(create=True, size=t.nbytes)
            vue = np.ndarray(t.shape, dtype=np.float64, buffer=shm.buf)
            vue[:] = t    # on copie le contenu dans le bloc partagé
            self._shms.append(shm)
            return shm.name, vue

        nD, _ = partager(self.D)
        nE, _ = partager(self.eta_beta)
        #  quand on modifie les phéromones ici, les processus voient directement le changement
        nT, self.tau = partager(self.tau)
        return nD, nE, nT

    def _liberer(self):

        self.tau = np.array(self.tau)
        _G.clear()
        for shm in self._shms:
            try:
                shm.close()
            except BufferError:
                pass
            shm.unlink()

    def pheromones_normalisees(self):
        # entre 0 et 1, juste pour l'affichage
        mx = self.tau.max()
        return self.tau / mx if mx > 0 else self.tau

    def mettre_a_jour_affichage(self, iteration):
        self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
        self.affichage.rafraichir(self.graph.coords, self.meilleur_tour, self.pheromones_normalisees())

    def resoudre(self):
        self.affichage.afficher_details = True
        noms = self._memoire_partagee()
        initargs = (*noms, self.n, self.alpha, self.cand)
        pool = None
        if self.P > 1:
            # on lance P processus ; chacun exécute _init_worker une fois au démarrage
            pool = mp.Pool(self.P, initializer=_init_worker, initargs=initargs)
            executer = pool.map
        else:
            # avec 1 seul processus on fait le calcul ici directement
            # (pratique pour comparer 1 coeur contre 4 avec exactement le même code)
            _init_worker(*initargs) 
            executer = lambda f, taches: list(map(f, taches))

        sans_amelioration = 0    # nb d'itérations de suite sans nouveau record
        iteration = 0
        try:
            for iteration in range(1, self.nb_iterations + 1):
                faire_2opt = (iteration - 1) % self.two_opt_every == 0
                # une graine aléatoire différente par processus
                graines = self.rng.integers(0, 2**32 - 1, size=self.P)
                taches = [(self.fpp, int(g), faire_2opt) for g in graines]

                # chaque processus construit ses fourmis, et on récupère la meilleure de chacun
                resultats = executer(_travail, taches)           # PARTIE PARALLÈLE
                # parmi les P meilleures, on prend la plus courte
                tour_ib, dist_ib = min(resultats, key=lambda r: r[1])

                # nouveau record ?
                if dist_ib < self.meilleure_distance - 1e-9:
                    self.meilleure_distance = dist_ib
                    self.meilleur_tour = tour_ib
                    self.iteration_trouvee = iteration
                    self._maj_bornes()
                    sans_amelioration = 0
                else:
                    sans_amelioration += 1

                # mise à jour des phéromones : ça on le fait ici, tout seul, une seule fois
                # (c'est la partie qu'on ne peut pas paralléliser)
                self.tau *= (1.0 - self.rho)                     # PARTIE SÉQUENTIELLE
                # 1 itération sur 5 c'est le record qui dépose, sinon la meilleure de l'itération
                ref, d_ref = ((self.meilleur_tour, self.meilleure_distance)
                              if iteration % 5 == 0 else (tour_ib, dist_ib))
                a, b = ref, np.roll(ref, -1)    # les arêtes du circuit : ville -> ville suivante
                self.tau[a, b] += 1.0 / d_ref   # circuit court = gros dépôt
                self.tau[b, a] += 1.0 / d_ref   # et dans l'autre sens aussi
                np.clip(self.tau, self.tau_min, self.tau_max, out=self.tau)

                # si ça stagne, on remet les phéromones au max pour relancer l'exploration
                if sans_amelioration == self.patience // 2:
                    self.tau[:] = self.tau_max
                # et si ça stagne trop longtemps, on arrête
                if sans_amelioration >= self.patience:
                    break

                if iteration % self.refresh_every == 0:
                    self.mettre_a_jour_affichage(iteration)

            # nettoyage final : un 2-opt complet (1 seule fois, très rapide) garantit
            # qu'il ne reste aucun croisement dans la route finale
            tour_final = deux_opt(self.meilleur_tour, self.D)
            dist_finale = self.graph.longueur_tour(tour_final)
            if dist_finale < self.meilleure_distance - 1e-9:
                self.meilleur_tour, self.meilleure_distance = tour_final, dist_finale
            # on garde l'état des phéromones choisi avec ESPACE (affichées ou non)
            self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
            self.affichage.rafraichir(self.graph.coords, self.meilleur_tour, self.pheromones_normalisees())
        except tk.TclError:
            # fenêtre fermée pendant le calcul
            print("Fenêtre fermée, arrêt de l'algorithme.")
        finally:
            # quoi qu'il arrive (fin normale, fenêtre fermée, erreur) on referme proprement
            # les processus et on libère la mémoire partagée
            if pool is not None:
                pool.close()
                pool.join()
            self._liberer()

        return self.meilleur_tour, self.meilleure_distance


def main():
    root = tk.Tk()
    graphe = Graph(fichier_csv="graph_150.csv")
    affichage = Affichage(root, group_name="6")

    # on affiche d'abord la solution "plus proche voisin" comme point de comparaison
    tour_nn = graphe.plus_proche_voisin_tour(0)
    dist_nn = graphe.longueur_tour(tour_nn)
    affichage.rafraichir(graphe.coords, tour_nn)
    affichage.info_label.config(
        text=f"[Plus Proche Voisin] Distance : {dist_nn:.2f} px | Appuie sur [ESPACE] pour lancer ACO")

    def demarrer_aco(event=None):
        affichage.calcul_en_cours = True
        solveur = TP_ACO_V2(graph=graphe, affichage=affichage,
                            nb_processus=4,       
                            fourmis_par_proc=8,
                            two_opt_every=3,
                            nb_iterations=300)
        meilleur_tour, meilleure_dist = solveur.resoudre()
        affichage.calcul_en_cours = False
        route = graphe.route_fermee(meilleur_tour)    # départ = ville 0, arrivée = ville 0
        print(f"Circuit final : départ {route[0]}, arrivée {route[-1]}, {len(route) - 1} villes visitées")
        affichage.info_label.config(
            text=f"ACO terminé ! Distance finale : {meilleure_dist:.2f} px (Heuristique : {dist_nn:.2f} px) "
                 f" \n  [ESC] : Quitter ")

    # 1er appui sur ESPACE : on lance l'algo. Ensuite : chaque appui affiche / cache les phéromones
    lance = [False]
    def touche_espace(event=None):
        if not lance[0]:
            lance[0] = True
            demarrer_aco()
        else:
            affichage.pheromones()

    root.bind('<space>', touche_espace)
    root.mainloop()


if __name__ == "__main__":
    mp.freeze_support()   
    main()