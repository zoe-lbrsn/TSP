"""if __name__ == "__main__":

    # Import des classes depuis ton fichier d'origine
    from tsp_graph_init import Graph, Affichage, Route

    import tkinter as tk
    
    root = tk.Tk()
    
    # 1. Création d'un graphe vide (on force liste_lieux=[] pour éviter la génération aléatoire)
    graphe_test = Graph(liste_lieux=[]) 
    
    # 2. Chargement des données depuis votre fichier CSV
    graphe_test.charger_graph("graph_5.csv")
    
    # 3. Initialisation de l'affichage
    affichage_test = Affichage(root)
    
    # 4. Création d'une route aléatoire basée sur les lieux du CSV et affichage
    route_aleatoire = Route(graphe_test.liste_lieux)
    affichage_test.rafraichir(graphe_test.liste_lieux, route_aleatoire.ordre)
    
    root.mainloop()
"""

    # main.py

# Import the necessary classes
from TP_ACO import TSP_ACO
from tsp_graph_init import Graph, Affichage, Route
import tkinter as tk

# Create a graph
graph = Graph()

# Load the graph data from a CSV file
graph.charger_graph("graph_5.csv")

# Create an instance of the TSP_ACO class
tsp_aco = TSP_ACO(graph, Affichage(tk.Tk()), nb_fourmis=10)

# Run the TSP_ACO algorithm 
tsp_aco.run()

# Create an instance of the Affichage class
affichage = Affichage(tk.Tk())

# Create a random route based on the graph and display it
route_aleatoire = Route(graph.liste_lieux)
affichage.rafraichir(graph.liste_lieux, route_aleatoire.ordre)

# Run the tkinter main loop
tk.mainloop()