import pdfplumber


def extract_tables_to_markdown(pdf_path, output_file="tables.md"):
    with open(output_file, "w", encoding="utf-8") as md_file:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) == 0:
                        continue

                    # Write header row
                    header = table[0]
                    md_file.write(
                        "| " + " | ".join(str(cell or "") for cell in header) + " |\n"
                    )
                    md_file.write("| " + " | ".join("---" for _ in header) + " |\n")

                    # Write remaining rows
                    for row in table[1:]:
                        md_file.write(
                            "| " + " | ".join(str(cell or "") for cell in row) + " |\n"
                        )

                    # Separate tables with ---
                    md_file.write("\n---\n\n")

    print(f"✅ Tables extracted and saved to: {output_file}")


pdf_path = r"../../data/guide-des-protocoles-699b8192dc98d654208814.pdf"  # replace with your PDF file path
extract_tables_to_markdown(pdf_path, "../../data/only_tables.md")
