class LIEU:
    def __init__(self, x, y, name):

        self.x = x
        self.y = y
        self.name = name

    def distance(self, autre_lieu):
        return (self.x - autre_lieu.x, self.y - autre_lieu.y)


import tkinter as tk
HAUTEUR = 600
LARGEUR = 800

class Affichage:
    def __init__(self, master, group_name="6"):
        self.master = master
        self.master.title(f"TSP - Groupe {group_name}")

        self.canvas = tk.Canvas(self.master, width=LARGEUR, height=HAUTEUR, bg='white')
        self.canvas.pack()

        self.info_label = tk.Label(
            self.master,
            text='Initialisation du graphe du TSP',
            font=('Arial', 12)
            fg='black'
        )
        self.info_label.pack()

        self.afficher_details = False

        self.master.bind('<g>', self.best_routes) #'g' pour gris clair (c'est évident)
        self.master.bind('<m>', self.pheromones) #'m' pour matrice (espèce de bouffon)
    

    def quitter(self, event=None):
        self.master.destroy() #ferme l'interface graphique complètement
        self.master.quit() #arrête la boucle principale de tkinter
    
    def pheromones(self, event=None):
        #affiche ou désaffiche les détails des phéromones sur le graphe
        self.affichage_details = not self.affichage_details
        print("bascule affichage des détails des phéromones:", self.affichage_details) #faudra relancer un canva dans le main

    def mettre_a_jour_texte(self, iteration, best_distance, infos_supplementaire="")
        #mettre à jour le texte en bas de la fenêtre
        texte = f"Iteration: {iteration} | Meilleure distance: {best_distance:.2f} | {infos_supplementaire}"
        self.info_label.config(text=texte)
    
    def dessiner_lieux(self, liste_lieux):
        