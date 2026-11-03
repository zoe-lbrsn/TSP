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
        #dessine les lieux en forme de cercle avec leur numéro au centre
        rayon=15
        for index, lieu in enumerate(liste_lieux):
            x, y = lieu.x, lieu.y

            #cercle qui représente le lieu
            self.canvas.create_oval(
                x - rayon, y - rayon, x + rayon, y + rayon,
                fill='lightpurple',
                outline='black'
            )

            #numéro du lieu au centre du cercle
            self.canvas.create_text(
                x, y,
                text=str(index),
                font=('Arial', 10, 'bold')
            )
    
    def dessiner_meilleure_route(self, route_ordre, liste_lieux):
        #dessine la meilleure route trouvée par l'algorithme et indique l'ordre des lieux visités
        if not route_ordre or len(route_ordre) < 2:
            return
        
        for i in range(len(route_ordre) - 1):
            index_lieu1 = route_ordre[i]
            index_lieu2 = route_ordre[i + 1]

            l1 = liste_lieux[index_lieu1]
            l2 = liste_lieux[index_lieu2]

            #ligne pointillée
            self.canvas.create_line(
                l1.x, l1.y, l2.x, l2.y,
                fill='purple',
                width=2,
                dash=(4, 2)  # ligne pointillée
            )

            #ordre de visite indiquée au dessus du lieu
            #attention, pas besoi pour le dernier point qui boucle sur le départ
            if i < len(route_ordre) - 1:
                self.canvas.create_text(
                    l1.x, l1.y -25,
                    text=f"Ordre: {i}", fill="blue", font=('Arial', 9)
                )
    
    
    def dessiner_pheromones(self, matrice_pheromones, liste_lieux, seuil = 0.1):
        #dessine la matrice des phéromones sous forme de lignes grises
        #L'épaisseur ou l'apparition de la ligne dépend de l'intensité des phéromones

        nb_lieux = len(liste_lieux)

        for i in range(nb_lieux):
            for j in range(i+1, nb_lieux): #pour éviter de dessiner en double
                niveau_pheromone = matrice_pheromones[i][j]

                #N'affiche que les pistes avec suffisemment de phéromones
                if niveau_pheromone > seuil:
                    l1 = liste_lieux[i]
                    l2 = liste_lieux[j]

                    #Plus il y a de phéromones, plus la ligne est épaisse
                    epaisseur = min(5, max(1, niveau_pheromone * 100))  # Limite l'épaisseur à 5
                    self.canvas.create_line(
                        l1.x, l1.y, l2.x, l2.y,
                        fill='lightgray',
                        width=epaisseur
                    )

    
    def rafraichir(self, liste_lieux, meilleure_route_ordre=None, matrice_pheromones=None):
        #Méthode qu'on appelle pour tout redessiner

        #on efface tout le canvas
        self.canvas.delete("all")

        #on dessine les phéromones en arrière-plan si la touche "m" a été pressée
        if self.affichage_details and matrice_pheromones is not None:
            self.dessiner_pheromones(matrice_pheromones, liste_lieux)
        
        #on dessine la route par dessus
        if meilleure_route_ordre is not None:
            self.dessiner_meilleure_route(meilleure_route_ordre, liste_lieux)
        
        #on dessine les lieux par dessus
        self.dessiner_lieux(liste_lieux)

        #on met à jour 
        self.master.update()
        