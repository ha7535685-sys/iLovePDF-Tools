import os
import re
import io
import fitz  # PyMuPDF
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def unspace_letters(text: str) -> str:
    """Normalize artificially spaced letters in PDF headings.
    e.g. 'C O N T A C T' -> 'CONTACT', 'E D U C A T I O N' -> 'EDUCATION', '2 0 2 6' -> '2026'.
    Preserves regular words like 'Capital University of Science & Technology'.
    """
    if not text:
        return text
    # Replace single alphanumeric characters separated by single spaces when part of an uppercase or digit word
    cleaned = re.sub(r'(?<=\b[A-Za-z0-9]) (?:(?=[A-Za-z0-9]\b)|(?=[A-Za-z0-9] ))', '', text)
    # Remove awkward tab runs within short text
    cleaned = re.sub(r'\t+', ' ', cleaned)
    return cleaned


def detect_page_columns(page: fitz.Page) -> list[tuple[float, float]]:
    """Detect vertical column bands in a PDF page based on text block bounding boxes and gutters.
    Returns a list of (x_min, x_max) intervals representing columns, or empty list if single-column.
    """
    page_width = page.rect.width
    page_height = page.rect.height
    blocks = page.get_text("blocks")
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    if len(text_blocks) < 5:
        return []

    # Filter to body blocks (excluding very top header or very bottom footer)
    mid_blocks = [b for b in text_blocks if b[1] >= page_height * 0.08 and b[3] <= page_height * 0.95]
    if len(mid_blocks) < 4:
        mid_blocks = text_blocks

    # 1. Test 3-column layout (e.g. landscape fee challans, 3-panel brochures)
    if page_width > 500:
        g1_min, g1_max = page_width * 0.28, page_width * 0.38
        g2_min, g2_max = page_width * 0.62, page_width * 0.72
        crossing_3col = [
            b for b in mid_blocks
            if (b[0] < g1_min and b[2] > g1_max) or (b[0] < g2_min and b[2] > g2_max)
        ]
        c1 = [b for b in mid_blocks if b[2] <= g1_max]
        c2 = [b for b in mid_blocks if b[0] >= g1_min and b[2] <= g2_max]
        c3 = [b for b in mid_blocks if b[0] >= g2_min]
        if len(crossing_3col) <= 2 and len(c1) >= 3 and len(c2) >= 3 and len(c3) >= 3:
            return [(0, g1_min), (g1_min, g2_min), (g2_min, page_width)]

    # 2. Test 2-column layout (e.g. 2-column resumes, research papers)
    best_gutter = None
    min_crossing = 999
    for split_pct in [0.25, 0.30, 0.33, 0.35, 0.40, 0.45, 0.50]:
        gutter_center = page_width * split_pct
        g_left = gutter_center - 15
        g_right = gutter_center + 15
        crossing = [b for b in mid_blocks if b[0] < g_left and b[2] > g_right]
        left = [b for b in mid_blocks if b[2] <= g_right]
        right = [b for b in mid_blocks if b[0] >= g_left]
        if len(crossing) == 0 and len(left) >= 3 and len(right) >= 3:
            best_gutter = (g_left, g_right)
            break
        elif len(crossing) < min_crossing and len(left) >= 4 and len(right) >= 4:
            min_crossing = len(crossing)
            if min_crossing <= 1:
                best_gutter = (g_left, g_right)

    if best_gutter:
        return [(0, best_gutter[0]), (best_gutter[1], page_width)]

    return []


def render_multicolumn_document(pdf_path: str, docx_path: str) -> bool:
    """Render a multi-column PDF into a beautifully structured Word document preserving
    independent parallel columns, font styling, headings, and images without text mixing.
    """
    doc_fitz = fitz.open(pdf_path)
    wdoc = docx.Document()

    for page_idx, page in enumerate(doc_fitz):
        page_w = page.rect.width
        page_h = page.rect.height
        is_landscape = page_w > page_h

        # Setup page section
        if page_idx == 0:
            section = wdoc.sections[0]
        else:
            section = wdoc.add_section()

        if is_landscape:
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width = Inches(11.0)
            section.page_height = Inches(8.5)
        else:
            section.orientation = WD_ORIENT.PORTRAIT
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)

        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.4)
        section.right_margin = Inches(0.4)

        cols = detect_page_columns(page)
        if not cols:
            # Fall back to 1-column if this page is single column
            cols = [(0, page_w)]

        # Extract text blocks with styling details
        page_dict = page.get_text("dict")
        raw_blocks = page_dict.get("blocks", [])

        text_blocks = []
        for b in raw_blocks:
            if b.get("type") == 0:  # text
                lines = b.get("lines", [])
                block_text = ""
                spans_list = []
                for line in lines:
                    for span in line.get("spans", []):
                        t = span.get("text", "")
                        if t:
                            spans_list.append(span)
                            block_text += t + " "
                    block_text += "\n"
                if block_text.strip():
                    bbox = b.get("bbox")
                    text_blocks.append({
                        "bbox": bbox,
                        "text": block_text.strip(),
                        "spans": spans_list,
                        "y0": bbox[1],
                        "y1": bbox[3],
                        "x0": bbox[0],
                        "x1": bbox[2],
                    })

        # Extract images on this page
        img_list = []
        try:
            for img_info in page.get_image_info(xrefs=True):
                xref = img_info.get("xref")
                if xref and xref > 0:
                    base_image = doc_fitz.extract_image(xref)
                    img_bytes = base_image.get("image")
                    if img_bytes:
                        img_list.append({
                            "bbox": img_info.get("bbox", (0, 0, 0, 0)),
                            "bytes": img_bytes,
                            "ext": base_image.get("ext", "png"),
                            "width": base_image.get("width", 100),
                            "height": base_image.get("height", 100),
                            "x0": img_info.get("bbox", (0, 0, 0, 0))[0],
                            "x1": img_info.get("bbox", (0, 0, 0, 0))[2],
                            "y0": img_info.get("bbox", (0, 0, 0, 0))[1],
                        })
        except Exception as e:
            print(f"Warning extracting images: {e}")

        num_cols = len(cols)

        if num_cols == 1:
            # Single-column page
            text_blocks.sort(key=lambda b: b["y0"])
            for b in text_blocks:
                _add_block_to_container(wdoc, b)
            continue

        # Distribute blocks into columns vs full-width header
        col_blocks = [[] for _ in range(num_cols)]
        col_images = [[] for _ in range(num_cols)]
        header_blocks = []
        header_images = []

        # Find header boundary: blocks near top that span across columns
        for b in text_blocks:
            placed = False
            for c_idx, (c_min, c_max) in enumerate(cols):
                x_center = (b["x0"] + b["x1"]) / 2.0
                if c_min <= x_center <= c_max or (b["x0"] >= c_min - 10 and b["x1"] <= c_max + 10):
                    col_blocks[c_idx].append(b)
                    placed = True
                    break
            if not placed:
                if b["y1"] < page_h * 0.35:
                    header_blocks.append(b)
                else:
                    closest_col = min(
                        range(num_cols),
                        key=lambda i: abs((b["x0"] + b["x1"]) / 2.0 - (cols[i][0] + cols[i][1]) / 2.0)
                    )
                    col_blocks[closest_col].append(b)

        # Distribute images
        for img in img_list:
            x_center = (img["x0"] + img["x1"]) / 2.0
            if img["y0"] < page_h * 0.25 and (img["x1"] - img["x0"]) > page_w * 0.4:
                header_images.append(img)
            else:
                closest_col = min(
                    range(num_cols),
                    key=lambda i: abs(x_center - (cols[i][0] + cols[i][1]) / 2.0)
                )
                col_images[closest_col].append(img)

        # Sort elements by Y coordinate
        header_blocks.sort(key=lambda b: b["y0"])
        for cb in col_blocks:
            cb.sort(key=lambda b: b["y0"])

        # Render Header Images & Blocks
        for img in header_images:
            try:
                p = wdoc.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run()
                run.add_picture(io.BytesIO(img["bytes"]), width=Inches(min(img["width"] / 72.0, 3.0)))
            except Exception:
                pass

        for b in header_blocks:
            _add_block_to_container(wdoc, b)

        # Render Columns via zero-border layout table
        avail_width = 10.2 if is_landscape else 7.7
        table = wdoc.add_table(rows=1, cols=num_cols)
        table.autofit = False

        # Apply zero borders
        tblPr = table._tbl.tblPr
        tblBorders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>\n'
            f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
            f'</w:tblBorders>'
        )
        tblPr.append(tblBorders)

        total_col_w = sum(c[1] - c[0] for c in cols)
        for c_idx, cell in enumerate(table.rows[0].cells):
            col_w_in = ((cols[c_idx][1] - cols[c_idx][0]) / total_col_w) * avail_width
            cell.width = Inches(col_w_in)

            # Add images for this column
            for img in col_images[c_idx]:
                try:
                    p = cell.add_paragraph()
                    p.paragraph_format.space_after = Pt(2)
                    run = p.add_run()
                    max_w = min(col_w_in * 0.9, img["width"] / 72.0)
                    run.add_picture(io.BytesIO(img["bytes"]), width=Inches(max(max_w, 0.5)))
                except Exception:
                    pass

            # Add text blocks for this column
            for b in col_blocks[c_idx]:
                _add_block_to_container(cell, b)

    doc_fitz.close()
    wdoc.save(docx_path)
    return True


def _add_block_to_container(container, b: dict):
    """Add a block with proper typography and heading normalization to a Word document or cell."""
    text = unspace_letters(b["text"])
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return

    p = container.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)

    # Determine dominant font size and bold from spans
    max_size = 10.0
    is_bold = False
    for s in b.get("spans", []):
        sz = s.get("size", 10.0)
        if sz > max_size:
            max_size = sz
        flags = s.get("flags", 0)
        font_name = s.get("font", "").lower()
        if (flags & 2) or "bold" in font_name or "black" in font_name:
            is_bold = True

    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.size = Pt(min(max_size, 22.0))
        # Detect headings
        if is_bold or (len(line) < 35 and line.isupper() and any(c.isalpha() for c in line)):
            run.font.bold = True
        if i < len(lines) - 1:
            p.add_run("\n")


def clean_docx_typography(docx_path: str):
    """Post-process a generated DOCX to fix unspaced headings and formatting artifacts."""
    try:
        doc = docx.Document(docx_path)
        modified = False

        for p in doc.paragraphs:
            cleaned = unspace_letters(p.text)
            if cleaned != p.text:
                p.text = cleaned
                modified = True

        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        cleaned = unspace_letters(p.text)
                        if cleaned != p.text:
                            p.text = cleaned
                            modified = True

        if modified:
            doc.save(docx_path)
    except Exception as e:
        print(f"clean_docx_typography warning: {e}")
