"""
ACO parallélisé : chaque processus (un par coeur) construit son groupe de fourmis,
applique le 2-opt sur sa meilleure route et renvoie le résultat au processus principal.

Les grosses matrices (distances, visibilité, phéromones) sont en MÉMOIRE PARTAGÉE :
on ne les copie/sérialise pas à chaque itération, les workers les lisent directement.

Nécessite tsp_aco_rapide.py dans le même dossier.
"""
import multiprocessing as mp
from multiprocessing import shared_memory
import tkinter as tk
import numpy as np

from tsp_moins_lent import Graph, Affichage, TP_ACO, deux_opt


# ==============================================================================
# CÔTÉ WORKER (fonctions au niveau du module, obligatoire pour multiprocessing)
# ==============================================================================
_G = {}


def _init_worker(nom_D, nom_eb, nom_tau, n, alpha):
    """Chaque worker s'attache une fois aux blocs de mémoire partagée."""
    for cle, nom in (("D", nom_D), ("eb", nom_eb), ("tau", nom_tau)):
        shm = shared_memory.SharedMemory(name=nom)
        _G[cle + "_shm"] = shm                      # garder la référence en vie
        _G[cle] = np.ndarray((n, n), dtype=np.float64, buffer=shm.buf)
    _G["n"] = n
    _G["alpha"] = alpha


def _travail_fourmis(args):
    """Construit nb fourmis, renvoie la meilleure route (après 2-opt) et sa longueur."""
    nb, graine, two_opt = args
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
    ib = int(longueurs.argmin())
    tour = tours[ib]
    if two_opt:
        tour = deux_opt(tour, D)
    return tour, float(D[tour, np.roll(tour, -1)].sum())


# ==============================================================================
# CÔTÉ PROCESSUS PRINCIPAL
# ==============================================================================
class TP_ACO_Parallele(TP_ACO):
    def __init__(self, graph, affichage, nb_processus=4, nb_fourmis=None, **kwargs):
        super().__init__(graph, affichage, nb_fourmis=nb_fourmis, **kwargs)
        self.nb_processus = nb_processus
        # fourmis réparties équitablement (au moins 1 par processus)
        self.fourmis_par_proc = max(1, self.m // nb_processus)

    def _creer_memoire_partagee(self):
        n = self.n
        self._shms = []

        def partager(tableau):
            shm = shared_memory.SharedMemory(create=True, size=tableau.nbytes)
            vue = np.ndarray(tableau.shape, dtype=np.float64, buffer=shm.buf)
            vue[:] = tableau
            self._shms.append(shm)
            return shm, vue

        shm_D, _ = partager(self.D)
        shm_eb, _ = partager(self.eta_beta)
        shm_tau, vue_tau = partager(self.tau)
        self.tau = vue_tau        # les mises à jour en place sont vues par les workers
        return shm_D.name, shm_eb.name, shm_tau.name

    def _liberer(self):
        self.tau = np.array(self.tau)   # copie hors mémoire partagée avant de la détruire
        for shm in self._shms:
            shm.close()
            shm.unlink()

    def resoudre(self):
        self.affichage.afficher_details = True
        noms = self._creer_memoire_partagee()
        sans_amelioration = 0
        iteration = 0
        pool = mp.Pool(self.nb_processus, initializer=_init_worker,
                       initargs=(*noms, self.n, self.alpha))
        try:
            for iteration in range(1, self.nb_iterations + 1):
                graines = self.rng.integers(0, 2**32 - 1, size=self.nb_processus)
                taches = [(self.fourmis_par_proc, int(g), self.two_opt) for g in graines]

                # ---- PARTIE PARALLÈLE : un lot de fourmis par coeur ----
                resultats = pool.map(_travail_fourmis, taches)

                tour_ib, dist_ib = min(resultats, key=lambda r: r[1])

                if dist_ib < self.meilleure_distance - 1e-9:
                    self.meilleure_distance = dist_ib
                    self.meilleur_tour = tour_ib
                    self.iteration_trouvee = iteration
                    self._maj_bornes()
                    sans_amelioration = 0
                else:
                    sans_amelioration += 1

                # ---- PARTIE SÉQUENTIELLE : mise à jour des phéromones ----
                self.tau *= (1.0 - self.rho)
                ref, d_ref = ((self.meilleur_tour, self.meilleure_distance)
                              if iteration % 5 == 0 else (tour_ib, dist_ib))
                a, b = ref, np.roll(ref, -1)
                depot = 1.0 / d_ref
                self.tau[a, b] += depot
                self.tau[b, a] += depot
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
        solveur = TP_ACO_Parallele(graph=graphe, affichage=affichage,
                                   nb_processus=4, nb_fourmis=32, nb_iterations=300)
        _, meilleure_dist = solveur.resoudre()
        affichage.info_label.config(
            text=f"ACO terminé ! Distance finale : {meilleure_dist:.2f} px (NN : {dist_nn:.2f} px) "
                 f"| [M] : Phéromones | [ESC] : Quitter")

    root.bind('<space>', demarrer_aco)
    root.mainloop()


if __name__ == "__main__":
    mp.freeze_support()     # nécessaire sous Windows
    main()