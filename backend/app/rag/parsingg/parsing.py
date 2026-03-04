import os

from dotenv import load_dotenv
from llama_parse import LlamaParse

pdf_path = r"../data/guide-des-protocoles-699b8192dc98d654208814.pdf"
md_output = r"../data/1_guide-des-protocoles.md"


load_dotenv()

parser = LlamaParse(
    api_key=os.environ.get("llamaParse_Key"),
    result_type="markdown",
    verbose=True,
    language="fr",
)

documents = parser.load_data(pdf_path)

with open(md_output, "w", encoding="utf-8") as f:
    for doc in documents:
        f.write(doc.text + "---")
