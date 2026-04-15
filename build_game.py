MUR     = -1
SOL     =  0
CIBLE   =  1
CAISSE  =  2
JOUEUR  =  3
CAISSE_SUR_CIBLE  =  4
JOUEUR_SUR_CIBLE  =  5

## Directions sur la matrice
HAUT   = ( 0, -1)  # y diminue
BAS    = ( 0,  1)  # y augmente
GAUCHE = (-1,  0)  # x diminue
DROITE = ( 1,  0)  # x augmente

## Accès à la matrice : matrice [y][x], à  savoir ligne puis colonne.

matrice = [[-1, -1, -1, -1, -1, -1, -1, -1],
           [-1,  0,  0,  0,  0,  0,  0, -1],
           [-1,  0,  0,  3,  0,  0,  0, -1],
           [-1,  0,  0,  0,  0,  1,  0, -1],
           [-1,  0,  2,  0,  0,  0,  0, -1],
           [-1,  0,  0,  0,  0,  2,  0, -1],
           [-1,  0,  0,  1,  0,  0,  0, -1],
           [-1, -1, -1, -1, -1, -1, -1, -1]]

def get_etat(matrice):
    position_joueur = None
    positions_caisses = []

    for y in range(len(matrice)): # Parcourt les lignes
        for x in range(len(matrice[y])) : # Parcourt les colonnes
            
            valeur = matrice[y][x]

            if valeur == JOUEUR or valeur == JOUEUR_SUR_CIBLE :
                position_joueur=(x,y)

            elif valeur == CAISSE or valeur == CAISSE_SUR_CIBLE :
                positions_caisses.append((x,y))

    return (position_joueur, frozenset(positions_caisses))

# Vérification fonctionnement 
# 

def get_voisins(etat, matrice):
    # Création de la liste qui contiendra les tuples des positions de voisins
    voisins = []
    position_joueur, positions_caisses = etat
    jx, jy = position_joueur

    for dx, dy in [HAUT, BAS, GAUCHE, DROITE]:
        nx, ny = jx + dx, jy + dy # case où le joueur veux aller, car est ajouté à sa position les valeurs issues de la manipulation des touches de direction
        
        if matrice[ny][nx] == MUR:
            continue

        nouvelles_caisses = set(positions_caisses)

        if (nx, ny) in positions_caisses:
            # On tente de pousser une caisse
            cx, cy = nx+dx, ny+dy # Nouvelle position de la caisse
            if matrice[cy][cx] == MUR or (cx, cy) in positions_caisses:
                continue # Caisse bloquée, mouvement impossible
            # On supprime l'ancienne position
            nouvelles_caisses.remove((nx, ny))
            # On ajoute la nouvelle
            nouvelles_caisses.add((cx, cy))

        nouvel_etat = ((nx, ny)), frozenset(nouvelles_caisses)
        voisins.append(nouvel_etat)


def est_gagne(etat):
    
    positions_caisses = etat[1]
    positions_cibles = set()

    for y in range(len(matrice)): # Parcourt les lignes
        for x in range(len(matrice[y])) : # Parcourt les colonnes
            valeur = matrice[y][x]

            if valeur == CIBLE :
                positions_cibles.add((x, y))
    
    return positions_caisses == positions_cibles


def deplacer_joueur(matrice, direction):
    # Récupérer position joueur depuis la matrice
    position_joueur, positions_caisses = get_etat(matrice)
    jx, jy = position_joueur
    # Calculer la case visée avec direction
    dx, dy = direction

    nx, ny = jx+dx, jy+dy
    if matrice[ny][nx] == MUR: 
        return
    
    # Cette notation reviens à écrire : if matrice[ny][nx] == CAISSE or matrice[ny][nx] == CAISSE_SUR_CIBLE:
    if matrice[ny][nx] in (CAISSE, CAISSE_SUR_CIBLE):
        cx, cy = nx+dx, ny+dy
        if matrice[cy][cx] == MUR or (cx, cy) in positions_caisses:
            return # Caisse bloquée, mouvement impossible
        
        if matrice[cy][cx] == CIBLE:
            matrice[cy][cx] = CAISSE_SUR_CIBLE
        else :
            matrice[cy][cx] = CAISSE

    if matrice[jy][jx] == JOUEUR_SUR_CIBLE:
        matrice[jy][jx] = CIBLE 
    else :
        matrice[jy][jx] = SOL

    if matrice[ny][nx] == CIBLE:
        matrice[ny][nx] = JOUEUR_SUR_CIBLE
    else :
        matrice[ny][nx] = JOUEUR