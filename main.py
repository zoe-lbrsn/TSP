import tkinter as tk
from tsp_graph_init import Graph, Affichage, Route
from TP_ACO import TP_ACO


def construire_route_plus_proche_voisin(graphe: Graph) -> Route:
    """
    Construit une route sur 1 tour avec l'heuristique du Plus Proche Voisin.
    Visite tous les lieux à partir du lieu 0 et revient au lieu 0.
    """
    nb_lieux = len(graphe.liste_lieux)
    visites = {0}
    ordre_nn = [0]
    courant = 0

    # On cherche le plus proche voisin non visité à chaque étape
    while len(visites) < nb_lieux:
        suivant = graphe.plus_proche_voisin(courant, visites)
        ordre_nn.append(suivant)
        visites.add(suivant)
        courant = suivant

    # Retour obligatoire au point de départ (lieu 0)
    ordre_nn.append(0)

    # Instanciation de l'objet Route avec l'ordre calculé
    route = Route(graphe.liste_lieux)
    route.ordre = ordre_nn
    return route


def main():
    root = tk.Tk()

    # 1. Initialisation du Graphe (vide au départ)
    graphe = Graph()
    
    # 2. Chargement du fichier CSV des 20 lieux
    graphe.charger_graph("graph_20.csv")

    # 3. Initialisation de l'affichage Tkinter (Groupe 6)
    affichage = Affichage(root, group_name="6")

    # --- ÉTAPE 1 : Calcul & Affichage du Plus Proche Voisin ---
    route_nn = construire_route_plus_proche_voisin(graphe)
    dist_nn = graphe.calcul_distance_route(route_nn)

    # Affichage du graphe et de la route initiale
    affichage.rafraichir(
        liste_lieux=graphe.liste_lieux,
        meilleure_route_ordre=route_nn.ordre
    )
    affichage.info_label.config(
        text=f"[Plus Proche Voisin] Distance : {dist_nn:.2f} px | Appuie sur [ESPACE] pour lancer ACO"
    )

    # --- ÉTAPE 2 : Déclenchement de l'ACO via la touche ESPACE ---
    def démarrer_aco(event=None):
        # On désactive la touche espace pour éviter de relancer l'algorithme pendant qu'il tourne
        root.unbind('<space>')
        
        # Activer le tracé des phéromones
        affichage.afficher_details = True

        # Création et lancement du solveur ACO
        solveur_aco = TP_ACO(
            graph=graphe,
            affichage=affichage,
            nb_fourmis=len(graphe.liste_lieux),  # 20 fourmis
            nb_iterations=200,
            pause=0.03
        )
        
        meilleur_ordre, meilleure_dist = solveur_aco.resoudre()

        # Message de fin
        affichage.info_label.config(
            text=f"ACO Terminé ! Distance finale : {meilleure_dist:.2f} px (NN : {dist_nn:.2f} px) | Touche [M] : Phéromones | [ESC] : Quitter"
        )

    # Associe la touche ESPACE au lancement de l'ACO
    root.bind('<space>', démarrer_aco)

    # Lancement de la boucle événementielle Tkinter
    root.mainloop()


if __name__ == "__main__":
    main()