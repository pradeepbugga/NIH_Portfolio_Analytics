#normalize.py
#this script contains functions to normalize project numbers and names

def normalize_project_num(project_num):
    if not project_num or not isinstance(project_num, str):
        return None
    if project_num.startswith("N"):
        return project_num.split("-")[0]
    return project_num[1:].split("-")[0]


def normalize_name(full_name):
    if not full_name or not isinstance(full_name, str):
        return "", "", "", None

    full_name = full_name.strip().title()
    
    # Handle "Last, First M" format
    if ',' in full_name:
        last, rest = full_name.split(',', 1)
        rest_parts = rest.strip().split()
        first = rest_parts[0] if len(rest_parts) > 0 else ""
        middle = " ".join(rest_parts[1:]) if len(rest_parts) > 1 else ""
    else:
        # Handle "First M Last" format
        parts = full_name.split()
        if len(parts) == 2:
            first, last = parts
            middle = ""
        elif len(parts) == 3:
            first, middle, last = parts
        elif len(parts) > 3:
            first = parts[0]
            middle = " ".join(parts[1:-1])
            last = parts[-1]
        else:
            return "", "", "", None  # Something wrong

    # Canonical format like: "Matrisian, L"
    if first and last:
        canonical = f"{last}, {first[0]}"
    else:
        canonical = None

    return first, middle, last, canonical