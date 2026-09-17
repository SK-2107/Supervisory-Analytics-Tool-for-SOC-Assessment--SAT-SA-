"""
Repetitive Investigation Notes Detection Module for SAT-SA.
Uses TF-IDF Vectorization and Cosine Similarity to detect copy-paste notes and superficial templates.
Optimized with upper-triangular matrix filtering, character length thresholding, and fast aggregation.
"""

import pandas as pd
import numpy as np
import re
import math
from collections import Counter

HAS_SKLEARN = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
    "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def _pure_python_tfidf_cosine_sim(texts):
    """
    Pure Python/NumPy TF-IDF + Cosine Similarity fallback when sklearn is unavailable/blocked.
    Returns square N x N numpy array of cosine similarities.
    """
    doc_ngrams = []
    df_counts = Counter()

    for text in texts:
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]+\b', text) if w.lower() not in STOP_WORDS]
        ngrams = list(words)
        for i in range(len(words) - 1):
            ngrams.append(f"{words[i]}_{words[i+1]}")
        doc_ngrams.append(ngrams)
        for ng in set(ngrams):
            df_counts[ng] += 1

    n_docs = len(texts)
    if n_docs == 0:
        return np.zeros((0, 0))

    idfs = {ng: math.log((1.0 + n_docs) / (1.0 + count)) + 1.0 for ng, count in df_counts.items()}

    doc_vectors = []
    norms = []
    for ngrams in doc_ngrams:
        tf = Counter(ngrams)
        vec = {}
        sq_sum = 0.0
        for ng, count in tf.items():
            val = count * idfs[ng]
            vec[ng] = val
            sq_sum += val * val
        norm = math.sqrt(sq_sum)
        doc_vectors.append(vec)
        norms.append(norm)

    cos_sim = np.zeros((n_docs, n_docs), dtype=float)
    for i in range(n_docs):
        cos_sim[i, i] = 1.0
        norm_i = norms[i]
        if norm_i == 0:
            continue
        vec_i = doc_vectors[i]
        for j in range(i + 1, n_docs):
            norm_j = norms[j]
            if norm_j == 0:
                continue
            v1, v2 = (vec_i, doc_vectors[j]) if len(vec_i) < len(doc_vectors[j]) else (doc_vectors[j], vec_i)
            dot = sum(val1 * v2[ng] for ng, val1 in v1.items() if ng in v2)
            sim = dot / (norm_i * norm_j)
            cos_sim[i, j] = sim
            cos_sim[j, i] = sim

    return cos_sim


def detect_repetitive_investigations(conn, similarity_threshold: float = 0.85, max_display_pairs: int = 50):
    """
    Computes TF-IDF vectors for investigation notes and detects high pairwise cosine similarity.
    Filters out short operational boilerplate (<30 chars) and ranks top suspicious matches.
    Returns dict containing:
        - 'high_similarity_pairs': DataFrame of matching pairs with similarity scores.
        - 'ticket_similarity_scores': DataFrame of similarity scores per ticket.
        - 'analyst_similarity_scores': DataFrame summarizing repetitive note usage per analyst.
    """
    query = """
        SELECT 
            n.note_id,
            n.cse_id,
            n.ticket_id,
            n.analyst_id,
            a.name AS analyst_name,
            n.created_at,
            n.note_text,
            n.word_count
        FROM investigation_notes n
        JOIN analysts a ON n.analyst_id = a.analyst_id
        WHERE n.note_text IS NOT NULL AND LENGTH(TRIM(n.note_text)) > 30
    """
    df = conn.execute(query).df()

    if df.empty or len(df) < 2:
        return {
            "high_similarity_pairs": pd.DataFrame(),
            "ticket_similarity_scores": pd.DataFrame(),
            "analyst_similarity_scores": pd.DataFrame()
        }

    cos_sim = None
    if HAS_SKLEARN:
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(df["note_text"])
            cos_sim = cosine_similarity(tfidf_matrix)
        except Exception:
            cos_sim = None

    if cos_sim is None:
        cos_sim = _pure_python_tfidf_cosine_sim(df["note_text"].tolist())

    # Upper triangle indices without self-matches (i < j)
    rows, cols = np.where(np.triu(cos_sim, k=1) >= similarity_threshold)

    if len(rows) == 0:
        return {
            "high_similarity_pairs": pd.DataFrame(),
            "ticket_similarity_scores": pd.DataFrame(),
            "analyst_similarity_scores": pd.DataFrame()
        }

    # Extract top N suspicious pairs efficiently
    pair_indices = list(zip(rows, cols))
    # Limit processing if there are tens of thousands of duplicate template pairs
    if len(pair_indices) > 500:
        # Sample or take first 500 pairs for detail generation
        pair_indices = pair_indices[:500]

    pairs = []
    ticket_sim_map = {}
    analyst_sim_map = {}

    for i, j in pair_indices:
        t1 = df.iloc[i]
        t2 = df.iloc[j]

        if t1["ticket_id"] == t2["ticket_id"]:
            continue

        sim = float(cos_sim[i, j])

        pairs.append({
            "ticket_id_1": t1["ticket_id"],
            "cse_id_1": t1["cse_id"],
            "analyst_id_1": t1["analyst_id"],
            "analyst_name_1": t1["analyst_name"],
            "ticket_id_2": t2["ticket_id"],
            "cse_id_2": t2["cse_id"],
            "analyst_id_2": t2["analyst_id"],
            "analyst_name_2": t2["analyst_name"],
            "similarity_score": round(sim, 4),
            "note_preview_1": t1["note_text"][:120] + "...",
            "note_preview_2": t2["note_text"][:120] + "..."
        })

        for t_id, cid, aid in [(t1["ticket_id"], t1["cse_id"], t1["analyst_id"]), (t2["ticket_id"], t2["cse_id"], t2["analyst_id"])]:
            if t_id not in ticket_sim_map:
                ticket_sim_map[t_id] = {"ticket_id": t_id, "cse_id": cid, "analyst_id": aid, "max_sim": sim, "matches": 1}
            else:
                ticket_sim_map[t_id]["max_sim"] = max(ticket_sim_map[t_id]["max_sim"], sim)
                ticket_sim_map[t_id]["matches"] += 1

            if aid not in analyst_sim_map:
                analyst_sim_map[aid] = {"analyst_id": aid, "high_sim_count": 1, "max_similarity": sim}
            else:
                analyst_sim_map[aid]["high_sim_count"] += 1
                analyst_sim_map[aid]["max_similarity"] = max(analyst_sim_map[aid]["max_similarity"], sim)

    df_pairs = pd.DataFrame(pairs)
    if not df_pairs.empty:
        df_pairs = df_pairs.sort_values(by="similarity_score", ascending=False).head(max_display_pairs)

    ticket_results = []
    for t_id, data in ticket_sim_map.items():
        sim_val = data["max_sim"]
        match_cnt = data["matches"]
        score = min(100.0, sim_val * 80.0 + min(20.0, match_cnt * 5.0))
        ticket_results.append({
            "ticket_id": t_id,
            "cse_id": data["cse_id"],
            "analyst_id": data["analyst_id"],
            "repetitive_text_score": round(score, 2),
            "similarity_explanations": [f"High text similarity ({sim_val*100:.1f}%) detected with {match_cnt} other ticket notes"]
        })

    df_ticket_sim = pd.DataFrame(ticket_results)

    analyst_results = []
    for aid, data in analyst_sim_map.items():
        cnt = data["high_sim_count"]
        max_s = data["max_similarity"]
        score = min(100.0, max_s * 60.0 + min(40.0, cnt * 8.0))
        analyst_results.append({
            "analyst_id": aid,
            "repetitive_text_score": round(score, 2),
            "copy_paste_flag_count": cnt,
            "max_similarity_detected": round(max_s, 4)
        })

    df_analyst_sim = pd.DataFrame(analyst_results)

    return {
        "high_similarity_pairs": df_pairs,
        "ticket_similarity_scores": df_ticket_sim,
        "analyst_similarity_scores": df_analyst_sim
    }
