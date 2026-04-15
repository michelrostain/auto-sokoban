# Algorithme de résolution de labyrinthe
### Les différents algorithmes
**BFS :**    
Technique de parcours de graphe qui agit par couches. On commence à explorer un noeud, puis ses successeurs, puis les successeurs de ses successeurs. Permet de calculer les distances de tous les noeuds depuis un noeud source dans un graphe non-pondéré, orienté ou non orienté. 

**DFS :**    
Technique de parcours de graphe qui explore un chemin dans un graphe jusqu'àun cul de sac ou un sommet déjà vsité. Il reviens alors au dernier sommet où on pouvait explorer un eutre chemin et explore une autre chemin. La récursivité est effective avec la mise en mémoire des noeuds où on a dû faire un choix.   
   
**A* :**   
Technique de parcours de graphe qui combine le coût réel parcouru (g) et une estimation de la distance restante jusqu'à l'arrivée (h), appelée heuristique. A* choisit à chaque étape le nœud dont la somme f = g + h est la plus faible. L'heuristique peut être la distance euclidienne, de Manhattan, ou toute autre estimation qui ne surestime jamais la distance réelle. Sans heuristique (h=0), A* explore par coût croissant sans orientation préférentielle.

### Le coût   



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

