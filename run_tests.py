"""
Test Runner & Quantitative Validation Script for SAT-SA.
Runs database tests, analytics engines, CSE capability evaluations,
ground-truth validation metrics (Precision, Recall, F1, FPR, FNR), and PDF generation.
"""

import sys
from src.db.connection import get_db_connection
from src.generator.mock_data import seed_database, validate_soc_dataset, get_dataset_provenance
from src.analytics.dimensions import evaluate_cse_capability_dimensions
from src.analytics.gaps import detect_execution_gaps
from src.analytics.negative_space import detect_negative_space
from src.analytics.outliers import detect_statistical_outliers
from src.analytics.anomaly import detect_multivariate_anomalies
from src.analytics.similarity import detect_repetitive_investigations
from src.analytics.scoring import calculate_supervisory_attention_scores
from src.reporting.pdf_generator import generate_supervisory_pdf_report


def run_all_tests():
    print("==================================================")
    print("SAT-SA SYSTEM VERIFICATION & VALIDATION SUITE")
    print("==================================================")

    # 1. Database & Schema Initialization Test
    print("\n[1/7] Testing DuckDB Schema Initialization...")
    conn = get_db_connection(db_path=":memory:")
    tables_df = conn.execute("SHOW TABLES").df()
    tables = list(tables_df["name"].values)
    print(f"  -> Created Tables: {tables}")
    assert "cses" in tables
    assert "assets" in tables
    assert "findings" in tables
    assert "supervisory_scores" in tables
    print("  [PASS] Database schema initialization successful.")

    # 2. Synthetic Data Seeding & Relational Validation Test (6 CSE Profiles)
    print("\n[2/7] Testing Ground-Truth Synthetic Dataset Generator & Validation...")
    counts = seed_database(conn, num_days=7)
    print(f"  -> Records Seeded: {counts}")
    assert counts["cses_count"] == 6
    assert counts["assets_count"] == 36
    assert counts["tickets_count"] > 0

    dataset_dict = {
        "cses": conn.execute("SELECT * FROM cses").df(),
        "assets": conn.execute("SELECT * FROM assets").df(),
        "analysts": conn.execute("SELECT * FROM analysts").df(),
        "alerts": conn.execute("SELECT * FROM alerts").df(),
        "tickets": conn.execute("SELECT * FROM tickets").df(),
        "investigation_notes": conn.execute("SELECT * FROM investigation_notes").df(),
        "shift_logs": conn.execute("SELECT * FROM shift_logs").df(),
    }
    val_res = validate_soc_dataset(dataset_dict)
    print(f"  -> Relational Validation Result: Valid={val_res['valid']} | Errors={val_res['error_count']}")
    assert val_res["valid"] is True

    prov = get_dataset_provenance()
    print(f"  -> Dataset Provenance: {prov['dataset_name']} (v{prov['version']})")
    print("  [PASS] Dataset generator, provenance, and schema validation successful.")

    # 3. 8 SIH26157 Capability Dimensions Test
    print("\n[3/7] Testing 8 Capability Dimensions & Findings Engine...")
    dim_res = evaluate_cse_capability_dimensions(conn)
    df_findings = dim_res["findings_df"]
    df_dim_scores = dim_res["dimension_scores"]
    print(f"  -> Total Structured Evidence Findings Logged: {len(df_findings)}")
    print(f"  -> CSE Capability Evaluations Completed: {len(df_dim_scores)}")
    assert not df_findings.empty
    print("  [PASS] 8 capability dimensions evaluation successful.")

    # 4. Analytics Sub-Engines Test
    print("\n[4/7] Testing Analytics Sub-Engines...")
    gaps = detect_execution_gaps(conn)
    print(f"  -> Execution Gaps Flagged: {len(gaps['ticket_gaps'])}")
    
    neg = detect_negative_space(conn)
    print(f"  -> Negative Space Flagged: {len(neg['analyst_negative_space'])}")

    outliers = detect_statistical_outliers(conn)
    print(f"  -> Outliers Evaluated: {len(outliers)}")

    anomalies = detect_multivariate_anomalies(conn)
    print(f"  -> Anomaly Scores (Isolation Forest): {len(anomalies)}")

    similarity = detect_repetitive_investigations(conn)
    print(f"  -> High Text Similarity Matches (TF-IDF): {len(similarity['high_similarity_pairs'])}")
    print("  [PASS] All sub-analytic engines executed cleanly.")

    # 5. Primary CSE Supervisory Attention Indicator Scoring Test
    print("\n[5/7] Testing CSE Supervisory Attention Indicator Scoring...")
    scoring_res = calculate_supervisory_attention_scores(conn)
    df_cse_scores = scoring_res["cse_scores"]

    print("  Ranked CSE Supervisory Attention Queue:")
    for idx, row in df_cse_scores.iterrows():
        print(f"    - [{row['criticality']}] {row['entity_name']} ({row['entity_id']}): Attention Score = {row['total_score']:.1f}/100 | {row['priority_level']}")

    assert not df_cse_scores.empty
    print("  [PASS] CSE supervisory attention scoring test successful.")

    # 6. Quantitative Ground-Truth Validation Metrics Test
    print("\n[6/7] Computing Ground-Truth Validation Quality Metrics...")
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

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    print(f"  -> Precision: {precision * 100:.1f}%")
    print(f"  -> Recall:    {recall * 100:.1f}%")
    print(f"  -> F1-Score:  {f1 * 100:.1f}%")
    print(f"  -> FPR:       {fpr * 100:.1f}%")
    print(f"  -> FNR:       {fnr * 100:.1f}%")
    assert precision >= 0.85
    assert recall >= 0.85
    print("  [PASS] Quantitative validation metrics passed.")

    # 7. ReportLab PDF Export Test
    print("\n[7/7] Testing ReportLab PDF Audit Exporter...")
    pdf_bytes = generate_supervisory_pdf_report(conn)
    print(f"  -> Generated PDF size: {len(pdf_bytes)} bytes")
    assert len(pdf_bytes) > 1000
    print("  [PASS] PDF export test successful.")

    conn.close()

    print("\n==================================================")
    print("ALL SAT-SA TESTS PASSED SUCCESSFULLY! [100% SUCCESS]")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()

