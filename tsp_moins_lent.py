import random
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
# 2. GRAPHE
# ==============================================================================
class LIEU:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name


class Graph:
    def __init__(self, liste_lieux=None, fichier_csv=None):
        self.liste_lieux = liste_lieux if liste_lieux is not None else []
        self.coords = None
        self.matrice_od = None

        if fichier_csv:
            self.charger_graph(fichier_csv)
        if not self.liste_lieux:
            self.generer_lieux_aleatoires(NB_LIEUX)
        self.calcul_matrice_cout_od()

    def generer_lieux_aleatoires(self, nb_lieux):
        marge = 40
        self.liste_lieux = [
            LIEU(random.uniform(marge, LARGEUR - marge),
                 random.uniform(marge, HAUTEUR - marge), f"LIEU_{i}")
            for i in range(nb_lieux)
        ]
        self.calcul_matrice_cout_od()

    def calcul_matrice_cout_od(self):
        """Matrice des distances calculée en UNE opération numpy (pas de double boucle Python)."""
        self.coords = np.array([[l.x, l.y] for l in self.liste_lieux], dtype=float)
        diff = self.coords[:, None, :] - self.coords[None, :, :]
        self.matrice_od = np.sqrt((diff ** 2).sum(axis=2))
        return self.matrice_od

    def charger_graph(self, fichier_csv):
        try:
            df = pd.read_csv(fichier_csv)
            noms = df['nom'].astype(str) if 'nom' in df.columns else [f"LIEU_{i}" for i in range(len(df))]
            self.liste_lieux = [LIEU(float(x), float(y), n)
                                for x, y, n in zip(df['x'], df['y'], noms)]
            self.calcul_matrice_cout_od()
        except Exception as e:
            print(f"Erreur lors du chargement du fichier CSV {fichier_csv} : {e}")
            self.liste_lieux = []

    def plus_proche_voisin_tour(self, depart=0):
        """Tour du plus proche voisin (tableau numpy, sans retour au départ)."""
        n = len(self.liste_lieux)
        D = self.matrice_od
        tour = np.empty(n, dtype=np.int64)
        libre = np.ones(n, dtype=bool)
        tour[0] = depart
        libre[depart] = False
        cur = depart
        for k in range(1, n):
            d = np.where(libre, D[cur], np.inf)
            cur = int(d.argmin())
            tour[k] = cur
            libre[cur] = False
        return tour

    def longueur_tour(self, tour):
        """Longueur d'un circuit fermé (tour sans répétition du départ)."""
        return float(self.matrice_od[tour, np.roll(tour, -1)].sum())


# ==============================================================================
# 3. AFFICHAGE (allégé : une seule polyligne pour la route, peu de lignes de phéromones)
# ==============================================================================
class Affichage:
    def __init__(self, master, group_name="6"):
        self.master = master
        self.master.title(f"TSP - Groupe {group_name}")

        self.canvas = tk.Canvas(self.master, width=LARGEUR, height=HAUTEUR, bg='white')
        self.canvas.pack()
        self.info_label = tk.Label(self.master, text='Initialisation du graphe du TSP',
                                   font=('Arial', 12), fg='black')
        self.info_label.pack()

        self.afficher_details = False
        self.master.bind('<Escape>', self.quitter)
        self.master.bind('<m>', self.pheromones)
        self.master.bind('<M>', self.pheromones)

    def quitter(self, event=None):
        self.master.destroy()
        self.master.quit()

    def pheromones(self, event=None):
        self.afficher_details = not self.afficher_details

    def mettre_a_jour_texte(self, iteration, best_distance, iteration_trouvee):
        self.info_label.config(
            text=f"Iteration : {iteration} | Meilleure distance : {best_distance:.2f} "
                 f"(trouvée à l'itération {iteration_trouvee})")

    def _vers_canvas(self, coords):
        """Met les points à l'échelle du canvas (utile si le CSV sort de 800x600)."""
        marge = 25
        mini, maxi = coords.min(axis=0), coords.max(axis=0)
        etendue = np.maximum(maxi - mini, 1e-9)
        echelle = np.array([LARGEUR - 2 * marge, HAUTEUR - 2 * marge]) / etendue
        return (coords - mini) * echelle + marge

    def rafraichir(self, coords, tour=None, matrice_pheromones=None, max_aretes=1500, seuil=0.2):
        self.canvas.delete("all")
        pts = self._vers_canvas(coords)
        n = len(pts)

        # Phéromones : uniquement les arêtes fortes, triangle supérieur seulement
        if self.afficher_details and matrice_pheromones is not None:
            idx = np.argwhere(np.triu(matrice_pheromones > seuil, 1))
            if len(idx) > max_aretes:
                vals = matrice_pheromones[idx[:, 0], idx[:, 1]]
                idx = idx[np.argpartition(vals, -max_aretes)[-max_aretes:]]
            for i, j in idx:
                ep = max(1, int(matrice_pheromones[i, j] * 6))
                self.canvas.create_line(pts[i, 0], pts[i, 1], pts[j, 0], pts[j, 1],
                                        fill='lightgray', width=ep)

        # Route : UNE seule polyligne
        if tour is not None and len(tour) > 1:
            boucle = np.append(tour, tour[0])
            flat = pts[boucle].ravel().tolist()
            self.canvas.create_line(*flat, fill='purple', width=2)

        # Lieux
        rayon = 15 if n <= 60 else (6 if n <= 200 else 3)
        for i, (x, y) in enumerate(pts):
            self.canvas.create_oval(x - rayon, y - rayon, x + rayon, y + rayon,
                                    fill='plum', outline='black')
            if n <= 60:
                self.canvas.create_text(x, y, text=str(i), font=('Arial', 10, 'bold'))
        self.master.update()


# ==============================================================================
# 4. 2-OPT VECTORISÉ (pour chaque i, on teste tous les j d'un coup)
# ==============================================================================
def deux_opt(tour, D, max_passes=100):
    tour = tour.copy()
    n = len(tour)
    if n < 5:
        return tour
    for _ in range(max_passes):
        ameliore = False
        for i in range(n - 2):
            a, b = tour[i], tour[i + 1]
            fin = n - 1 if i == 0 else n
            js = np.arange(i + 2, fin)
            if js.size == 0:
                continue
            c = tour[js]
            d = tour[(js + 1) % n]
            delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
            k = int(delta.argmin())
            if delta[k] < -1e-9:
                j = js[k]
                tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1].copy()
                ameliore = True
        if not ameliore:
            break
    return tour


# ==============================================================================
# 5. ACO (style MAX-MIN Ant System) VECTORISÉ
# ==============================================================================
class TP_ACO:
    def __init__(self, graph, affichage, nb_fourmis=None, alpha=1.0, beta=3.0,
                 rho=0.1, nb_iterations=300, two_opt=True, patience=100,
                 refresh_every=None, seed=None):
        self.graph = graph
        self.affichage = affichage
        self.D = graph.matrice_od
        self.n = len(graph.liste_lieux)

        # Peu de fourmis suffisent (20-30) : le coût est proportionnel à leur nombre
        self.m = nb_fourmis if nb_fourmis is not None else min(self.n, 30)
        self.alpha = alpha
        self.rho = rho
        self.nb_iterations = nb_iterations
        self.two_opt = two_opt
        self.patience = patience
        self.refresh_every = refresh_every if refresh_every else (1 if self.n <= 200 else 5)
        self.rng = np.random.default_rng(seed)

        # Visibilité^beta précalculée une fois pour toutes
        with np.errstate(divide='ignore'):
            eta = 1.0 / self.D
        np.fill_diagonal(eta, 0.0)
        self.eta_beta = eta ** beta

        # Solution initiale : plus proche voisin (+ 2-opt)
        tour = graph.plus_proche_voisin_tour(0)
        if self.two_opt:
            tour = deux_opt(tour, self.D)
        self.meilleur_tour = tour
        self.meilleure_distance = graph.longueur_tour(tour)
        self.iteration_trouvee = 0

        self._maj_bornes()
        self.tau = np.full((self.n, self.n), self.tau_max)

    def _maj_bornes(self):
        self.tau_max = 1.0 / (self.rho * self.meilleure_distance)
        self.tau_min = self.tau_max / (2.0 * self.n)

    def construire_tours(self):
        """Toutes les fourmis avancent EN PARALLÈLE : n étapes numpy au lieu de m*n étapes Python."""
        n, m = self.n, self.m
        choix = (self.tau ** self.alpha) * self.eta_beta   # calculé 1 fois par itération
        tours = np.empty((m, n), dtype=np.int64)
        libre = np.ones((m, n), dtype=bool)
        lignes = np.arange(m)

        cur = self.rng.integers(0, n, size=m)
        tours[:, 0] = cur
        libre[lignes, cur] = False

        for k in range(1, n):
            w = (choix[cur] + 1e-300) * libre            # poids, 0 pour les villes visitées
            cum = np.cumsum(w, axis=1)
            seuil = (1.0 - self.rng.random(m)) * cum[:, -1]
            cur = (cum < seuil[:, None]).sum(axis=1)     # tirage à la roulette
            tours[:, k] = cur
            libre[lignes, cur] = False
        return tours

    def pheromones_normalisees(self):
        mx = self.tau.max()
        return self.tau / mx if mx > 0 else self.tau

    def mettre_a_jour_affichage(self, iteration):
        self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
        self.affichage.rafraichir(self.graph.coords, self.meilleur_tour, self.pheromones_normalisees())

    def resoudre(self):
        self.affichage.afficher_details = True
        sans_amelioration = 0
        iteration = 0
        try:
            for iteration in range(1, self.nb_iterations + 1):
                tours = self.construire_tours()
                longueurs = self.D[tours, np.roll(tours, -1, axis=1)].sum(axis=1)

                ib = int(longueurs.argmin())
                tour_ib = tours[ib]
                if self.two_opt:
                    tour_ib = deux_opt(tour_ib, self.D)
                dist_ib = self.graph.longueur_tour(tour_ib)

                if dist_ib < self.meilleure_distance - 1e-9:
                    self.meilleure_distance = dist_ib
                    self.meilleur_tour = tour_ib
                    self.iteration_trouvee = iteration
                    self._maj_bornes()
                    sans_amelioration = 0
                else:
                    sans_amelioration += 1

                # Évaporation + dépôt de la seule meilleure fourmi (alternance itération / globale)
                self.tau *= (1.0 - self.rho)
                ref, d_ref = ((self.meilleur_tour, self.meilleure_distance)
                              if iteration % 5 == 0 else (tour_ib, dist_ib))
                a, b = ref, np.roll(ref, -1)
                depot = 1.0 / d_ref
                self.tau[a, b] += depot
                self.tau[b, a] += depot
                np.clip(self.tau, self.tau_min, self.tau_max, out=self.tau)

                # Relance des phéromones si stagnation
                if sans_amelioration == self.patience // 2:
                    self.tau[:] = self.tau_max
                if sans_amelioration >= self.patience:
                    break

                if iteration % self.refresh_every == 0:
                    self.mettre_a_jour_affichage(iteration)

            self.affichage.afficher_details = False
            self.affichage.mettre_a_jour_texte(iteration, self.meilleure_distance, self.iteration_trouvee)
            self.affichage.rafraichir(self.graph.coords, self.meilleur_tour)
        except tk.TclError:
            print("Fenêtre fermée, arrêt de l'algorithme.")

        return self.meilleur_tour, self.meilleure_distance


# ==============================================================================
# 6. MAIN
# ==============================================================================
def main():
    root = tk.Tk()

    graphe = Graph(fichier_csv="graph_1000.csv")   # tombe sur des lieux aléatoires si le fichier manque
    affichage = Affichage(root, group_name="6")

    tour_nn = graphe.plus_proche_voisin_tour(0)
    dist_nn = graphe.longueur_tour(tour_nn)
    affichage.rafraichir(graphe.coords, tour_nn)
    affichage.info_label.config(
        text=f"[Plus Proche Voisin] Distance : {dist_nn:.2f} px | Appuie sur [ESPACE] pour lancer ACO")

    def demarrer_aco(event=None):
        root.unbind('<space>')
        solveur = TP_ACO(graph=graphe, affichage=affichage, nb_iterations=300)
        _, meilleure_dist = solveur.resoudre()
        affichage.info_label.config(
            text=f"ACO terminé ! Distance finale : {meilleure_dist:.2f} px (NN : {dist_nn:.2f} px) "
                 f"| [M] : Phéromones | [ESC] : Quitter")

    root.bind('<space>', demarrer_aco)
    root.mainloop()


if __name__ == "__main__":
    main()