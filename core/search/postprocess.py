# this script deduplicates results by core project number


def dedupe_by_core_project(results):
    seen = set()
    output = []
    for r in results:
        if r["core_project_num"] not in seen:
            seen.add(r["core_project_num"])
            output.append(r)
    return output
