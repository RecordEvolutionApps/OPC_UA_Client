from datetime import datetime

def flatten_json_tree(json_obj, tsp, parent_path=""):
    rows = []
    
    for key, value in json_obj.items():
        current_path = f"{parent_path}.{key}" if parent_path else key
        
        if isinstance(value, dict):
            rows.extend(flatten_json_tree(value, current_path))
        else:
            rows.append({"tsp": tsp, "variable": current_path, "value": value})
    
    return rows

def json_tree_to_table(json_obj):
    tsp = datetime.now().astimezone().isoformat()
    rows = flatten_json_tree(json_obj, tsp)
    return rows