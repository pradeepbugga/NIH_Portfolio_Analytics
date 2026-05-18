import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

def cluster_filtered_grants(active_grants_list):
    """
    Takes the dynamically filtered grants currently showing on the frontend,
    clusters them using your HDBSCAN workflow, and extracts the key content.
    """
    if len(active_grants_list) < 50:
        return {"error": "Not enough grants to cluster dynamically."}

    # 1. Extract raw text abstracts and pre-computed embeddings
    abstracts = [g["abstract"] for g in active_grants_list]
    titles = [g["title"] for g in active_grants_list]
    embeddings = np.array([g["embedding"] for g in active_grants_list])
    amount = np.array([g["amount"] for g in active_grants_list], dtype=np.float32)

    # Safety Check: If you have fewer grants than your targeted cluster count
    num_grants = len(active_grants_list)
    n_clusters = min(6, num_grants) # Target 6 distinct strategic pillars, adjusted for small pools

    if num_grants < 2: 
        # not enough data to cluster, return all as cluster 0
        for g in active_grants_list:
            g["cluster_id"] = 0
        return {"0": active_grants_list}

    # initalize and fit agglomerative clustering model
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters, 
        metric = 'cosine', 
        linkage = 'average'
    )
    labels = clusterer.fit_predict(embeddings)

    clusters_output = {}
    for idx, label in enumerate(labels):
        label_id = int(label)
        
        # Agglomerative Clustering has no noise outliers (-1), 
        # so every single grant gets cleanly accounted for here.

        if label_id not in clusters_output:
            clusters_output[label_id] = []

        # Grab and sanitize the amount value
        raw_amount = amount[idx]
        try:
            grant_amount = float(raw_amount) if raw_amount is not None else 0.0
        except ValueError:
            grant_amount = 0.0

        clusters_output[label_id].append({
            "grant_id": active_grants_list[idx].get("grant_id"), # Keeping your primary unique keys intact
            "title": active_grants_list[idx].get("title") or titles[idx],
            "abstract": active_grants_list[idx].get("abstract") or abstracts[idx], 
            "amount": grant_amount,
            "text": active_grants_list[idx].get("text", "") # Crucial for your LLM context parsing!
        })

    return clusters_output

 