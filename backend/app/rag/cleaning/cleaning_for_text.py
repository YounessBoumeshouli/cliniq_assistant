md_file = r"../../data/1_guide-des-protocoles.md"
md_output = r"../../data/only_text.md"


with open(md_file, "r", encoding="utf-8") as f:
    text = f.read()


def split_into_pages(text):
    pages = []
    for p in text.split("\n---\n"):
        pages.append(p.strip())
    return pages


def remove_header(text):
    pages = split_into_pages(text)
    cleaned_pages = []
    remove_words = ["Version", "Validation", "Date"]
    for p in pages:
        lines = p.split("\n")
        new_lines = []
        for line in lines:
            if not any(word in line for word in remove_words):
                new_lines.append(line)

        cleaned_pages.append("\n".join(new_lines).strip())

    return "\n---\n".join(cleaned_pages)


def remove_footer(text):
    pages = split_into_pages(text)
    cleaned_pages = []
    for p in pages:
        lines = p.split("\n")
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if "Guide des Protocoles" in stripped:
                continue
            if stripped.isdigit():
                continue
            new_lines.append(line)
        cleaned_pages.append("\n".join(new_lines))
    return "\n---\n".join(cleaned_pages)


def remove_tables(text):
    pages = split_into_pages(text)
    cleaned_pages = []

    for p in pages:
        lines = p.split("\n")
        lines = [line for line in lines if not line.strip().startswith("|")]
        cleaned_pages.append("\n".join(lines))

    return "\n---\n".join(cleaned_pages)


with open(md_output, "w", encoding="utf-8") as f:
    f.write(remove_tables(remove_footer(remove_header(text))))
