from pathlib import Path
from markdownify import markdownify as md
from tqdm import tqdm


def convert_html_to_markdown(in_dir: Path, out_dir: Path, doc_name: str):
    """
    Convert HTML files in a given directory to markdown files.
    """
    pages = in_dir / doc_name / "pages"
    markdown_pages = []
    # convert all HTML files in the pages directory to markdown
    for html_file in pages.glob("*.html"):
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # convert HTML to markdown
        markdown = md(html_content)
        # save the markdown page if not empty
        if markdown.strip():
            markdown_pages.append(markdown)

    # save the markdown to a file with the same name but .md extension
    md_file = out_dir / f"{doc_name}.md"
    if not markdown_pages:
        print(f"No content found in {doc_name}. Skipping...")
        return

    with open(md_file, "w", encoding="utf-8") as f:
        # write each markdown page to the file
        for page in markdown_pages:
            f.write(page + "\n\n")


if __name__ == "__main__":
    in_dir = Path("final_terms/docs")
    out_dir = Path("data/txt")
    # ensure the input directory exists
    if not in_dir.exists():
        raise FileNotFoundError(f"The directory {in_dir} does not exist.")
    # for every subdirectory in the input directory, convert HTML files to markdown
    for doc_name in tqdm(list(in_dir.iterdir())):
        if doc_name.is_dir():
            # convert HTML files in the subdirectory to markdown
            convert_html_to_markdown(in_dir, out_dir, doc_name.name)
