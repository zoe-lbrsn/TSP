"""
ACO parallèle v2.

Améliorations par rapport à tsp_aco_parallele.py :
  1. 2-opt à LISTES DE VOISINS (on ne teste que les k plus proches voisins de chaque ville
     + "don't look bits") : beaucoup plus rapide que le 2-opt complet, et coût ~ linéaire en n.
  2. 2-opt appliqué seulement toutes les `two_opt_every` itérations.
  3. Plus de fourmis par coeur (fourmis_par_proc) : à temps réel égal, on explore plus de routes.
  4. nb_processus=1 => exécution séquentielle (même code) pour comparer proprement 1 vs 4 coeurs.

Nécessite tsp_aco_rapide.py dans le même dossier. scipy est optionnel (accélère la recherche des voisins).
"""
import multiprocessing as mp
from multiprocessing import shared_memory
import tkinter as tk
import numpy as np

from tsp_moins_lent import Graph, Affichage


# ==============================================================================
# VOISINS + 2-OPT À LISTES DE VOISINS
# ==============================================================================
def calculer_voisins(coords, D, k):
    """Pour chaque ville, indices de ses k plus proches voisins, triés par distance croissante."""
    n = len(coords)
    k = min(k, n - 1)
    try:
        from scipy.spatial import cKDTree
        _, idx = cKDTree(coords).query(coords, k=k + 1)
        return idx[:, 1:].astype(np.int64)            # on enlève la ville elle-même
    except ImportError:
        M = D + np.diag(np.full(n, np.inf))
        idx = np.argpartition(M, k - 1, axis=1)[:, :k]
        ordre = np.argsort(np.take_along_axis(M, idx, axis=1), axis=1)
        return np.take_along_axis(idx, ordre, axis=1).astype(np.int64)


def deux_opt_voisins(tour, D, cand, max_passes=50):
    """2-opt restreint aux voisins proches, avec don't-look bits."""
    tour = tour.copy()
    n = len(tour)
    if n < 5:
        return tour
    pos = np.empty(n, dtype=np.int64)
    pos[tour] = np.arange(n)
    dlb = np.zeros(n, dtype=bool)                      # True = "inutile de regarder cette ville"
    for _ in range(max_passes):
        ameliore = False
        for i in range(n):
            a = tour[i]
            if dlb[a]:
                continue
            b = tour[(i + 1) % n]
            c = cand[a]                                # voisins de a
            j = pos[c]
            d = tour[(j + 1) % n]
            delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
            k = int(delta.argmin())
            if delta[k] < -1e-9:
                jk = int(j[k])
                lo, hi = (i, jk) if i < jk else (jk, i)
                seg = tour[lo + 1:hi + 1][::-1].copy()
                tour[lo + 1:hi + 1] = seg
                pos[seg] = np.arange(lo + 1, hi + 1)
                dlb[a] = dlb[b] = dlb[c[k]] = dlb[d[k]] = False
                ameliore = True
            else:
                dlb[a] = True
        if not ameliore:
            break
    return tour


# ==============================================================================
# CÔTÉ WORKER
# ==============================================================================
_G = {}


def _init_worker(nom_D, nom_eb, nom_tau, n, alpha, cand):
    for cle, nom in (("D", nom_D), ("eb", nom_eb), ("tau", nom_tau)):
        shm = shared_memory.SharedMemory(name=nom)
        _G[cle + "_shm"] = shm
        _G[cle] = np.ndarray((n, n), dtype=np.float64, buffer=shm.buf)
    _G["n"], _G["alpha"], _G["cand"] = n, alpha, cand


def _travail(args):
    """Construit `nb` fourmis ; renvoie la meilleure route (2-opt éventuel) et sa longueur."""
    nb, graine, faire_2opt = args
    n, D = _G["n"], _G["D"]
    rng = np.random.default_rng(graine)
    choix = (_G["tau"] ** _G["alpha"]) * _G["eb"]

    tours = np.empty((nb, n), dtype=np.int64)
    libre = np.ones((nb, n), dtype=bool)
    lignes = np.arange(nb)
    cur = rng.integers(0, n, size=nb)
    tours[:, 0] = cur
    libre[lignes, cur] = False
    for k in range(1, n):
        w = (choix[cur] + 1e-300) * libre
        cum = np.cumsum(w, axis=1)
        seuil = (1.0 - rng.random(nb)) * cum[:, -1]
        cur = (cum < seuil[:, None]).sum(axis=1)
        tours[:, k] = cur
        libre[lignes, cur] = False

    longueurs = D[tours, np.roll(tours, -1, axis=1)].sum(axis=1)
    tour = tours[int(longueurs.argmin())]
    if faire_2opt:
        tour = deux_opt_voisins(tour, D, _G["cand"])
    return tour, float(D[tour, np.roll(tour, -1)].sum())


# ==============================================================================
# ACO
# ==============================================================================
class TP_ACO_V2:
    def __init__(self, graph, affichage, nb_processus=4, fourmis_par_proc=8,
                 alpha=1.0, beta=3.0, rho=0.1, nb_iterations=300,
                 two_opt_every=3, nb_voisins=15, patience=100,
                 refresh_every=None, seed=None):
        self.graph = graph
        self.affichage = affichage
        self.D = graph.matrice_od
        self.n = len(graph.liste_lieux)
        self.P = max(1, nb_processus)
        self.fpp = fourmis_par_proc
        self.alpha, self.rho = alpha, rho
        self.nb_iterations = nb_iterations
        self.two_opt_every = max(1, two_opt_every)
        self.patience = patience
        self.refresh_every = refresh_every if refresh_every else (1 if self.n <= 200 else 5)
        self.rng = np.random.default_rng(seed)

        with np.errstate(divide='ignore'):
            eta = 1.0 / self.D
        np.fill_diagonal(eta, 0.0)
        self.eta_beta = eta ** beta

        self.cand = calculer_voisins(graph.coords, self.D, nb_voisins)

        tour = deux_opt_voisins(graph.plus_proche_voisin_tour(0), self.D, self.cand)
        self.meilleur_tour = tour
        self.meilleure_distance = graph.longueur_tour(tour)
        self.iteration_trouvee = 0
        self._maj_bornes()
        self.tau = np.full((self.n, self.n), self.tau_max)

    def _maj_bornes(self):
        self.tau_max = 1.0 / (self.rho * self.meilleure_distance)
        self.tau_min = self.tau_max / (2.0 * self.n)

    def _memoire_partagee(self):
        self._shms = []

        def partager(t):
            shm = shared_memory.SharedMemory(create=True, size=t.nbytes)
            vue = np.ndarray(t.shape, dtype=np.float64, buffer=shm.buf)
            vue[:] = t
            self._shms.append(shm)
            return shm.name, vue

        nD, _ = partager(self.D)
        nE, _ = partager(self.eta_beta)
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
            pool = mp.Pool(self.P, initializer=_init_worker, initargs=initargs)
            executer = pool.map
        else:
            _init_worker(*initargs)                  # mode séquentiel : même code, même process
            executer = lambda f, taches: list(map(f, taches))

        sans_amelioration = 0
        iteration = 0
        try:
            for iteration in range(1, self.nb_iterations + 1):
                faire_2opt = (iteration - 1) % self.two_opt_every == 0
                graines = self.rng.integers(0, 2**32 - 1, size=self.P)
                taches = [(self.fpp, int(g), faire_2opt) for g in graines]

                resultats = executer(_travail, taches)           # PARTIE PARALLÈLE
                tour_ib, dist_ib = min(resultats, key=lambda r: r[1])

                if dist_ib < self.meilleure_distance - 1e-9:
                    self.meilleure_distance = dist_ib
                    self.meilleur_tour = tour_ib
                    self.iteration_trouvee = iteration
                    self._maj_bornes()
                    sans_amelioration = 0
                else:
                    sans_amelioration += 1

                self.tau *= (1.0 - self.rho)                     # PARTIE SÉQUENTIELLE
                ref, d_ref = ((self.meilleur_tour, self.meilleure_distance)
                              if iteration % 5 == 0 else (tour_ib, dist_ib))
                a, b = ref, np.roll(ref, -1)
                self.tau[a, b] += 1.0 / d_ref
                self.tau[b, a] += 1.0 / d_ref
                np.clip(self.tau, self.tau_min, self.tau_max, out=self.tau)

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
        finally:
            if pool is not None:
                pool.close()
                pool.join()
            self._liberer()

        return self.meilleur_tour, self.meilleure_distance


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    root = tk.Tk()
    graphe = Graph(fichier_csv="graph_1000.csv")
    affichage = Affichage(root, group_name="6")

    tour_nn = graphe.plus_proche_voisin_tour(0)
    dist_nn = graphe.longueur_tour(tour_nn)
    affichage.rafraichir(graphe.coords, tour_nn)
    affichage.info_label.config(
        text=f"[Plus Proche Voisin] Distance : {dist_nn:.2f} px | Appuie sur [ESPACE] pour lancer ACO")

    def demarrer_aco(event=None):
        root.unbind('<space>')
        solveur = TP_ACO_V2(graph=graphe, affichage=affichage,
                            nb_processus=4,          # <- mets 1 pour comparer en séquentiel
                            fourmis_par_proc=8,
                            two_opt_every=3,
                            nb_iterations=300)
        _, meilleure_dist = solveur.resoudre()
        affichage.info_label.config(
            text=f"ACO terminé ! Distance finale : {meilleure_dist:.2f} px (NN : {dist_nn:.2f} px) "
                 f"| [M] : Phéromones | [ESC] : Quitter")

    root.bind('<space>', demarrer_aco)
    root.mainloop()


if __name__ == "__main__":
    mp.freeze_support()
    main()