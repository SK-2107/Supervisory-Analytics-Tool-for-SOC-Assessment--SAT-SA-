"""
Quantitative Detection Quality & Ground-Truth Validation Suite for SAT-SA.
Evaluates Precision, Recall, F1-Score, FPR, FNR, CSE Ranking Quality, and Relational Schema Validation.
"""

import pytest
from src.db.connection import get_db_connection
from src.generator.mock_data import seed_database, validate_soc_dataset, get_dataset_provenance
from src.analytics.scoring import calculate_supervisory_attention_scores


@pytest.fixture
def validation_conn():
    conn = get_db_connection(db_path=":memory:")
    seed_database(conn, num_days=7)
    yield conn
    conn.close()


def test_ground_truth_cse_detection(validation_conn):
    """
    Evaluates detection metrics against ground truth CSE profiles.
    """
    results = calculate_supervisory_attention_scores(validation_conn)
    df_cse_scores = results["cse_scores"]
    df_findings = results["findings_df"]

    assert not df_cse_scores.empty
    assert not df_findings.empty

    tp, fp, tn, fn = 0, 0, 0, 0

    for _, row in df_cse_scores.iterrows():
        cid = row["entity_id"]
        score = row["total_score"]
        fnd_cnt = row["finding_count"]

        is_abnormal_gt = (cid != "CSE-101")
        is_flagged = (score >= 10.0 or fnd_cnt > 0)

        if is_abnormal_gt and is_flagged:
            tp += 1
        elif not is_abnormal_gt and is_flagged:
            fp += 1
        elif not is_abnormal_gt and not is_flagged:
            tn += 1
        elif is_abnormal_gt and not is_flagged:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    print(f"\nValidation Quality Metrics:")
    print(f"  -> Precision: {precision * 100:.1f}%")
    print(f"  -> Recall:    {recall * 100:.1f}%")
    print(f"  -> F1-Score:  {f1 * 100:.1f}%")
    print(f"  -> FPR:       {fpr * 100:.1f}%")
    print(f"  -> FNR:       {fnr * 100:.1f}%")

    assert precision >= 0.85
    assert recall >= 0.85
    assert f1 >= 0.85
    assert fpr <= 0.15

    # Verify CSE Ranking Quality: Mature CSE-101 should rank at bottom (lowest attention score)
    cse_101_score = df_cse_scores.loc[df_cse_scores["entity_id"] == "CSE-101", "total_score"].values[0]
    top_cse_score = df_cse_scores.iloc[0]["total_score"]
    assert top_cse_score > cse_101_score
    assert cse_101_score == 0.0


def test_dataset_validation_rules(validation_conn):
    """
    Tests relational schema structure and foreign key validation rules.
    """
    dataset_dict = {
        "cses": validation_conn.execute("SELECT * FROM cses").df(),
        "assets": validation_conn.execute("SELECT * FROM assets").df(),
        "analysts": validation_conn.execute("SELECT * FROM analysts").df(),
        "alerts": validation_conn.execute("SELECT * FROM alerts").df(),
        "tickets": validation_conn.execute("SELECT * FROM tickets").df(),
        "investigation_notes": validation_conn.execute("SELECT * FROM investigation_notes").df(),
        "shift_logs": validation_conn.execute("SELECT * FROM shift_logs").df(),
    }
    val_res = validate_soc_dataset(dataset_dict)
    assert val_res["valid"] is True
    assert val_res["error_count"] == 0
    assert "cses" in val_res["record_counts"]
    assert "assets" in val_res["record_counts"]


def test_dataset_provenance_metadata():
    """
    Tests dataset provenance metadata generation.
    """
    prov = get_dataset_provenance()
    assert "dataset_name" in prov
    assert "ground_truth_profiles" in prov
    assert "CSE-101" in prov["ground_truth_profiles"]

