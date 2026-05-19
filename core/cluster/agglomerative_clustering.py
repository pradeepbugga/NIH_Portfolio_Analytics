import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import re
from collections import Counter

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

def cluster_filtered_grants_for_map(active_grants_list):
    """
    Clusters active grants via Agglomerative Clustering and computes advanced
    spatial telemetry (centroids, semantic boundaries, and outlier flags) 
    to feed the high-innovation and maturity topic analysis.
    """
    if len(active_grants_list) < 5:
        return {"error": "Not enough grants to cluster dynamically."}

    # 1. Extract metadata and vectors
    abstracts = [g.get("abstract", "") for g in active_grants_list]
    titles = [g.get("title", "") for g in active_grants_list]
    embeddings = np.array([g["embedding"] for g in active_grants_list])
    amounts = np.array([g.get("amount", 0.0) for g in active_grants_list], dtype=np.float32)
    mechanisms = [g["grant_id"][1:4].upper() if g.get("grant_id") and len(g["grant_id"]) >= 4 else "Other" for g in active_grants_list]


    num_grants = len(active_grants_list)
    
    # Dynamically scale cluster counts so large datasets split beautifully
    if num_grants > 1000:
        n_clusters = 12  # Give the LLM more specialized pillars to analyze
    elif num_grants > 200:
        n_clusters = 8
    else:
        n_clusters = min(6, num_grants)

    # Unit-normalize embeddings for pristine cosine calculations
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid divide-by-zero for safety
    norms[norms == 0] = 1.0
    normalized_embeddings = embeddings / norms

    # Execute Complete Linkage to ruthlessly break up massive clusters
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters, 
        metric='cosine', 
        linkage='complete' # Crucial switch to stop mega-clusters!
    )
    labels = clusterer.fit_predict(normalized_embeddings)

    # 3. Create structural cluster groups
    raw_clusters = {}
    for idx, label in enumerate(labels):
        label_id = int(label)
        if label_id not in raw_clusters:
            raw_clusters[label_id] = []
        
        raw_clusters[label_id].append({
            "idx": idx,
            "grant_id": active_grants_list[idx].get("grant_id"),
            "title": titles[idx],
            "abstract": abstracts[idx],
            "amount": float(amounts[idx]),
            "mechanism": mechanisms[idx],
            "embedding": embeddings[idx]
        })

    # High-risk mechanisms that denote agile, early-stage exploratory research
    AGILE_MECHANISMS = {"R21", "DP2", "DP5", "UG3", "UH2", "R33", "K99", "R00", "F31", "F32", "R43", "R41"}

    final_clusters_payload = {}

    # 4. Compute Spatial Telemetry & Extract Web-Search Query Strings
    for label_id, cluster_items in raw_clusters.items():
        cluster_embeddings = np.array([item["embedding"] for item in cluster_items])
        cluster_amounts = [item["amount"] for item in cluster_items]
        
        # Calculate cluster core metrics
        total_cluster_budget = sum(cluster_amounts)
        cluster_size = len(cluster_items)
        
        # Calculate mathematical Centroid
        centroid = np.mean(cluster_embeddings, axis=0)
        centroid = centroid / np.linalg.norm(centroid)  # Normalize
        
        # Calculate Cosine Distance from Centroid for every single item in this cluster
        for item in cluster_items:
            # cosine_distance returns 1 - cosine_similarity
            item["distance_from_centroid"] = float(cosine_distances(item["embedding"].reshape(1, -1), centroid.reshape(1, -1))[0][0])

        # Sort cluster items by distance from centroid (Ascending = Core Consensus, Descending = Structural Outliers)
        cluster_items.sort(key=lambda x: x["distance_from_centroid"])
        
        consensus_core_projects = cluster_items[:3]  # Closest to center
        peripheral_outlier_projects = cluster_items[-3:]  # Furthest on spatial boundaries
        
        # Scan peripheral outliers for high-innovation signature (Boundary Position + Agile Mechanism)
        innovation_outliers_payload = []
        for out in reversed(peripheral_outlier_projects):  # Start with absolute furthest
            if out["mechanism"] in AGILE_MECHANISMS:
                innovation_outliers_payload.append({
                    "title": out["title"],
                    "mechanism": out["mechanism"],
                    "amount": out["amount"],
                    "distance_score": round(out["distance_from_centroid"], 3)
                })

        # Generate a targeted real-time web search query string based on word frequencies in titles
        combined_titles = " ".join([item["title"].lower() for item in cluster_items])
        words = re.findall(r'\b[a-z]{4,}\b', combined_titles)  # Keep words with length >= 4
        stop_words = {"research", "study", "grant", "clinical", "project", "analysis", "effects", "mechanisms", "targeting", "treatment", "therapeutic", "disease", "patients"}
        filtered_words = [w for w in words if w not in stop_words]
        top_terms = [pair[0] for pair in Counter(filtered_words).most_common(4)]
        search_query_string = f"{' '.join(top_terms)} scientific breakthroughs therapeutic trends 2025 2026"

        # Build final structural payload block for this topic cluster
        final_clusters_payload[str(label_id)] = {
            "cluster_id": label_id,
            "total_budget": total_cluster_budget,
            "project_count": cluster_size,
            "generated_web_search_query": search_query_string,
            "consensus_core": [
                {"title": p["title"], "amount": p["amount"], "mechanism": p["mechanism"]} 
                for p in consensus_core_projects
            ],
            "high_innovation_outliers": innovation_outliers_payload[:2] # Keep top 2 maximum to conserve tokens
        }

    return final_clusters_payload 