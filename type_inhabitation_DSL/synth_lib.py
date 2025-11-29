# synth_lib.py
import yaml, json, heapq
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class Func:
    id: str
    dom: str
    cod: str
    cost: float
    conf: float
    impl: dict
    inverse_of: str|None = None

class Catalog:
    def __init__(self, catalog_dict):
        self.types = {t['name']: t for t in catalog_dict.get('types', [])}
        self.funcs = []
        for f in catalog_dict.get('functions', []):
            sig = f['sig'].strip()
            if '->' not in sig:
                raise ValueError('sig must be A -> B')
            a,b = [s.strip() for s in sig.split('->',1)]
            func = Func(id=f['id'], dom=a, cod=b,
                        cost=float(f.get('cost',1)),
                        conf=float(f.get('confidence',1.0)),
                        impl=f.get('impl',{}),
                        inverse_of=f.get('inverse_of'))
            self.funcs.append(func)
        # index by cod for backward search, and by dom for forward exploration
        self.by_cod = defaultdict(list)
        self.by_dom = defaultdict(list)
        for func in self.funcs:
            self.by_cod[func.cod].append(func)
            self.by_dom[func.dom].append(func)

    def funcs_returning(self, typ):
        return list(self.by_cod.get(typ, []))

    def funcs_from(self, typ):
        return list(self.by_dom.get(typ, []))

# backward A* (here implemented as Dijkstra-like with zero heuristic)
def synthesize_backward(catalog: Catalog, src_type: str, goal_type: str, max_cost=100, max_steps=10000):
    # PQ entries: (est_total_cost, cum_cost, node_type, path_functions_list)
    # path_functions_list is list of Func objects in forward order (from src to goal)
    pq = []
    heapq.heappush(pq, (0.0, 0.0, goal_type, []))
    visited_best = {}  # type -> best_cost_seen
    results = []
    steps = 0
    while pq and steps < max_steps:
        est_total, cum_cost, cur_type, path = heapq.heappop(pq)
        steps += 1
        if cur_type == src_type:
            results.append((cum_cost, list(path)))
            # continue searching for possibly better alternatives
            continue
        # prune
        best = visited_best.get(cur_type)
        if best is not None and cum_cost >= best:
            continue
        visited_best[cur_type] = cum_cost
        # expand: find functions f with f.cod == cur_type
        for f in catalog.funcs_returning(cur_type):
            new_cum = cum_cost + f.cost
            if new_cum > max_cost:
                continue
            new_path = [f] + path  # prepend (because backward)
            next_type = f.dom
            heapq.heappush(pq, (new_cum, new_cum, next_type, new_path))
    results.sort(key=lambda x: x[0])
    return results

def path_to_json(path):
    return [ { 'id': f.id, 'sig': f.dom + ' -> ' + f.cod, 'cost': f.cost, 'conf': f.conf } for f in path ]
