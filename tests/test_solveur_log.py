import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from build_game import solveur, charger_niveau, get_etat
import copy

def test_solveur_retourne_4_valeurs():
    m = copy.deepcopy(charger_niveau(1))
    result = solveur(m, mode='BFS')
    assert len(result) == 4, f"Attendu 4 valeurs, obtenu {len(result)}"

def test_exploration_log_bfs_format():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='BFS')
    assert len(log) > 0
    # Premier entrée = racine, parent None
    etat0, parent0 = log[0]
    assert parent0 is None
    # Toutes les autres entrées ont un parent
    for etat, parent in log[1:]:
        assert parent is not None

def test_exploration_log_astar_a_h_score():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='Astar')
    assert len(log) > 0
    # Toutes les entrées ont 3 éléments
    for entry in log:
        assert len(entry) == 3, f"A* attendu 3 éléments par entrée, obtenu {len(entry)}"
        etat, parent, h = entry
        assert isinstance(h, (int, float))
        assert h >= 0

def test_exploration_log_dfs_format():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='DFS')
    assert len(log) > 0
    etat0, parent0 = log[0]
    assert parent0 is None

def test_log_pas_de_doublons():
    m = copy.deepcopy(charger_niveau(1))
    _, _, _, log = solveur(m, mode='BFS')
    etats = [entry[0] for entry in log]
    assert len(etats) == len(set(etats)), "Chaque état doit apparaître une seule fois"

def test_nb_visites_coherent_avec_log():
    m = copy.deepcopy(charger_niveau(1))
    _, _, nb_visites, log = solveur(m, mode='BFS')
    assert nb_visites == len(log)
