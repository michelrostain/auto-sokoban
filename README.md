# Algorithme de résolution de labyrinthe
## Les différents algorithmes
**BFS :**    
Technique de parcours de graphe qui agit par couches. On commence à explorer un noeud, puis ses successeurs, puis les successeurs de ses successeurs. Permet de calculer les distances de tous les noeuds depuis un noeud source dans un graphe non-pondéré, orienté ou non orienté. 

**DFS :**    
Technique de parcours de graphe qui explore un chemin dans un graphe jusqu'àun cul de sac ou un sommet déjà vsité. Il reviens alors au dernier sommet où on pouvait explorer un eutre chemin et explore une autre chemin. La récursivité est effective avec la mise en mémoire des noeuds où on a dû faire un choix.  