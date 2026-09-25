"""
Ingestion REST Endpoints for SAT-SA.
Supports data seeding, validation, dataset provenance documentation, and external data file uploading.
Includes clean exception handling and database concurrency safety.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import pandas as pd
import io
from src.db.connection import get_db_connection
from src.generator.mock_data import seed_database, validate_soc_dataset, get_dataset_provenance

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


@router.post("/seed-sample-data")
def seed_sample_data(num_days: int = 7):
    """
    Seeds the DuckDB database with realistic synthetic SOC logs.
    """
    conn = get_db_connection(read_only=False)
    try:
        counts = seed_database(conn, num_days=num_days)
        return {
            "status": "success",
            "message": f"Successfully seeded database with {num_days} days of synthetic SOC logs.",
            "records_inserted": counts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Database seeding failed", "message": str(e)}
        )
    finally:
        conn.close()


@router.get("/validate")
def validate_dataset_schema():
    """
    Runs schema structure and relational foreign key integrity checks on current database tables.
    """
    conn = get_db_connection(read_only=True)
    try:
        data = {
            "cses": conn.execute("SELECT * FROM cses").df(),
            "assets": conn.execute("SELECT * FROM assets").df(),
            "analysts": conn.execute("SELECT * FROM analysts").df(),
            "alerts": conn.execute("SELECT * FROM alerts").df(),
            "tickets": conn.execute("SELECT * FROM tickets").df(),
            "investigation_notes": conn.execute("SELECT * FROM investigation_notes").df(),
            "shift_logs": conn.execute("SELECT * FROM shift_logs").df(),
        }
        res = validate_soc_dataset(data)
        return {
            "status": "success",
            "validation": res
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Dataset validation check failed", "message": str(e)}
        )
    finally:
        conn.close()


@router.get("/provenance")
def get_provenance_metadata():
    """
    Returns dataset provenance, documentation, and ground-truth profile metadata.
    """
    try:
        return {
            "status": "success",
            "provenance": get_dataset_provenance()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve provenance metadata", "message": str(e)}
        )


@router.post("/upload")
async def upload_dataset(
    target_table: str = Form(..., description="Target table: 'cses', 'assets', 'analysts', 'alerts', 'tickets', 'investigation_notes', or 'shift_logs'"),
    file: UploadFile = File(...)
):
    """
    Uploads CSV or JSON file and inserts records into specified DuckDB table.
    """
    valid_tables = ["cses", "assets", "analysts", "alerts", "tickets", "investigation_notes", "shift_logs"]
    if target_table not in valid_tables:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid target table", "message": f"Must be one of {valid_tables}"}
        )

    content = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "Unsupported file format", "message": "Only .csv and .json files are supported."}
            )

        conn = get_db_connection(read_only=False)
        try:
            conn.register("df_upload", df)
            conn.execute(f"INSERT INTO {target_table} SELECT * FROM df_upload")
        finally:
            conn.close()

        return {
            "status": "success",
            "target_table": target_table,
            "rows_inserted": len(df)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to ingest uploaded file", "message": str(e)}
        )
