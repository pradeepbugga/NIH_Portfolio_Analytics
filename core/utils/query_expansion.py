import re

def expand_query_for_fts(normalized_query: str, synonym_registry: dict) -> str:
    """
    Takes a pre-normalized query string and appends matching RCDC synonyms
    using the provided in-memory synonym dictionary mapping.
    """
    # Tokenize the base query words (e.g., "multiple sclerosis" -> "'multiple' AND 'sclerosis'")
    base_words = re.findall(r'\w+', normalized_query)
    if not base_words:
        return ""
    base_fts_clause = " AND ".join(f"'{w}'" for w in base_words)
    
    # Check for matching RCDC registry keys within the normalized string
    expanded_terms = []
    for category_name, synonyms in synonym_registry.items():
        if category_name in normalized_query:
            expanded_terms.extend(synonyms)
            
    # Combine with OR operators if synonyms are found
    if expanded_terms:
        synonym_clause = " OR ".join(f"'{syn}'" for syn in expanded_terms)
        return f"({base_fts_clause}) OR {synonym_clause}"
        
    return base_fts_clause