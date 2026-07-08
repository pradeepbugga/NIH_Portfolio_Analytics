
def expand_query_for_fts(normalized_query: str, synonym_registry: dict) -> tuple[str, list[str]]:
    """
    Takes a pre-normalized query string, extracts matching RCDC synonyms,
    and returns BOTH the original query and the list of raw synonym strings.
    """
    expanded_terms = []
    
    # Check for matching RCDC registry keys within the normalized string
    for category_name, synonyms in synonym_registry.items():
        if category_name in normalized_query:
            expanded_terms.extend(synonyms)
            
    return normalized_query, expanded_terms