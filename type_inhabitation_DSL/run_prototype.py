# run_prototype.py
import yaml, json
from synth_lib import Catalog, synthesize_backward, path_to_json

def main():
    catalog_path = "catalog.yaml"
    with open(catalog_path, "r", encoding="utf-8") as f:
        cat_dict = yaml.safe_load(f)
    cat = Catalog(cat_dict)
    results = synthesize_backward(cat, src_type="Product", goal_type="CO2", max_cost=50)
    out = {"goal":"Product->CO2", "plans": []}
    for cost, path in results:
        out["plans"].append({
            "cost": cost,
            "confidence_est": round(prod_confidence(path), 6),
            "steps": path_to_json(path),
            "proof": " ∘ ".join([p.id for p in path])
        })
    print(json.dumps(out, indent=2, ensure_ascii=False))

def prod_confidence(path):
    if not path:
        return 1.0
    prod = 1.0
    for p in path:
        prod *= p.conf
    return prod

if __name__ == "__main__":
    main()
