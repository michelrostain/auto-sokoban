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
    for mode in ('BFS', 'DFS', 'Astar'):
        m = copy.deepcopy(charger_niveau(1))
        _, _, _, log = solveur(m, mode=mode)
        etats = [entry[0] for entry in log]
        assert len(etats) == len(set(etats)), f"{mode}: chaque état doit apparaître une seule fois"

def test_nb_visites_coherent_avec_log():
    for mode in ('BFS', 'DFS', 'Astar'):
        m = copy.deepcopy(charger_niveau(1))
        _, _, nb_visites, log = solveur(m, mode=mode)
        assert nb_visites == len(log), f"{mode}: nb_visites doit égaler len(log)"


def _make_graph_window_stub(algo='BFS'):
    """Crée un GraphWindow minimal sans pygame pour tester le layout."""
    from build_game import solveur, charger_niveau
    import copy
    m = copy.deepcopy(charger_niveau(1))
    _, _, _, log = solveur(m, mode=algo)

    import graph_view
    obj = object.__new__(graph_view.GraphWindow)
    obj.exploration_log = log[:graph_view.MAX_NODES]
    obj.chemin          = None
    obj.algo            = algo
    obj.targets         = []
    obj.node_positions  = {}
    obj.parent_of       = {}
    obj.tree_height     = 0
    obj._compute_layout()
    return obj

def test_layout_bfs_positions_uniques():
    gw = _make_graph_window_stub('BFS')
    positions = list(gw.node_positions.values())
    assert len(positions) == len(set(positions))

def test_layout_racine_en_haut():
    from build_game import charger_niveau, get_etat
    import copy
    gw = _make_graph_window_stub('BFS')
    m = copy.deepcopy(charger_niveau(1))
    etat_racine = get_etat(m)
    _, y_racine = gw.node_positions[etat_racine]
    min_y = min(py for _, py in gw.node_positions.values())
    assert y_racine == min_y

def test_layout_tous_les_etats_places():
    gw = _make_graph_window_stub('BFS')
    for entry in gw.exploration_log:
        etat = entry[0]
        assert etat in gw.node_positions
