import re

def get_query_synonyms(normalized_query: str, synonym_registry: dict) -> tuple[str, list[str]]:
    """
    Takes a pre-normalized query string, extracts matching RCDC synonyms,
    and returns both the original query and the list of raw synonym terms.
    """
    expanded_terms = []
    
    # Check for matching RCDC registry keys within the normalized string
    for category_name, synonyms in synonym_registry.items():
        if category_name in normalized_query:
            expanded_terms.extend(synonyms)
            
    # Return both the query and the array of raw short-codes/abbreviations
    return normalized_query, expanded_terms