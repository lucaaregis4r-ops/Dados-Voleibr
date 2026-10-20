"""Script to inspect PDF structure using PyMuPDF (fitz) and pdfplumber."""

import sys
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber

def inspect_pdf(pdf_path: Path, output_text_path: Path):
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"=== Inspecting PDF: {pdf_path.name} ===")
    
    # 1. PyMuPDF analysis
    doc = fitz.open(pdf_path)
    print(f"Total Pages (PyMuPDF): {len(doc)}")
    
    extracted_text_blocks = []
    extracted_text_blocks.append(f"=== PyMuPDF Extraction for {pdf_path.name} (Pages: {len(doc)}) ===\n")

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text")
        extracted_text_blocks.append(f"--- PAGE {page_idx + 1} (PyMuPDF Text) ---\n")
        extracted_text_blocks.append(text)
        extracted_text_blocks.append("\n")

        # Blocks with coordinates
        blocks = page.get_text("blocks")
        extracted_text_blocks.append(f"--- PAGE {page_idx + 1} (PyMuPDF Blocks: {len(blocks)}) ---\n")
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            extracted_text_blocks.append(f"Block {b[5]} [bbox: ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f})]:\n{b[4]}\n")

    # 2. pdfplumber analysis (extracting tables and layout text)
    extracted_text_blocks.append("\n=== pdfplumber Extraction ===\n")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total Pages (pdfplumber): {len(pdf.pages)}")
        for page_idx, page in enumerate(pdf.pages):
            extracted_text_blocks.append(f"--- PAGE {page_idx + 1} (pdfplumber extract_text layout=True) ---\n")
            layout_text = page.extract_text(layout=True)
            extracted_text_blocks.append(layout_text or "[No text]")
            extracted_text_blocks.append("\n\n")

            tables = page.extract_tables()
            extracted_text_blocks.append(f"--- PAGE {page_idx + 1} (pdfplumber extract_tables: {len(tables)}) ---\n")
            for t_idx, table in enumerate(tables):
                extracted_text_blocks.append(f"Table {t_idx + 1} ({len(table)} rows):\n")
                for row in table:
                    clean_row = [c.replace("\n", " ") if c else "" for c in row]
                    extracted_text_blocks.append(f"{clean_row}\n")
                extracted_text_blocks.append("\n")

    output_text_path.parent.mkdir(parents=True, exist_ok=True)
    full_output = "".join(extracted_text_blocks)
    output_text_path.write_text(full_output, encoding="utf-8")
    print(f"Extraction saved to {output_text_path} ({len(full_output)} chars)")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    pdf_file = base_dir / "data" / "raw" / "reports" / "2590834.pdf"
    out_file = base_dir / "data" / "processed" / "2590834_raw_text.txt"
    inspect_pdf(pdf_file, out_file)
