import time
import tkinter as tk

from tsp_graph_init import Graph, Route, Affichage
from TP_ACO import TP_ACO

if __name__ == "__main__":
    root = tk.Tk()

    # 1. Graphe chargé depuis le CSV
    graphe = Graph(liste_lieux=[])
    graphe.charger_graph("graph_30.csv")

    # 2. Fenêtre d'affichage
    affichage = Affichage(root)

    # 3. Algorithme de colonie de fourmis
    aco = TP_ACO(graphe, affichage, nb_iterations=100, rho=0.3)

    # 4. Affichage de la solution du plus proche voisin
    aco.initialiser_plus_proche_voisin()

    # 5. Attente de l'appui sur la touche M
    try:
        while not affichage.fourmis_lancees:
            root.update()
            time.sleep(0.05)
    except tk.TclError:
        raise SystemExit  # fenêtre fermée avant le lancement

    # 6. Lancement des fourmis
    meilleure_route, meilleure_distance = aco.resoudre()

    print("Meilleure route :", meilleure_route.ordre)
    print("Distance :", meilleure_distance)

    try:
        root.mainloop()
    except tk.TclError:
        pass