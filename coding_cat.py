import turtle

# Configuration de la fenêtre
screen = turtle.Screen()
screen.setup(600, 700)
screen.title("Mon Chat en Python")

t = turtle.Turtle()
t.speed(9)

# COULEURS
couleur_chat = "#FFA500"      # Orange
couleur_oreilles = "#FF8C00"  # Orange foncé
couleur_nez = "#FFC0CB"       # Rose

# ==========================================
# 1. LA QUEUE DÉTOURÉE (Dessinée avec contour noir)
# ==========================================
t.penup()
t.goto(60, -150)
t.setheading(40)
t.pendown()
t.fillcolor(couleur_chat)
t.begin_fill()
# On trace la queue en forme de croissant pour pouvoir la remplir et la détourer
t.circle(60, 90)
t.circle(10, 180)
t.circle(-50, 90)
t.end_fill()

# ==========================================
# 2. LE CORPS (Grand cercle orange)
# ==========================================
t.penup()
t.goto(0, -180)
t.pendown()
t.fillcolor(couleur_chat)
t.begin_fill()
t.setheading(0)
t.circle(75)
t.end_fill()

# ==========================================
# 3. LES PATTES ARRIÈRE (Les pieds sur les côtés)
# ==========================================
def dessiner_pied_arriere(x, y, orientation):
    t.penup()
    t.goto(x, y)
    t.setheading(orientation)
    t.pendown()
    t.fillcolor(couleur_oreilles)
    t.begin_fill()
    t.circle(18, 180) # Petit dôme arrondi pour le pied au sol
    t.left(90)
    t.forward(36)
    t.end_fill()

# Pied gauche et pied droit à la base du corps
dessiner_pied_arriere(-75, -160, 90)
dessiner_pied_arriere(40, -160, 90)

# ==========================================
# 4. LES PATTES AVANT
# ==========================================
def dessiner_patte_avant(x, y):
    t.penup()
    t.goto(x, y)
    t.setheading(-90)
    t.pendown()
    t.fillcolor(couleur_oreilles)
    t.begin_fill()
    t.forward(60)
    t.circle(12, 180)
    t.forward(60)
    t.end_fill()

dessiner_patte_avant(-30, -90)
dessiner_patte_avant(5, -90)

# ==========================================
# 5. LA TÊTE
# ==========================================
t.penup()
t.goto(0, -45)
t.pendown()
t.fillcolor(couleur_chat)
t.begin_fill()
t.setheading(0)
t.circle(75)
t.end_fill()

# ==========================================
# 6. LES OREILLES
# ==========================================
# Oreille Gauche
t.penup()
t.goto(-55, 60)
t.setheading(120)
t.pendown()
t.fillcolor(couleur_oreilles)
t.begin_fill()
t.forward(45)
t.right(140)
t.forward(47)
t.end_fill()

# Oreille Droite
t.penup()
t.goto(55, 60)
t.setheading(60)
t.pendown()
t.fillcolor(couleur_oreilles)
t.begin_fill()
t.forward(45)
t.left(140)
t.forward(47)
t.end_fill()

# ==========================================
# 7. LES YEUX
# ==========================================
def dessiner_oeil(x, y):
    t.penup()
    t.goto(x, y)
    t.setheading(0)
    t.pendown()
    t.fillcolor("white")
    t.begin_fill()
    t.circle(14)
    t.end_fill()
    
    t.penup()
    t.goto(x, y + 6)
    t.pendown()
    t.fillcolor("black")
    t.begin_fill()
    t.circle(6)
    t.end_fill()

dessiner_oeil(-28, 30)
dessiner_oeil(28, 30)

# ==========================================
# 8. LE NEZ & LE SOURIRE CORRIGÉ (Style 'w' mignon)
# ==========================================
# Nez rose
t.penup()
t.goto(-8, 15)
t.setheading(0)
t.pendown()
t.fillcolor(couleur_nez)
t.begin_fill()
for _ in range(3):
    t.forward(16)
    t.right(120)
t.end_fill()

# Petite ligne verticale sous le nez
t.penup()
t.goto(0, 1)
t.setheading(-90)
t.pendown()
t.forward(8)

# Babine gauche (arc de cercle propre)
t.setheading(180)
t.circle(7, -180)

# Babine droite (arc de cercle propre)
t.penup()
t.goto(0, -7)
t.setheading(0)
t.pendown()
t.circle(7, 180)

# ==========================================
# 9. LES MOUSTACHES
# ==========================================
def trace_moustache(x, y, angle):
    t.penup()
    t.goto(x, y)
    t.setheading(angle)
    t.pendown()
    t.forward(35)

t.pensize(2)
# Gauches
trace_moustache(-15, 3, 165)
trace_moustache(-15, -1, 180)
trace_moustache(-15, -5, 195)
# Droites
trace_moustache(15, 3, 15)
trace_moustache(15, -1, 0)
trace_moustache(15, -5, -15)

t.hideturtle()
turtle.done()
