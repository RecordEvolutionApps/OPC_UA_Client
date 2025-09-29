from datetime import datetime

def flatten_json_tree(json_obj, tsp, parent_path=""):
    rows = []
    
    for key, value in json_obj.items():
        current_path = f"{parent_path}.{key}" if parent_path else key
        if current_path == 'tsp': continue # the tsp is in every row, no need for an extra row

        if isinstance(value, dict):
            rows.extend(flatten_json_tree(value, tsp, current_path))
        else:
            rows.append({"tsp": tsp, "variable": current_path, "value": value})
    
    return rows

def json_tree_to_table(json_obj):
    tsp = json_obj.get('tsp', datetime.now().astimezone().isoformat())
    rows = flatten_json_tree(json_obj.get("data", {}), tsp)
    return rows