
import os
import re
import base64
import tempfile
import requests
from io import BytesIO
from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_bookmark(paragraph, bookmark_name):
    """
    Insert a bookmark start and end in the paragraph.
    This allows internal linking (TOC, cross-refs).
    """
    run = paragraph.add_run()
    tag = run._r
    start = OxmlElement('w:bookmarkStart')
    start.set(qn('w:id'), '0') # ID needs to be unique in real doc, but 0 often works for simple cases or needs management
    start.set(qn('w:name'), bookmark_name)
    tag.append(start)
    
    end = OxmlElement('w:bookmarkEnd')
    end.set(qn('w:id'), '0')
    tag.append(end)

def html_to_docx(doc, html_content, theme=0):
    """
    Parses HTML content and adds elements to the python-docx Document.
    Handles Headings, Paragraphs, Lists, Images, and custom 'Note' tables.
    """
    if not html_content: return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Pre-process: fix image src if relative or base64
    # (Assuming images are already handled/embedded mostly, but we need to decode base64)

    def process_node(node, parent_container=None):
        """
        Recursive function to process HTML nodes.
        parent_container: The docx object to add to (doc or table cell).
        If None, adds to 'doc'.
        """
        container = parent_container if parent_container else doc

        if isinstance(node, NavigableString):
            text = str(node).strip()
            if text:
                # If we are inside a paragraph context in HTML (like <span>), 
                # python-docx doesn't easily support inline appending to *current* paragraph 
                # without passing the paragraph object down.
                # For simplicity in this v1, we treats top-level text as paragraph.
                # If parent is a paragraph-like tag (p, span), we might need logic.
                pass 
            return

        if isinstance(node, Tag):
            tag = node.name.lower()
            
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag[1])
                text = node.get_text(strip=True)
                if text:
                    container.add_heading(text, level=level)
            
            elif tag == 'p':
                p = container.add_paragraph()
                process_inline_content(p, node)
                
                # Check for alignment
                style = node.get('style', '')
                if 'text-align: center' in style:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif 'text-align: right' in style:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif 'text-align: justify' in style:
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            elif tag in ['ul', 'ol']:
                style = 'List Bullet' if tag == 'ul' else 'List Number'
                for li in node.find_all('li', recursive=False):
                    p = container.add_paragraph(style=style)
                    process_inline_content(p, li)

            elif tag == 'img':
                handle_image(container, node)

            elif tag == 'table':
                handle_table(container, node)
                
            elif tag == 'div':
                 # Treat div as container, just recurse
                 for child in node.children:
                     process_node(child, container)
            
            elif tag == 'hr':
                # Add horizontal rule (border bottom on paragraph)
                p = container.add_paragraph()
                pPr = p._element.get_or_add_pPr()
                # pBdr might not be exposed, create manually
                pBdr = OxmlElement('w:pBdr')
                bottom = OxmlElement('w:bottom')
                bottom.set(qn('w:val'), 'single')
                bottom.set(qn('w:sz'), '6')
                bottom.set(qn('w:space'), '1')
                bottom.set(qn('w:color'), 'auto')
                pBdr.append(bottom)
                pPr.append(pBdr)

    def process_inline_content(paragraph, html_element):
        """
        Extracts text and applies inline styles (bold, italic, color) to runs.
        """
        for child in html_element.children:
            if isinstance(child, NavigableString):
                text = str(child)
                # Naive cleanup of excessive whitespace if needed, but keep some
                if text:
                    paragraph.add_run(text)
            elif isinstance(child, Tag):
                tag = child.name.lower()
                if tag == 'br':
                    paragraph.add_run().add_break()
                elif tag == 'img':
                    # Inline images are tricky in docx, often added as separate block
                    # For now, treat as block for stability
                    handle_image(doc, child) 
                else:
                    # Recursive for nested spans/b/i
                    # Capture the start of this run to apply styles
                    run = paragraph.add_run()
                    run.text = child.get_text() # Flatten text for now to avoid huge complexity?
                    # Ideally we recurse, but python-docx runs are linear.
                    # Simple version:
                    
                    if tag in ['b', 'strong']:
                        run.bold = True
                    if tag in ['i', 'em']:
                        run.italic = True
                    if tag in ['u', 'ins']:
                        run.underline = True
                    if tag in ['s', 'del', 'strike']:
                        run.font.strike = True
                    
                    # Color handling
                    style = child.get('style', '')
                    color_match = re.search(r'color:\s*#([0-9a-fA-F]{6})', style)
                    if color_match:
                         # apply color
                         hex_color = color_match.group(1)
                         run.font.color.rgb = RGBColor(int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16))

    def handle_image(container, img_tag):
        src = img_tag.get('src')
        if not src: return

        try:
            image_stream = None
            if src.startswith('data:image'):
                # Base64
                header, encoded = src.split(',', 1)
                data = base64.b64decode(encoded)
                image_stream = BytesIO(data)
            elif src.startswith('http'):
                # URL
                resp = requests.get(src, timeout=5)
                if resp.status_code == 200:
                   image_stream = BytesIO(resp.content)
            
            if image_stream:
                # Add picture with reasonable width limit
                container.add_picture(image_stream, width=Inches(5.0))
        except Exception as e:
            print(f"Error adding image: {e}")
            container.add_paragraph(f"[Image: {src[:20]}...]")

    def handle_table(container, table_tag):
        # Check if this is a "Note Box" or Code Block (often 1x1 table style)
        rows = table_tag.find_all('tr')
        if not rows: return
        
        # Create Docx Table
        num_rows = len(rows)
        # Find max cols
        max_cols = 0
        for r in rows:
            cols = r.find_all(['td', 'th'])
            max_cols = max(max_cols, len(cols))
        
        if max_cols == 0: return

        docx_table = container.add_table(rows=num_rows, cols=max_cols)
        docx_table.style = 'Table Grid'
        
        # Check for background color in style (Note Box detection)
        style = table_tag.get('style', '')
        bg_color = None
        if 'background-color' in style:
             match = re.search(r'background-color:\s*#([0-9a-fA-F]{6})', style)
             if match:
                 bg_color = match.group(1)

        for i, row in enumerate(rows):
            cols = row.find_all(['td', 'th'])
            for j, col in enumerate(cols):
                cell = docx_table.cell(i, j)
                # Recurse process content into cell
                # We can just process children into the cell's paragraphs
                # Clear default paragraph
                cell._element.clear_content()
                
                for child in col.children:
                    process_node(child, cell)
                
                # Apply Cell Background if needed
                if bg_color:
                    set_cell_background(cell, bg_color)

    # Start processing soup
    # Iterate over top-level elements
    for child in soup.body.children if soup.body else soup.children:
        process_node(child)

def set_cell_background(cell, hex_color):
    """
    Set background color of a table cell.
    """
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def export_note_to_docx(note, output_path):
    doc = Document()
    
    # Title
    doc.add_heading(note.title, 0)
    
    # Metadata
    p = doc.add_paragraph()
    run = p.add_run(f"Created: {note.created_at}")
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(128, 128, 128)
    
    doc.add_paragraph() # Spacer
    
    # Content
    html_to_docx(doc, note.content)
    
    doc.save(output_path)
    return True

def export_folder_to_docx(folder, output_path, progress_callback=None):
    doc = Document()
    
    # Folder Title Page
    doc.add_heading(folder.name, 0)
    doc.add_paragraph("Folder Export").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    
    # Iterate Notes
    notes = sorted(folder.notes, key=lambda n: n.created_at) # Sort by creation or custom order
    total = len(notes)
    
    for i, note in enumerate(notes):
        if progress_callback: progress_callback(i, total)
        
        doc.add_heading(note.title, 1)
        html_to_docx(doc, note.content)
        doc.add_page_break()
        
    doc.save(output_path)
    return True
