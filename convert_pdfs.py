import argparse
from pathlib import Path
from docling.document_converter import DocumentConverter


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to markdown text files."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/pdf",
        help="Directory containing PDF files to convert."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/txt",
        help="Directory to save converted markdown files."
    )
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # convert each PDF file in the input using docling
    for pdf_file in input_dir.glob("*.pdf"):
        print(f"Converting {pdf_file.name} to markdown...")
        result = DocumentConverter().convert(source=str(pdf_file))
        markdown = result.document.export_to_markdown()

        # save markdown to a file
        output_file = output_dir / f"{pdf_file.stem}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Saved converted file to {output_file}")


if __name__ == "__main__":
    main()
