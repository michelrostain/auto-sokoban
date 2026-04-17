from collections import deque
import heapq

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


historique = []

## Accès à la matrice : matrice [y][x], à  savoir ligne puis colonne.

matrice = [[-1, -1, -1, -1, -1, -1, -1, -1],
           [-1,  0,  0,  0,  0,  0,  0, -1],
           [-1,  0,  0,  3,  0,  0,  0, -1],
           [-1,  0,  0,  0,  0,  1,  0, -1],
           [-1,  0,  2,  0,  0,  0,  0, -1],
           [-1,  0,  0,  0,  0,  2,  0, -1],
           [-1,  0,  0,  1,  0,  0,  0, -1],
           [-1, -1, -1, -1, -1, -1, -1, -1]]


NIVEAUX = {
    1: [[-1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  0,  3,  0,  0,  0, -1],
        [-1,  0,  0,  0,  0,  1,  0, -1],
        [-1,  0,  2,  0,  0,  0,  0, -1],
        [-1,  0,  0,  0,  0,  2,  0, -1],
        [-1,  0,  0,  1,  0,  0,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1]],

    2: [[-1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  2,  0,  0,  0,  0, -1],
        [-1,  0,  0, -1, -1,  0,  0, -1],
        [-1,  0,  0,  3,  0,  0,  0, -1],
        [-1,  0,  0, -1,  0,  2,  0, -1],
        [-1,  0,  1,  0,  0,  1,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1]],

    3: [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  2,  0, -1,  0,  2,  0, -1],
        [-1,  0,  0,  0, -1,  0,  0,  0, -1],
        [-1,  0,  0,  3,  0,  0,  0,  0, -1],
        [-1,  0,  0,  0, -1,  0,  2,  0, -1],
        [-1,  0,  1,  0, -1,  0,  1,  0, -1],
        [-1,  0,  0,  0,  0,  0,  1,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1]],

    4: [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  2,  0, -1,  0,  2,  0, -1],
        [-1,  0,  0,  0, -1,  0,  0,  0, -1],
        [-1,  0,  2,  0,  3,  0,  2,  0, -1],
        [-1,  0,  0, -1, -1, -1,  0,  0, -1],
        [-1,  0,  1,  0,  0,  0,  1,  0, -1],
        [-1,  0,  0,  0,  1,  0,  1,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1]],

    5: [[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  0,  1,  0,  0,  1,  0,  0, -1],
        [-1,  0,  2,  0, -1, -1,  0,  2,  0, -1],
        [-1,  0,  0,  0, -1,  0,  0,  0,  0, -1],
        [-1,  0, -1,  2,  0,  0,  2, -1,  0, -1],
        [-1,  0,  0,  0,  3,  0,  0,  0,  0, -1],
        [-1,  0, -1,  2,  0,  0,  2, -1,  0, -1],
        [-1,  0,  1,  0,  1,  0,  1,  0,  1, -1],
        [-1,  0,  0,  0,  0,  0,  0,  0,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]],
}

def charger_niveau(numero):
    return NIVEAUX[numero]

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
    
    return voisins


def est_gagne(etat, matrice):
    
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
        if matrice[ny][nx] == CAISSE_SUR_CIBLE:
                matrice[ny][nx] = CIBLE
        else:
            matrice[ny][nx] = SOL
            
    if matrice[jy][jx] == JOUEUR_SUR_CIBLE:
        matrice[jy][jx] = CIBLE 
    else :
        matrice[jy][jx] = SOL

    if matrice[ny][nx] == CIBLE:
        matrice[ny][nx] = JOUEUR_SUR_CIBLE
    else :
        matrice[ny][nx] = JOUEUR

def mouvement_valide(matrice, direction):
    # Récupérer position joueur depuis la matrice
    position_joueur, positions_caisses = get_etat(matrice)
    jx, jy = position_joueur
    # Calculer la case visée avec direction
    dx, dy = direction

    nx, ny = jx+dx, jy+dy
    if matrice[ny][nx] == MUR: 
        return False
    
    # Cette notation reviens à écrire : if matrice[ny][nx] == CAISSE or matrice[ny][nx] == CAISSE_SUR_CIBLE:
    if matrice[ny][nx] in (CAISSE, CAISSE_SUR_CIBLE):
        cx, cy = nx+dx, ny+dy
        if matrice[cy][cx] == MUR or (cx, cy) in positions_caisses:
            return False # Caisse bloquée, mouvement impossible
        
    return True

def annuler_mouvement(historique):
    if len(historique) > 0 : # On pourrait marquer juste : if historique
        return historique.pop()


#### Les algorithmes

def heuristique(etat, matrice):
    """
    Somme des distances de Manhattan de chaque caisse
    vers la cible la plus proche.
    """
    _, positions_caisses = etat
    
    # Extraire les positions des cibles depuis la matrice
    positions_cibles = set()
    for y in range(len(matrice)):
        for x in range(len(matrice[y])):
            if matrice[y][x] == CIBLE:
                positions_cibles.add((x, y))
    
    total = 0
    for (cx, cy) in positions_caisses:
        # Distance de Manhattan vers la cible la plus proche
        distance_min = min(
            abs(cx - tx) + abs(cy - ty)
            for (tx, ty) in positions_cibles
        )
        total += distance_min
    
    return total

def reconstruire_chemin(prev, etat_final):
    """
    Remonte le dictionnaire prev depuis l'état final
    jusqu'à l'état initial.
    """
    chemin = []
    etat = etat_final
    
    while etat is not None:
        chemin.append(etat)
        etat = prev.get(etat)  # remonte d'un cran
    
    chemin.reverse()  # on remet dans l'ordre chronologique
    return chemin

def solveur(matrice, mode='BFS', stop_flag=None):
    etat_initial = get_etat(matrice)
    prev = {etat_initial: None}

    if mode == 'Astar':
        file_ou_pile = [(0, etat_initial)]
        h0 = heuristique(etat_initial, matrice)
        exploration_log = [(etat_initial, None, h0)]
    else:
        file_ou_pile = [etat_initial]
        exploration_log = [(etat_initial, None)]

    visites = {etat_initial}
    etapes = 0

    while file_ou_pile:
        etapes += 1

        if stop_flag is not None and etapes % 500 == 0 and stop_flag():
            return None, etapes, len(visites), exploration_log

        if mode == 'BFS':
            actuel = file_ou_pile.pop(0)
        elif mode == 'DFS':
            actuel = file_ou_pile.pop()
        elif mode == 'Astar':
            priorite, actuel = heapq.heappop(file_ou_pile)

        if est_gagne(actuel, matrice):
            return reconstruire_chemin(prev, actuel), etapes, len(visites), exploration_log

        for voisin in get_voisins(actuel, matrice):
            if voisin not in visites:
                visites.add(voisin)
                prev[voisin] = actuel
                if mode == 'Astar':
                    h = heuristique(voisin, matrice)
                    f_score = etapes + h
                    heapq.heappush(file_ou_pile, (f_score, voisin))
                    exploration_log.append((voisin, actuel, h))
                else:
                    file_ou_pile.append(voisin)
                    exploration_log.append((voisin, actuel))

    return None, etapes, len(visites), exploration_log