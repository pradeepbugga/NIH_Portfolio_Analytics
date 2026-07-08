import re

import re

def expand_query_for_fts(normalized_query: str, synonym_registry: dict) -> str:
    """
    Takes a pre-normalized query string and appends matching RCDC synonyms
    using strict Postgres native operators (& and |) for to_tsquery compatibility.
    """
    # 1. Tokenize the base words
    base_words = re.findall(r'\w+', normalized_query)
    if not base_words:
        return ""
    
    # Use native Postgres '&' instead of string 'AND' 🚀
    base_fts_clause = " & ".join(f"'{w}'" for w in base_words)
    
    # 2. Extract synonyms from global dictionary
    expanded_terms = []
    for category_name, synonyms in synonym_registry.items():
        if category_name in normalized_query:
            expanded_terms.extend(synonyms)
            
    # 3. Combine using native Postgres '|' instead of string 'OR' 🚀
    if expanded_terms:
        synonym_clause = " | ".join(f"'{syn}'" for syn in expanded_terms)
        return f"({base_fts_clause}) | {synonym_clause}"
        
    return base_fts_clause