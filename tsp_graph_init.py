import random  # bibli pour générer des nombres aléatoires

class Route: # classe route qui représente un chemin dans le problème du voyageur de commerce avec un ordre de passage par les lieux
    def __init__(self, liste_lieux): # initialisation de la classe Route avec une liste de lieux
        self.ordre = list(range(1, len(liste_lieux))) # création d'une liste d'indices représentant les lieux à visiter (sauf le point de départ et d'arrivée)

        random.shuffle(self.ordre) # mélanger aléatoirement l'ordre des lieux à visiter

        self.ordre.insert(0,0) # insérer le point de départ (indice 0) au début de la liste des lieux à visiter
        self.ordre.append(0) # insérer le point d'arrivée (indice 0) à la fin de la liste des lieux à visiter

