# Algorithme de résolution de labyrinthe
### Les différents algorithmes
**BFS :**    
Technique de parcours de graphe qui agit par couches. On commence à explorer un noeud, puis ses successeurs, puis les successeurs de ses successeurs. Permet de calculer les distances de tous les noeuds depuis un noeud source dans un graphe non-pondéré, orienté ou non orienté. 

**DFS :**    
Technique de parcours de graphe qui explore un chemin dans un graphe jusqu'àun cul de sac ou un sommet déjà vsité. Il reviens alors au dernier sommet où on pouvait explorer un eutre chemin et explore une autre chemin. La récursivité est effective avec la mise en mémoire des noeuds où on a dû faire un choix.   
   
**A* :**   
Technique de parcours de graphe qui combine le coût réel parcouru (g) et une estimation de la distance restante jusqu'à l'arrivée (h), appelée heuristique. A* choisit à chaque étape le nœud dont la somme f = g + h est la plus faible. L'heuristique peut être la distance euclidienne, de Manhattan, ou toute autre estimation qui ne surestime jamais la distance réelle. Sans heuristique (h=0), A* explore par coût croissant sans orientation préférentielle.

### Le coût   
   
Soit V le nombre de sommets (états du graphe), et E le nombre d'arrêtes (transitions valides entre états).   

**BFS :**   
Complexité temporelle O(V + E) : chaque sommet et chaque arrêtes sont explorées une seule fois.   
Complexité spatiale : tous les états d'un niveaux sont mis en mémoire.   
Garantie : solution optimale (la plus courte) toujours trouvée.   

**DFS :**   
Complexité temporelle O(V + E) ; chaque sommet et chaque arrête d'un chemin est exploré une fois.

Complexité spatiale : très faible, DFS ne stocke qu'un seul chemin à la fois.

Garantie : aucune. Peut trouver une chamin très long ou s'enfoncer très loin avant de trouver   
   
**Astar :**   

COmplexité : O(V log V)

Coût : explore en priorité les états dont le score f=g+h est lke plus faible.   
- G = coût réel depuis l'état inital   
- H = estimation heuristique du coût restant   

La file de priorité est maintenue  rangée grâce à heapq, qui maintient en haut de la liste le score le plus faible de la distance de manhattan.

Garantie : solution optimale si l'heuristique est admissible, c'est a dire si elle ne surestime jamais le coût réel. La distance de Manhattan est admissible car elle ignore les obstacles et sous estime toujours.
  
**Une bonne approximation rapide vaut mieux qu'une réponse exacte trop couteuse à obtenir**   

**La distance de Manhattan :**   
C'est l'heuristique qui correspond à la géométrie réelle des déplacements. Vu qu'il n'y a pas de possibilité de se déplacer en diagonale, la distance Euclidienne sous estimerai trop la  distance vers les cibles et serai trop loin d'une "bonne approximation".


### Le sokoban : un graphe en mouvement    
Dans le cas du Sokoban, un nouveau graphe est créé à chaque coups. On ne construit pas de graphe de cases comme dans un labyrinthe, on construit un graphe d'état. Dans ce contexte, les sommets sont des états complets du jeu et les arrêtes des coups valides.

## Les définitions des différentes fonctions du code : 

**def get_etat :**    
C'est une fonction qui photographie l'état du jeu et le garde en mémoire sous la forme d'un tuple. Cette représentation sert d'identifiant unique pour un sommet du  graphe d'état. Sert à vérifier siun sommet a déjà été visité, évitant ainsi les boucles infinies. L'utilisation d'in tuple est fondamental car il est immuable : cela repose sur le contrat "ne recherche pas où tu as déjà cherché".


**def get_voisins :**   
Détermine, depuis un état donné, quels sont les états accessibles en 1 coup valide. Ces états constituent les arrêtes et les sommets que l'algo ajoutera localement au graphe qu'il construit au fur et à mesure. Cette fonction est destinée à l'algorithme BFS pour la recherche de solution.

**def deplacer_joueur :**    
Permet au joueur de se déplacer, avec la même logique que get_voisin pour les conditions de déplacement (murs, caisses bloquées) : Récupère la position du joueur depuis la matrice, calcule la case visée.   
Si mur → abandon.   
Si caisse → vérifie si elle peut bouger, la déplace dans la matrice.  
Efface l'ancienne position du joueur (CIBLE ou SOL).  
Place le joueur à sa nouvelle position (JOUEUR_SUR_CIBLE ou JOUEUR).

**def est_gagne :**    
Permet de comparer les positions de cibles et des caisses. Si celkles ci sont identiques alors c'est gagné.

**def mouvement_valide :**    
Permet de définir les mouvement autorisés du jeu

**def annuler_mouvement :**   
Permet de revenir en arrière pour le joueur

**Def heuristique :**    
Détermine les cibles à atteindre dans le jeu pour kles algos de résolution. Référence pour le calcul de la distance de Manhattan.

**Def reconstruire chemin :**    
Permet de refaire le chemin pour l'affichage de la résolution dans pygame

**Def solveur :**    
FOnction qui regroupe les trois algorithmes mis en oeuvres.


---

## Visualisation de l'arbre de recherche

Après la résolution (ou après un arrêt manuel), le bouton **"Voir la résolution de graphe"** ouvre une fenêtre dédiée qui anime l'arbre de recherche nœud par nœud.

### Structure commune (les 3 algos)

La zone gauche affiche l'arbre de recherche :
- Chaque **point** = un état du jeu (position du joueur + positions des caisses)
- Les **lignes grises** entre points = arêtes parent→enfant (quel état a engendré quel autre)
- La **racine** est en haut, ses enfants en dessous, à raison de 20px par niveau de profondeur
- Le nœud **blanc avec halo violet** = le nœud actuellement découvert dans le replay
- Les nœuds de la **solution** (si trouvée) sont en **vert**
- La molette de la souris permet de **scroller** si l'arbre déborde vers le bas

### BFS (Breadth-First Search)

L'arbre s'élargit **horizontalement** par vagues. Le niveau 1 = tous les voisins de la racine, le niveau 2 = tous leurs enfants, etc. Tous les nœuds découverts sont **violets** — BFS n'a pas de notion de "chemin mort", il explore tout par couches. La structure est très **large et plate** : BFS garantit le chemin le plus court, donc il trouve souvent la solution à une profondeur assez faible, mais explore énormément de nœuds sur les premiers niveaux.

Ce qui est intéressant à observer : la symétrie horizontale à chaque niveau — BFS traite les états "équitablement", sans préférence.

### DFS (Depth-First Search)

La **chaîne racine → nœud courant** est en **violet** : c'est le chemin actif que DFS explore en ce moment. Les branches **abandonnées** (backtrackées) deviennent **grises foncées** — DFS est allé jusqu'au bout, n'a pas trouvé, et est remonté. L'arbre est souvent **très profond et fin** : DFS plonge à fond avant d'explorer en largeur.

Ce qui est intéressant à observer : on voit clairement les "tentatives" — chaque branche grise est un couloir sans issue que DFS a complètement exploré. Sur un niveau difficile, il peut y avoir des centaines de branches grises avant de trouver (ou d'être arrêté). C'est la raison pour laquelle DFS est lent sur certains niveaux.

### A* (A-Star)

Les nœuds ont une **couleur en dégradé bleu → rouge** :
- **Bleu** = h_score élevé (les caisses sont loin des cibles, état peu prometteur)
- **Rouge** = h_score proche de 0 (les caisses sont proches des cibles, état prioritaire)

La structure de l'arbre est **moins uniforme** que BFS : A* ne développe pas les couches de façon homogène, il suit les états les plus prometteurs en priorité.

Au **survol d'un nœud** (hover), une mini-grille apparaît montrant la position du joueur et des caisses. Pour A*, des **lignes vertes** relient chaque caisse à sa cible la plus proche avec la **distance de Manhattan annotée** — c'est exactement la valeur h qu'A* a utilisée pour prioriser cet état.

### Résumé comparatif

| | BFS | DFS | A* |
|---|---|---|---|
| Couleur des nœuds | Violet uniforme | Violet (actif) / Gris (backtrack) | Bleu→Rouge selon h_score |
| Forme de l'arbre | Large et plat | Profond et fin | Irrégulier, suit les priorités |
| Ce qu'on voit progresser | Les vagues horizontales | La plongée + les remontées | Les pistes prometteuses rouges |
| Hover | Mini-grille | Mini-grille | Mini-grille + lignes Manhattan |

### Légende des couleurs des nœuds

**Commun à tous les algos :**

| Couleur | Signification |
|---|---|
| Blanc + halo violet | Nœud courant du replay (le dernier découvert affiché) |
| Vert | Nœud appartenant au chemin solution |

**BFS :**

| Couleur | Signification |
|---|---|
| Violet | Tous les nœuds découverts |

**DFS :**

| Couleur | Signification |
|---|---|
| Violet | Chemin actif (racine → nœud courant) |
| Gris foncé | Branches abandonnées (backtrack) |

**Astar :**

| Couleur | Signification |
|---|---|
| Bleu | h_score élevé → caisses loin des cibles (mauvais état) |
| Rouge | h_score faible → caisses proches des cibles (état prioritaire) |
| Intermédiaire | Dégradé continu bleu→rouge selon h / h_max |   


---
## Axes d'amélioration   

**Amélioration de l'algorithme Astar :**   
Il serait oertinent dans le contexte du SOKODAN d'ajouter la prise en compte de sobsatcles dans le calcul du coût. Ainsi l'heuristique deviendrai inadmissible( c'est à dire qu'elle ne donnerai pas le nombre de coups minimum pour la prochaine solution valide). Ce facteur serait à ajouter au calcul de la distance de Manahattan de la façon suivante :    



