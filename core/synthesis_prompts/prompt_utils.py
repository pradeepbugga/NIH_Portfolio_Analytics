def lookup_mission_by_name(cluster_label: str, missions_db: dict) -> dict:
    """
    Finds an institute profile by matching against its acronym key 
    or its human-readable full name.
    """
    # Clean up input string for resilient matching
    target = cluster_label.strip().lower()
    
    # 1. Direct key match check (e.g., if label is 'NCI')
    if cluster_label in missions_db:
        return missions_db[cluster_label]
        
    # 2. Iterative value match check (e.g., if label is 'National Cancer Institute')
    for acronym, profile in missions_db.items():
        if target == profile.get("full_name", "").strip().lower():
            return profile
            
    return None

def format_currency_short(amount: float) -> str:
    """
    Converts a raw float amount into an abbreviated, rounded string format.
    Example: 2486960962.00 -> $2.5B
    Example: 218709838.00  -> $218.7M
    """
    if amount is None:
        return "$0.0"
    
    abs_amount = abs(amount)
    
    if abs_amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif abs_amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif abs_amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    else:
        return f"${amount:.1f}"