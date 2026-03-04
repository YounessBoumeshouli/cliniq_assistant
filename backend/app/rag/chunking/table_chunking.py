import json
import os
import time

import mlflow

md_file = os.path.join(os.path.dirname(__file__), "../../data/only_tables.md")
json_output = os.path.join(os.path.dirname(__file__), "../../data/table_chunks1.json")

# ---------------------------
# MLflow Setup
# ---------------------------
mlflow.set_tracking_uri("http://localhost:5009")
mlflow.set_experiment("RAG_Chunking")

start_time = time.time()

with mlflow.start_run(run_name="table_chunking"):

    # ---------------------------
    # Log Static Params
    # ---------------------------
    mlflow.log_param("input_markdown_file", md_file)
    mlflow.log_param("output_json_file", json_output)
    mlflow.log_param("chunking_strategy", "table_row_based")

    # ---------------------------
    # Load Markdown
    # ---------------------------
    with open(md_file, "r", encoding="utf-8") as f:
        text = f.read()

    def split_into_tables(text):
        tables = []
        for t in text.split("\n---\n"):
            tables.append(t.strip())
        return tables

    def parse_table_rows(table_text, table_id):
        lines = [line.rstrip() for line in table_text.split("\n") if line.strip()]
        if not lines:
            return []
        header = [h.strip() for h in lines[0].strip("|").split("|")]
        num_cols = len(header)

        chunks = []
        buffer = ""

        for line in lines[2:]:
            buffer += line + "\n"
            if buffer.count("|") >= num_cols + 1:
                cells = [
                    c.strip().replace("\n", " ")
                    for c in buffer.strip().strip("|").split("|")
                ]
                row = {}
                for i in range(num_cols):
                    row[header[i]] = cells[i] if i < len(cells) else ""
                chunks.append({"table_id": table_id, "row": row})
                buffer = ""

        return chunks

    def parse_all_tables(text):
        tables = split_into_tables(text)
        all_chunks = []
        column_counts = []

        for idx, t in enumerate(tables, 1):
            rows = parse_table_rows(t, idx)
            all_chunks.extend(rows)

            # count columns for metrics
            if rows:
                column_counts.append(len(rows[0]["row"]))

        return tables, all_chunks, column_counts

    # ---------------------------
    # Parse Tables
    # ---------------------------
    tables, chunks, column_counts = parse_all_tables(text)

    # ---------------------------
    # Save JSON
    # ---------------------------
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Log Dynamic Params
    # ---------------------------
    mlflow.log_param("tables_detected", len(tables))
    mlflow.log_param("total_chunks_created", len(chunks))

    # ---------------------------
    # Log Metrics
    # ---------------------------
    duration = time.time() - start_time

    avg_columns = sum(column_counts) / len(column_counts) if column_counts else 0

    mlflow.log_metric("avg_columns_per_table", avg_columns)
    mlflow.log_metric("chunking_duration_seconds", duration)

print("Chunking completed and saved ✅")
