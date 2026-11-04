if __name__ == "__main__":

    # Import des classes depuis ton fichier d'origine
    from tsp_graph_init import Graph, Affichage, Route

    import tkinter as tk
    
    root = tk.Tk()
    
    # 1. Création d'un graphe vide (on force liste_lieux=[] pour éviter la génération aléatoire)
    graphe_test = Graph(liste_lieux=[]) 
    
    # 2. Chargement des données depuis votre fichier CSV
    graphe_test.charger_graph("graph_20.csv")
    
    # 3. Initialisation de l'affichage
    affichage_test = Affichage(root)
    
    # 4. Création d'une route aléatoire basée sur les lieux du CSV et affichage
    route_aleatoire = Route(graphe_test.liste_lieux)
    affichage_test.rafraichir(graphe_test.liste_lieux, route_aleatoire.ordre)
    
    root.mainloop()