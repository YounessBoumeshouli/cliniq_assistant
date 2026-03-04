import json
import os
import time

import mlflow
print("Starting text chunking process...")
md_file = os.path.join(os.path.dirname(__file__), "../../data/only_text.md")
json_output = os.path.join(os.path.dirname(__file__), "../../data/text_chunks1.json")

mlflow.set_tracking_uri("http://localhost:5009")
mlflow.set_experiment("RAG_Chunking")

start_time = time.time()

with mlflow.start_run(run_name="text_chunking"):

    mlflow.log_param("input_markdown_file", md_file)
    mlflow.log_param("output_json_file", json_output)
    mlflow.log_param("chunking_strategy", "title_based")
    mlflow.log_param("domain_strategy", "page_range_mapping")

    def chunk_markdown_by_title(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            pages = f.read().split("\n---\n")

        all_chunks = []

        for page_number, page in enumerate(pages, 1):
            lines = page.split("\n")
            current_title = None
            current_content = []

            for line in lines:
                line = line.strip()

                if line.startswith("#"):
                    if current_title and current_content:
                        all_chunks.append(
                            {
                                "title": current_title.replace("#", "").strip(),
                                "content": "\n".join(current_content).strip(),
                                "page": page_number,
                            }
                        )

                    current_title = line
                    current_content = []

                elif current_title:
                    if line != "":
                        current_content.append(line)

            if current_title and current_content:
                all_chunks.append(
                    {
                        "title": current_title.replace("#", "").strip(),
                        "content": "\n".join(current_content).strip(),
                        "page": page_number,
                    }
                )

        return pages, all_chunks

    def add_domain_metadata(chunks):
        for chunk in chunks:
            page = chunk["page"]

            if 1 <= page <= 8:
                chunk["domain"] = "PÉDIATRIE"
            elif 9 <= page <= 37:
                chunk["domain"] = "MÉDECINE ADULTE"
            elif 38 <= page <= 48:
                chunk["domain"] = "DENTAIRE"
            else:
                chunk["domain"] = "UNKNOWN"

        return chunks

    pages, chunks = chunk_markdown_by_title(md_file)
    chunks = add_domain_metadata(chunks)

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    mlflow.log_param("total_pages_detected", len(pages))
    mlflow.log_param("total_chunks_created", len(chunks))

    chunk_lengths = [len(chunk["content"]) for chunk in chunks]

    avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
    max_chunk_length = max(chunk_lengths) if chunk_lengths else 0

    duration = time.time() - start_time

    mlflow.log_metric("avg_chunk_length", avg_chunk_length)
    mlflow.log_metric("max_chunk_length", max_chunk_length)
    mlflow.log_metric("chunking_duration_seconds", duration)

print("JSON with domain metadata created and tracked in MLflow ✅")
