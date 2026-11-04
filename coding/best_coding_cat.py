import numpy as np
import matplotlib.pyplot as plt

# Palette de couleurs au format Hexadécimal standard
PALETTE_HEX = {
    '.': "#1e1e2e",     # Fond bleu nuit
    'T': "#4a2c11",     # Table en bois
    'P': "#6c7086",     # PC portable (Gris)
    'E': "#11111b",     # Intérieur écran (Noir)
    'C': "#313244",     # Pelage du chat (Gris foncé)
    'W': "#cdd6f4",     # Pattes/Détails (Blanc cassé)
    'G': "#a6e3a1",     # Code (Vert Matrix)
    'R': "#f38ba8"      # Intérieur oreilles (Rose)
}

# La grille 24x24 du dessin
GRILLE_DESSIN = [
    "........................",
    "........................",
    "........................",
    "........R....R..........",
    ".......CCC..CCC.........",
    ".......CCCCCCCC...PPPPPP",
    ".......CCCCCCCC...PEEEEP",
    ".......C.C..C.C...PEGEEP",
    ".......CCCCCCCC...PEEEEP",
    "........CCCCCC....PPPPPP",
    ".......CCCCCCCC...P.....",
    "......CCCCCCCCCC.P......",
    "......CCCCCCCCCCPPPPPPPP",
    "......CCCCCCCCCCWWWWWWWP",
    "......CCCCCCCCCC.PPPPPPP",
    "......CCCCCCCCCC........",
    ".....CCCCCCCCCCCC.......",
    "....CCCCCCCCCCCCCC......",
    "....CCCCWWWWWWCCCC......",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTT"
]

def hex_to_rgb(hex_str):
    """Convertit une chaîne hexadécimale '#RRGGBB' en liste [R, G, B]"""
    h = hex_str.lstrip('#')
    return [int(h[i:i+2], 16) for i in (0, 2, 4)]

def main():
    hauteur = len(GRILLE_DESSIN)
    largeur = len(GRILLE_DESSIN[0])
    
    # Création d'une image vide aux bonnes dimensions
    image_rgb = np.zeros((hauteur, largeur, 3), dtype=np.uint8)

    # Remplissage de la matrice pixel par pixel
    for y in range(hauteur):
        for x in range(largeur):
            caractere = GRILLE_DESSIN[y][x]
            couleur_hex = PALETTE_HEX[caractere]
            image_rgb[y, x] = hex_to_rgb(couleur_hex)

    # Rendu graphique avec Matplotlib
    plt.figure(figsize=(7, 7), facecolor='#1e1e2e')
    plt.imshow(image_rgb, interpolation='nearest')
    
    # Nettoyage des bordures pour ne laisser que le dessin
    plt.axis('off')
    plt.title("Le Chat Développeur (Pixel Art 8-bit)", color='white', fontsize=12, pad=10)
    
    print("🐾 Génération du pixel art réussie !")
    plt.show()

if __name__ == "__main__":
    main()
