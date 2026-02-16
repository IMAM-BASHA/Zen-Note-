from PyQt6.QtGui import QTextDocument, QPageSize, QAbstractTextDocumentLayout, QPageLayout, QFont, QPainter, QImage
from PyQt6.QtCore import QSizeF, Qt, QMarginsF, QRectF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter

import logging
import re
import requests
import base64
from urllib.parse import quote
from datetime import datetime
from util.logger import logger

# Cache for emoji data URIs to avoid redundant network calls
EMOJI_CACHE = {}

from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_emoji_svg(emoji):
    """Worker function to fetch a single emoji SVG."""
    if emoji in EMOJI_CACHE:
        return emoji, EMOJI_CACHE[emoji]
        
    try:
        hex_code = '-'.join(f'{ord(c):x}' for c in emoji)
        svg_url = f'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/{hex_code}.svg'
        response = requests.get(svg_url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            svg_data = response.text
            b64_data = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
            img_tag = f'<img src="data:image/svg+xml;base64,{b64_data}" width="18" height="18" style="vertical-align: middle;">'
            return emoji, img_tag
    except Exception:
        pass
    return emoji, None

def process_html_emojis(html):
    """Replaces unicode emojis in HTML with high-fidelity SVGs using parallel fetching."""
    if not html: return html
    emoji_pattern = r'([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\u2600-\u26FF\u2700-\u27BF])'
    needed_emojis = set(re.findall(emoji_pattern, html))
    missing_emojis = [e for e in needed_emojis if e not in EMOJI_CACHE]
    
    if missing_emojis:
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_emoji = {executor.submit(fetch_emoji_svg, emoji): emoji for emoji in missing_emojis}
            for future in as_completed(future_to_emoji):
                emoji, img_tag = future.result()
                if img_tag:
                    EMOJI_CACHE[emoji] = img_tag
    
    return re.sub(emoji_pattern, lambda m: EMOJI_CACHE.get(m.group(1), m.group(1)), html)

# --- NEW HELPERS ---

def scan_and_inject_toc(html_content, unique_prefix="", note_index=None):
    """
    Scans HTML for Level Boxes ([1.1], [1.1.1]).
    Injects <a name="..."> anchors into the NUMBER CELL only.
    Use manual lookahead to find content for TOC to avoid destroying HTML structure.
    """
    if not html_content:
        return [], html_content
        
    toc_items = []
    
    def make_anchor(prefix, idx):
        return f"toc_{prefix}_{idx}"
    
    counter = 0
    l1_counter = 0
    l2_counter = 0
    
    # NEW PATTERN: Target ONLY the cell containing the number [1.1]
    # We do NOT capture the next cell in the replacement group to ensure we don't accidentally delete it.
    level_pattern = re.compile(
        r'(<td[^>]*>.*?)(\[\s*(\d+(?:\.\d+)+)\s*\])(.*?</td>)',
        re.IGNORECASE | re.DOTALL
    )
    
    def level_sub(m):
        nonlocal counter, l1_counter, l2_counter
        
        # Original Match Parts
        cell_pre = m.group(1)   # <td...>...
        full_bracket = m.group(2) # [1.1]
        number_str = m.group(3) # 1.1
        cell_post = m.group(4)  # ...</td>
        
        # Calculate Logic
        dots = number_str.count('.')
        toc_level = dots
        if toc_level < 1: toc_level = 1
        
        # Dynamic Renumbering Logic
        display_number = number_str
        if note_index is not None:
            if toc_level == 1:
                l1_counter += 1
                l2_counter = 0 # Reset sub-level
                display_number = f"{note_index}.{l1_counter}"
            elif toc_level >= 2:
                l2_counter += 1
                base_l1 = l1_counter if l1_counter > 0 else 1
                display_number = f"{note_index}.{base_l1}.{l2_counter}"
        
        # --- ROBUST CONTENT EXTRACTION (Peek Ahead) ---
        # We need to find the text in the *next* cell (Content Cell)
        # m.end() is the end of the number cell </td>
        # We search forward in the original string for the next <td>...</td>
        remaining_html = m.string[m.end():]
        # Look for first <td>...</td>
        content_match = re.search(r'<td[^>]*>(.*?)</td>', remaining_html, re.IGNORECASE | re.DOTALL)
        
        clean_text = "Content" # Fallback
        if content_match:
            raw_content = content_match.group(1)
            # Remove tags to get plain text for TOC
            clean_text = re.sub(r'<[^>]+>', '', raw_content).replace('&nbsp;', ' ').strip()
        
        display_text = f"{display_number} {clean_text}"
        
        counter += 1
        anchor = make_anchor(unique_prefix, counter)
        
        toc_items.append({
            'level': toc_level,
            'text': display_text,
            'anchor': anchor,
            'is_level_box': True 
        })
        
        # Inject anchor & UPDATE NUMBER in HTML
        new_bracket_content = f"[{display_number}]"
        new_bracket_html = f'<a name="{anchor}"></a>{new_bracket_content}'
        
        # We return ONLY the modified number cell. The rest of the HTML (content cell) remains untouched.
        return f'{cell_pre}{new_bracket_html}{cell_post}'
        
    # Uses re.sub on the number cell only
    processed_html = level_pattern.sub(level_sub, html_content)
    return toc_items, processed_html

def enforce_level_box_styles(html_content, debug=False):
    """
    Enforce proper styling for level 1 and level 2 boxes.
    Qt-compatible version using BeautifulSoup.
    
    Args:
        html_content: Raw HTML string
        debug: If True, print diagnostic information
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("WARNING: BeautifulSoup not available, skipping level box styling")
        return html_content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        print(f"ERROR parsing HTML: {e}")
        return html_content

    import re

    LEVEL_1_COLOR = '#ffffe0'  # Light yellow
    LEVEL_2_COLOR = '#aaffff'  # Light cyan

    # Qt-compatible clean CSS (No !important, no double semicolons)
    def get_table_style(bg_color, margin_left=0):
        return (
            f"margin-top:8px; "
            f"margin-bottom:8px; "
            f"margin-left:{margin_left}px; "
            f"margin-right:0px; "
            f"background-color:{bg_color}; "
            f"border:1px solid #cccccc; "
            f"border-collapse:collapse;"
        )

    def get_cell_style(bg_color):
        return (
            f"background-color:{bg_color}; "
            f"padding:8px; "
            f"border:none; "
            f"color:#000000;"
        )

    processed_count = {'level_1': 0, 'level_2': 0}

    for table in soup.find_all('table'):
        first_cell = table.find('td')
        if not first_cell:
            continue
            
        cell_text = first_cell.get_text(strip=True)
        # Match [5] or [5.1] or [5.1.1]
        match = re.match(r'\[(\d+(?:\.\d+)*)\]', cell_text)
        if not match:
            continue
        
        level_num = match.group(1)
        parts = level_num.split('.')
        
        if len(parts) == 1:
            # Level 1 (e.g. [5])
            color = LEVEL_1_COLOR
            margin_left = 0
            processed_count['level_1'] += 1
        else:
            # Level 2+ (e.g. [5.1], [5.1.1])
            color = LEVEL_2_COLOR
            margin_left = 40
            processed_count['level_2'] += 1
        
        # Apply styles
        table['style'] = get_table_style(color, margin_left)
        table['border'] = '0'
        table['cellspacing'] = '0'
        table['cellpadding'] = '8'
        table['width'] = '100%'
        
        # Apply styles to all cells
        for td in table.find_all('td'):
            td['style'] = get_cell_style(color)
            
            # Force black text on ALL text containers to override theme white
            # We use !important because the global theme uses !important
            black_style = "color:#000000 !important;"
            
            tags_to_fix = ['span', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'b', 'strong', 'i', 'em', 'u']
            for tag_name in tags_to_fix:
                for element in td.find_all(tag_name):
                    curr_style = element.get('style', '')
                    # Avoid double-appending if already present (simple check)
                    if 'color:#000000' not in curr_style and 'color: #000000' not in curr_style:
                         element['style'] = f"{curr_style}; {black_style}"

            # Ensure links are visible (Dark Blue instead of Theme Light Blue)
            # Theme Light Blue (#66b3ff) is invisible on Yellow. We use Standard Blue (#007ACC)
            link_style = "color:#007ACC !important;"
            for a in td.find_all('a'):
                curr_style = a.get('style', '')
                if 'color:' not in curr_style:
                    a['style'] = f"{curr_style}; {link_style}"
        
        # --- NEW: Add "Back to TOC" link AFTER the table ---
        if color == LEVEL_1_COLOR or color == LEVEL_2_COLOR:
            try:
                # Create container div for link
                link_div = soup.new_tag("div")
                link_div['style'] = "text-align: right; margin-top: 2px; margin-bottom: 8px;"
                
                # Create anchor
                back_link = soup.new_tag("a", href="#toc_anchor")
                back_link.string = "↑ Back to TOC"
                back_link['style'] = "color: #007ACC; text-decoration: none; font-size: 10pt;"
                
                link_div.append(back_link)
                
                # Insert after table
                table.insert_after(link_div)
            except Exception as e:
                print(f"Error inserting TOC link: {e}")
            

    if debug:
        print(f"Styled {processed_count['level_1']} Level 1 boxes")
        print(f"Styled {processed_count['level_2']} Level 2 boxes")
    
    try:
        return str(soup)
    except Exception as e:
        print(f"ERROR serializing HTML: {e}")
        return html_content

def generate_toc_html(toc_items, theme):
    """Generates HTML block for TOC."""
    if not toc_items: return ""
    
    if theme == 1:
        color = "#ffffff"
        link_color = "#66b3ff"
    elif theme == 2:
        color = "#433422"
        link_color = "#8e5c2e"
    else:
        color = "#000000"
        link_color = "#007ACC"
    
    html = [f'<div id="toc_anchor" class="pdf-toc" style="margin-bottom: 20px;">']
    html.append(f'<h2 style="color: {color}; border-bottom: 2px solid #ccc;">Table of Contents</h2>')
    html.append('<ul style="list-style-type: none; padding-left: 0;">')
    
    for item in toc_items:
        level = item['level']
        indent = (level - 1) * 20
        font_weight = "bold" if level == 1 else "normal"
        text = item['text']
        anchor = item['anchor']
        
        html.append(f'<li style="margin-left: {indent}px; margin-bottom: 5px;">')
        html.append(f'<a href="#{anchor}" style="text-decoration: none; color: {link_color}; font-weight: {font_weight};">{text}</a>')
        html.append('</li>')
        
    html.append('</ul></div><hr/><br/>')
    return "".join(html)



def process_internal_links(html_content, available_note_ids, theme=0):
    """
    Rewrites internal note:// links for PDF export.
    - If target note is in available_note_ids, rewrites to internal anchor #note_<uuid>.
    - If not found, styles as broken/external link.
    """
    if not html_content: return html_content
    
    import re
    # Match href="note://UUID"
    # We use a function to check validity
    
    def replacer(match):
        # match.group(0) is full match, we want to replace the href part
        # Regex: href=["']note://(...)["']
        
        quote = match.group(1)
        note_id = match.group(2)
        
        if note_id in available_note_ids:
            # Valid internal link
            return f'href={quote}#note_{note_id}{quote}'
        else:
            # External or missing link
            # We treat it as void/broken for the PDF context
            # Optional: Add visual cue
            return f'href={quote}#void{quote} style={quote}color: gray; text-decoration: line-through; cursor: not-allowed;{quote} title={quote}Note not included in this export{quote}'

    # Regex to find the HREF attribute specifically
    pattern = r'href=([\"\'])note://([a-fA-F0-9\-]+)\1'
    return re.sub(pattern, replacer, html_content)

# --- END NEW HELPERS ---

def _print_document_with_footer(doc, printer, footer_text=None, progress_callback=None, theme=0):
    painter = QPainter(printer)
    # Enable High Sharpness Render Hints
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    layout_rect = printer.pageRect(QPrinter.Unit.Point)
    device_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
    scale = 1.0
    if layout_rect.width() > 0:
        scale = device_rect.width() / layout_rect.width()
    else:
        layout_rect = QRectF(0, 0, 595, 842)
    
    doc.setPageSize(QSizeF(layout_rect.width(), layout_rect.height()))
    page_count = doc.pageCount()
    
    from PyQt6.QtGui import QColor, QBrush
    
    for i in range(page_count):
        if progress_callback and callable(progress_callback):
            progress_callback(i + 1, page_count)
            QApplication.processEvents()

        if i > 0:
            printer.newPage()

        if theme != 0: # Anything other than Light
            painter.save()
            page_rect_dev = printer.pageRect(QPrinter.Unit.DevicePixel)
            paper_rect_dev = printer.paperRect(QPrinter.Unit.DevicePixel)
            left_margin = page_rect_dev.left() - paper_rect_dev.left()
            top_margin = page_rect_dev.top() - paper_rect_dev.top()
            full_page_rect = QRectF(-left_margin, -top_margin, paper_rect_dev.width(), paper_rect_dev.height())
            
            if theme == 1:
                bg_color = QColor("#1e1e1e")
            elif theme == 2:
                bg_color = QColor("#f5f0e8")
            elif isinstance(theme, str) and theme.startswith("#"):
                bg_color = QColor(theme)
            else:
                bg_color = Qt.GlobalColor.white

            painter.fillRect(full_page_rect, QBrush(bg_color))
            painter.restore()

        painter.save()
        painter.scale(scale, scale)
        painter.translate(0, -i * layout_rect.height())
        clip_rect = QRectF(0, i * layout_rect.height(), layout_rect.width(), layout_rect.height())
        doc.drawContents(painter, clip_rect)
        painter.restore()

        painter.save()
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        if theme == 1:
            painter.setPen(Qt.GlobalColor.lightGray)
        elif theme == 2:
            painter.setPen(QColor("#8e5c2e")) # Brownish for sepia
        elif isinstance(theme, str) and theme.startswith("#"):
            # Auto-detect brightness for footer text
            c = QColor(theme)
            brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
            if brightness < 128:
                painter.setPen(Qt.GlobalColor.lightGray)
            else:
                painter.setPen(Qt.GlobalColor.darkGray)
        else:
            painter.setPen(Qt.GlobalColor.gray)

        display_text = f"Page {i + 1} of {page_count}"
        if footer_text:
            display_text = f"{footer_text} - {display_text}"
            
        painter.drawText(device_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, display_text)
        painter.restore()
        
    painter.end()

def export_note_to_pdf(note, output_path, progress_callback=None, theme=0):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setColorMode(QPrinter.ColorMode.Color)
    printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
    page_metrics = {
        'usable_width': int(page_rect.width()),
        'usable_height': int(page_rect.height()) - 50
    }

    whiteboard_images = getattr(note, 'whiteboard_images', {})
    
    html_content = process_html_emojis(note.content)
    html_content = cleanup_editor_artifacts(html_content)
    html_content = sanitize_note_tables(html_content)
    html_content = process_images_for_pdf(html_content, whiteboard_images, page_metrics, theme)
    html_content = apply_theme_to_html(html_content, theme)
    html_content = force_code_block_styles(html_content)

    # --- TOC & INDENTATION LOGIC ---
    import uuid
    # Calculate Note Position for Renumbering
    note_pos = 1
    if hasattr(note, 'folder') and note.folder:
        try:
            from models.note import Note
            sorted_notes = sorted(note.folder.notes, key=Note.sort_key)
            for i, n in enumerate(sorted_notes, 1):
                if n.id == note.id:
                    note_pos = i
                    break
        except Exception:
            pass

    # Inject Anchors
    toc_items, html_content = scan_and_inject_toc(html_content, unique_prefix=f"note_{note.id}_{uuid.uuid4().hex[:4]}", note_index=note_pos)
    
    # Enforce Level Box Styles (Contrast Fix)
    import os
    debug_mode = os.environ.get('PDF_EXPORT_DEBUG', '').lower() == 'true'
    html_content = enforce_level_box_styles(html_content, debug=debug_mode)
    
    # Prepend TOC
    if toc_items:
        toc_html = generate_toc_html(toc_items, theme)
        html_content = toc_html + html_content
    # -------------------------------

    if debug_mode:
        try:
            debug_path = output_path.replace('.pdf', '_debug.html')
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"DEBUG EXPORT: HTML dumped to {debug_path}")
        except Exception as e:
            print(f"DEBUG EXPORT ERROR: {e}")

    doc = QTextDocument()
    doc.setDocumentMargin(5)
    doc.setDefaultFont(QFont("Segoe UI", 7))
    doc.setHtml(html_content)

    logger.info(f"Exporting note '{note.title}' to {output_path} (Native + Footer)...")
    _print_document_with_footer(doc, printer, note.title, progress_callback, theme)

def cleanup_editor_artifacts(html):
    """
    Removes editor-only artifacts like image control tables using BeautifulSoup.
    Replaces the control table with just the image.
    """
    if not html: return html
    if 'action://' not in html: return html

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all action links (Edit/Delete buttons)
        # We process them to find their wrapper tables
        action_links = soup.find_all('a', href=re.compile(r'^action://'))
        
        # Use a set to track tables we've already handled to avoid double-processing
        handled_tables = set()
        
        for link in action_links:
            # Find the nearest parent table
            parent_table = link.find_parent('table')
            
            if parent_table and parent_table not in handled_tables:
                # Security Check: Ensure this is actually an image wrapper table
                # It should contain an image.
                img = parent_table.find('img')
                if img:
                    # Replace the WHOLE table with just the image
                    # This removes the buttons and the wrapper table
                    parent_table.replace_with(img)
                    handled_tables.add(parent_table)
        
        return str(soup)
        
    except ImportError:
        # Fallback to Regex if BS4 missing (though strict regex is risky, we try to be non-greedy)
        # We tighten the regex to avoid matching across Note Blocks
        # Match <table...>...<img...>...action://...</table> but ensure no nested tables inside?
        # Actually, the original bug was likely matching a parent table.
        # We'll use a safer regex that forbids internal <table> tags to prevent greedy eating
        pattern = r'<table[^>]*>((?:(?!<table).)*?action://(?:(?!<table).)*?)</table>'
        
        def replacer(match):
            content = match.group(1)
            # extracting image from content
            m_img = re.search(r'(<img[^>]+>)', content)
            if m_img: return m_img.group(1)
            return match.group(0) # Fail safe
            
        cleaned = re.sub(pattern, replacer, html, flags=re.DOTALL | re.IGNORECASE)
        return cleaned
    except Exception as e:
        print(f"Error in cleanup_editor_artifacts: {e}")
        return html

def sanitize_note_tables(html):
    """
    Retroactive Fix: Removes <thead>/<tbody> tags from Note tables to prevent
    header repetition on new pages in PDF export.
    Target specifically tables containing "Note:" in the header.
    """
    if not html: return html
    if '<thead>' not in html: return html

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all tables with thead
        tables_with_thead = soup.find_all('table')
        
        modified = False
        for table in tables_with_thead:
            thead = table.find('thead')
            if thead:
                # Check if it's likely a Note box (contains "Note:")
                # We check the text of the thead
                header_text = thead.get_text()
                if "Note:" in header_text:
                    # Unwrap thead (remove tag, keep content)
                    thead.unwrap()
                    
                    # Also unwrap tbody if present, to flatten structure completely
                    tbody = table.find('tbody')
                    if tbody:
                        tbody.unwrap()
                    modified = True
        
        if modified:
            return str(soup)
        return html
        
    except ImportError:
        # Fallback Regex (Less precise, removes all theads/tbodies)
        # Only apply if "Note:" is arguably present? Regex is hard to scope to table.
        # We'll just strip all thead/tbody tags if BS4 fails, assuming the user likely
        # doesn't want repeating headers for *any* table in this context (it's a note app).
        import re
        html = re.sub(r'</?thead[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'</?tbody[^>]*>', '', html, flags=re.IGNORECASE)
        return html
    except Exception as e:
        print(f"Error in sanitize_note_tables: {e}")
        return html

def apply_theme_to_html(html, theme=0):
    if theme == 1:
        theme_styles = """
        * { margin: 0; padding: 0; }
        html, body {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0 !important; padding: 0 !important;
        }
        .dark-page-wrapper {
            background-color: #1e1e1e !important; color: #ffffff !important;
            padding: 15px; min-height: 100vh;
        }
        h1, h2, h3, h4, h5, h6 { color: #ffffff !important; border-bottom: 2px solid #444444 !important; }
        p, div, span { color: #ffffff !important; }
        code, pre { background-color: #2d2d2d !important; color: #f8f8f2 !important; border: 1px solid #444444 !important; }
        table { background-color: #2d2d2d !important; color: #ffffff !important; border: 1px solid #444444 !important; width: 100% !important; border-collapse: collapse !important; }
        thead { display: table-header-group !important; }
        tr { page-break-inside: avoid !important; }
        td, th { background-color: #2d2d2d !important; color: #ffffff !important; border: 1px solid #444444 !important; padding: 8px !important; word-wrap: break-word !important; }
        hr { border-color: #444444 !important; }
        a { color: #66b3ff !important; }
        img { border: none !important; max-width: 100% !important; height: auto !important; object-fit: contain !important; display: block; margin: 5px auto; page-break-inside: avoid !important; }
        table.code-block-table { background-color: #2F3437 !important; border: 1px solid #373c3f !important; border-radius: 6px !important; margin: 10px 0 !important; border-collapse: separate !important; }
        td.code-block-cell { background-color: #2F3437 !important; color: #f8f8f2 !important; border: none !important; padding: 15px !important; }
        pre.code-block-pre { background-color: transparent !important; color: #f8f8f2 !important; border: none !important; }
        """
        try:
            from pygments.formatters import HtmlFormatter
            formatter = HtmlFormatter(style='monokai', nowrap=True)
            pygments_css = formatter.get_style_defs('.highlight')
            pygments_css = pygments_css.replace(";", " !important;") 
            theme_styles += "\n" + pygments_css
        except ImportError:
            pass

    elif isinstance(theme, str) and theme.startswith("#"):
        # Custom Color Theme
        from PyQt6.QtGui import QColor
        bg_color = theme
        c = QColor(theme)
        # Determine text color based on brightness
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        text_color = "#ffffff" if brightness < 128 else "#000000"
        border_color = "#444444" if brightness < 128 else "#cccccc"
        code_bg = "#2d2d2d" if brightness < 128 else "#f7f6f3"
        code_text = "#f8f8f2" if brightness < 128 else "#37352f"
        
        theme_styles = f"""
        * {{ margin: 0; padding: 0; }}
        html, body {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0 !important; padding: 0 !important;
            text-rendering: optimizeLegibility !important;
            -webkit-font-smoothing: antialiased !important;
        }}
        .custom-page-wrapper {{
            background-color: {bg_color} !important; color: {text_color} !important;
            padding: 15px; min-height: 100vh;
        }}
        h1, h2, h3, h4, h5, h6 {{ color: {text_color} !important; border-bottom: 2px solid {border_color} !important; }}
        p, div, span {{ color: {text_color} !important; }}
        code, pre {{ background-color: {code_bg} !important; color: {code_text} !important; border: 1px solid {border_color} !important; }}
        table {{ background-color: transparent !important; color: {text_color} !important; border: 1px solid {border_color} !important; width: 100% !important; border-collapse: collapse !important; }}
        thead {{ display: table-header-group !important; }}
        tr {{ page-break-inside: avoid !important; }}
        td, th {{ background-color: transparent !important; color: {text_color} !important; border: 1px solid {border_color} !important; padding: 8px !important; word-wrap: break-word !important; }}
        hr {{ border-color: {border_color} !important; }}
        a {{ color: {"#66b3ff" if brightness < 128 else "#007ACC"} !important; }}
        img {{ border: none !important; max-width: 100% !important; height: auto !important; object-fit: contain !important; display: block; margin: 5px auto; page-break-inside: avoid !important; }}
        
        /* Code Block Specifics */
        table.code-block-table {{ background-color: {code_bg} !important; border: 1px solid {border_color} !important; border-radius: 6px !important; margin: 10px 0 !important; border-collapse: separate !important; }}
        td.code-block-cell {{ background-color: {code_bg} !important; color: {code_text} !important; border: none !important; padding: 15px !important; }}
        pre.code-block-pre {{ background-color: transparent !important; color: {code_text} !important; border: none !important; }}
        """
        try:
            from pygments.formatters import HtmlFormatter
            py_style = 'monokai' if brightness < 128 else 'default'
            formatter = HtmlFormatter(style=py_style, nowrap=True)
            pygments_css = formatter.get_style_defs('.highlight')
            pygments_css = pygments_css.replace(";", " !important;")
            theme_styles += "\n" + pygments_css
        except ImportError:
            pass
            
    elif theme == 2: # Sepia
        theme_styles = """
        * { margin: 0; padding: 0; }
            background-color: #f5f0e8 !important;
            color: #433422 !important;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0 !important; padding: 0 !important;
            text-rendering: optimizeLegibility !important;
            -webkit-font-smoothing: antialiased !important;
        }
        .sepia-page-wrapper {
            background-color: #f5f0e8 !important; color: #433422 !important;
            padding: 15px; min-height: 100vh;
        }
        h1, h2, h3, h4, h5, h6 { color: #433422 !important; border-bottom: 2px solid #dcd1bc !important; }
        p, div, span { color: #433422 !important; }
        code, pre { background-color: #ede6d9 !important; color: #433422 !important; border: 1px solid #dcd1bc !important; }
        table { background-color: #f5f0e8 !important; color: #433422 !important; border: 1px solid #dcd1bc !important; width: 100% !important; border-collapse: collapse !important; }
        thead { display: table-header-group !important; }
        tr { page-break-inside: avoid !important; }
        td, th { background-color: #f5f0e8 !important; color: #433422 !important; border: 1px solid #dcd1bc !important; padding: 8px !important; word-wrap: break-word !important; }
        hr { border-color: #dcd1bc !important; }
        a { color: #8e5c2e !important; }
        img { border: none !important; max-width: 100% !important; height: auto !important; object-fit: contain !important; display: block; margin: 5px auto; page-break-inside: avoid !important; }
        table.code-block-table { background-color: #ede6d9 !important; border: 1px solid #dcd1bc !important; border-radius: 6px !important; margin: 10px 0 !important; border-collapse: separate !important; }
        td.code-block-cell { background-color: #ede6d9 !important; color: #433422 !important; border: none !important; padding: 15px !important; }
        pre.code-block-pre { background-color: transparent !important; color: #433422 !important; border: none !important; }
        """
        try:
            from pygments.formatters import HtmlFormatter
            formatter = HtmlFormatter(style='friendly', nowrap=True) # Friendly style for sepia
            pygments_css = formatter.get_style_defs('.highlight')
            pygments_css = pygments_css.replace(";", " !important;")
            theme_styles += "\n" + pygments_css
        except ImportError:
            pass
            
    else:
        theme_styles = """
        body { 
            background-color: #ffffff !important; 
            color: #000000 !important; 
            font-family: 'Segoe UI', Arial, sans-serif; 
            text-rendering: optimizeLegibility !important;
            -webkit-font-smoothing: antialiased !important;
        }
        h1, h2, h3, h4, h5, h6 { color: #000000 !important; }
        p, div, span { color: #000000 !important; }
        code, pre { background-color: #f7f6f3 !important; color: #37352f !important; border: 1px solid #e0e0e0 !important; }
        table { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #cccccc !important; width: 100% !important; border-collapse: collapse !important; }
        thead { display: table-header-group !important; }
        tr { page-break-inside: avoid !important; }
        td, th { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #cccccc !important; padding: 8px !important; word-wrap: break-word !important; }
        hr { border-color: #cccccc !important; }
        a { color: #007ACC !important; }
        img { border: none !important; max-width: 100% !important; height: auto !important; object-fit: contain !important; display: block; margin: 5px auto; page-break-inside: avoid !important; }
        table.code-block-table { background-color: #2F3437 !important; border: 1px solid #373c3f !important; border-radius: 6px !important; margin: 10px 0 !important; border-collapse: separate !important; }
        td.code-block-cell { background-color: #2F3437 !important; color: #f8f8f2 !important; border: none !important; padding: 15px !important; }
        pre.code-block-pre { background-color: transparent !important; color: #f8f8f2 !important; border: none !important; }
        """
        try:
            from pygments.formatters import HtmlFormatter
            formatter = HtmlFormatter(style='default', nowrap=True)
            pygments_css = formatter.get_style_defs('.highlight')
            pygments_css = pygments_css.replace(";", " !important;")
            theme_styles += "\n" + pygments_css
        except ImportError:
            pass
    
    theme_html = f'<style type="text/css">{theme_styles}</style>'
    if theme == 1:
        if '<head>' in html: html = html.replace('<head>', f'<head>{theme_html}')
        else: html = f'{theme_html}{html}'
        html = f'<div class="dark-page-wrapper">{html}</div>'
    elif theme == 2:
        if '<head>' in html: html = html.replace('<head>', f'<head>{theme_html}')
        else: html = f'{theme_html}{html}'
        html = f'<div class="sepia-page-wrapper">{html}</div>'
    elif isinstance(theme, str) and theme.startswith("#"):
        if '<head>' in html: html = html.replace('<head>', f'<head>{theme_html}')
        else: html = f'{theme_html}{html}'
        html = f'<div class="custom-page-wrapper">{html}</div>'
    else:
        if '<head>' in html: html = html.replace('<head>', f'<head>{theme_html}')
        else: html = f'{theme_html}{html}'
    return html

def process_images_for_pdf(html, whiteboard_images=None, page_metrics=None, theme=0):
    if not whiteboard_images: return html
    if not page_metrics:
        page_metrics = {'usable_width': 718, 'usable_height': 1000}
    
    usable_w = page_metrics['usable_width']
    usable_h = page_metrics['usable_height']
    
    image_map = {}
    for res_name, b64_data in whiteboard_images.items():
        if res_name.endswith("_meta") or res_name.endswith("_source"): continue
        if not b64_data.startswith('data:image'):
            image_map[res_name] = f"data:image/png;base64,{b64_data}"
        else:
            image_map[res_name] = b64_data

    if not image_map: return html

    pattern = r'<img\s+[^>]*?src=([\"\'])(.*?)\1[^>]*?>'
    
    def wrapper(m):
        res_name = m.group(2)
        if res_name in image_map:
            img_data = image_map[res_name]
            scaled_w = usable_w
            scaled_h = None
            try:
                if 'base64,' in img_data:
                    b64_clean = img_data.split('base64,')[1]
                    img_bytes = base64.b64decode(b64_clean)
                    image = QImage.fromData(img_bytes)
                    if not image.isNull():
                        orig_w = image.width()
                        orig_h = image.height()
                        if orig_w > 0:
                            scale_factor = usable_w / orig_w
                            projected_h = orig_h * scale_factor
                            if projected_h <= usable_h:
                                scaled_w = usable_w
                                scaled_h = None
                            else:
                                scaled_h = usable_h
                                scaled_w = None
            except Exception:
                scaled_w = min(usable_w, 500)
                scaled_h = None
            
            style_parts = ["display: block;", "object-fit: contain;", "margin: 5px 0;", "page-break-inside: avoid !important;", "max-width: 100%;"]
            if theme == 1:
                style_parts.extend(["border: 2px solid #444444 !important;", "box-shadow: 0 0 10px rgba(0,0,0,0.5);"])
            else:
                style_parts.append("border: 1px solid #dddddd !important;")
            
            if scaled_w: style_parts.append(f"width: {scaled_w}px; height: auto;")
            elif scaled_h: style_parts.append(f"height: {scaled_h}px; width: auto;")
            else: style_parts.append("width: 100%; height: auto;")
                
            style_str = " ".join(style_parts)
            return (f'<table class="wb-image-block" style="width: 100% !important; margin: 0 !important; border-collapse: collapse !important;">'
                    f'<tr style="page-break-inside: avoid !important;">'
                    f'<td style="page-break-inside: avoid !important; border: none !important; padding: 0 !important; text-align: left;">'
                    f'<img src="{img_data}" style="{style_str}">'
                    f'</td></tr></table>')
        return m.group(0)
    return re.sub(pattern, wrapper, html)

def force_code_block_styles(html):
    if not html: return html
    def fix_code_table(match):
        full_tag = match.group(0)
        fixed = re.sub(r'\s*bgcolor=["\']?[^"\'\s>]*["\']?', '', full_tag, flags=re.IGNORECASE)
        fixed = fixed.rstrip('>') + ' style="background-color: #2F3437 !important; border: 1px solid #373c3f !important; border-radius: 6px !important; border-collapse: separate !important; margin: 10px 0 !important; width: 100%; page-break-inside: avoid !important;">'
        return fixed
    html = re.sub(r'<table[^>]*bgcolor=["\']?#2f3437["\']?[^>]*>', fix_code_table, html, flags=re.IGNORECASE)
    
    def fix_code_cell(match):
        full_tag = match.group(0)
        if '#373c3f' in full_tag.lower() or 'border-top-color:#373c3f' in full_tag.lower():
            fixed = re.sub(r'\s*bgcolor=["\']?[^"\'\s>]*["\']?', '', full_tag, flags=re.IGNORECASE)
            fixed = re.sub(r'\s*style=["\'][^"\']*["\']', '', fixed)
            fixed = fixed.rstrip('>') + ' style="background-color: #2F3437 !important; color: #f8f8f2 !important; border: none !important; padding: 15px !important;">'
            return fixed
        return full_tag
    html = re.sub(r'<td[^>]*bgcolor=[^>]*>', fix_code_cell, html, flags=re.IGNORECASE)
    
    def fix_code_pre(match):
        full_tag = match.group(0)
        if 'consolas' in full_tag.lower() or 'monaco' in full_tag.lower() or 'courier' in full_tag.lower():
            fixed = re.sub(r'\s*style=["\'][^"\']*["\']', '', full_tag)
            fixed = fixed.rstrip('>') + ' style="background-color: transparent !important; color: #f8f8f2 !important; border: none !important; font-family: Consolas, Monaco, monospace; white-space: pre-wrap; margin: 0;">'
            return fixed
        return full_tag
    html = re.sub(r'<pre[^>]*>', fix_code_pre, html, flags=re.IGNORECASE)
    return html

def generate_folder_header_html(folder, theme=0):
    """Generates the title and date header for the folder export."""
    if theme == 1:
        title_style = "font-size: 32pt; font-weight: bold; color: #ffffff;"
        subtitle_style = "color: #cccccc; font-size: 14pt;"
        divider_style = "border-color: #444444;"
    elif theme == 2:
        title_style = "font-size: 32pt; font-weight: bold; color: #433422;"
        subtitle_style = "color: #8e5c2e; font-size: 14pt;"
        divider_style = "border-color: #dcd1bc;"
    else:
        title_style = "font-size: 32pt; font-weight: bold; color: #000000;"
        subtitle_style = "color: #666666; font-size: 14pt;"
        divider_style = "border-color: #cccccc;"
    
    now = datetime.now()
    date_str = now.strftime("%b %d %Y 🕜%I:%M%p")
    
    return f"""
    <div style="text-align: center; margin-top: 0px;">
        <h1 style="{title_style}; margin-top: 0px; margin-bottom: 5px;">{folder.name}</h1>
        <p style="{subtitle_style}; margin-top: 0px; margin-bottom: 5px;">Full Folder Export</p>
        <p style="{subtitle_style}; margin-top: 0px; font-size: 10pt;">{date_str}</p>
    </div>
    <hr style="{divider_style}; margin-top: 20px; margin-bottom: 20px;" />
    """

def prepare_note_for_export(note, idx, for_preview=False, theme=0, available_note_ids=None):
    """Processes a single note's content for export, including cleanup, emojis, and anchors."""
    anchor_id = f"note_{note.id}"
    
    # Base processing
    processed_content = cleanup_editor_artifacts(note.content)
    processed_content = sanitize_note_tables(processed_content)
    
    if not for_preview:
        processed_content = process_html_emojis(processed_content)
        
    # Scan and Inject Anchors for sub-items
    sub_toc, content_with_anchors = scan_and_inject_toc(processed_content, unique_prefix=anchor_id, note_index=idx)
    
    # Enforce Level Box Styles (Contrast Fix)
    content_with_anchors = enforce_level_box_styles(content_with_anchors)
    
    # NEW: Process Internal Links
    if available_note_ids:
        content_with_anchors = process_internal_links(content_with_anchors, available_note_ids, theme)
    
    return {
        'content': content_with_anchors,
        'sub_toc': sub_toc,
        'anchor': anchor_id
    }

def generate_note_title_block(note, idx, anchor, theme=0):
    """Generates the main title block for a note in the export."""
    return f'<div id="{anchor}"><h1 style="margin-bottom: 20px;"><span style="font-size: 60pt; background-color: #FFFF00; color: #000000 !important; padding: 10px;">{idx}. {note.title}</span></h1></div>'

def generate_folder_html(folder, for_preview=False, theme=0, start_index=1):
    html_parts = []
    
    if theme == 1:
        divider_style = "border-color: #444444;"
        toc_title_style = "color: #ffffff;"
        toc_link_style = "text-decoration: underline; color: #66b3ff;"
    elif theme == 2:
        divider_style = "border-color: #dcd1bc;"
        toc_title_style = "color: #433422;"
        toc_link_style = "text-decoration: underline; color: #8e5c2e;"
    else:
        divider_style = "border-color: #cccccc;"
        toc_title_style = "color: #000000;"
        toc_link_style = "text-decoration: underline; color: #007ACC;"
    
    # 1. Header
    html_parts.append(generate_folder_header_html(folder, theme))
    
    from models.note import Note
    sorted_notes = sorted(folder.notes, key=Note.sort_key)
    
    # --- UPDATED MASTER TOC ---
    html_parts.append(f'<div id="toc_anchor"><h2 style="{toc_title_style}">Table of Contents</h2></div><ul style="font-size: 14pt; line-height: 1.6;">')
    
    processed_notes_data = [] # Store items for content phase
    
    # Collect all IDs for link resolution
    available_note_ids = {n.id for n in sorted_notes}
    
    for idx, note in enumerate(sorted_notes, start_index):
        # Use new modular helper
        note_data = prepare_note_for_export(note, idx, for_preview, theme, available_note_ids)
        
        processed_notes_data.append({
            'note': note,
            'content': note_data['content'],
            'idx': idx,
            'anchor': note_data['anchor']
        })
        
        # Add Note Title to Main TOC
        html_parts.append(f'<li><a href="#{note_data["anchor"]}" style="{toc_link_style}"><b>{idx}. {note.title}</b></a>')
        
        # Add Sub-items
        sub_toc = note_data['sub_toc']
        if sub_toc:
            html_parts.append('<ul style="font-size: 11pt; list-style-type: circle; color: #555;">')
            for item in sub_toc:
                sub_indent = "margin-left: 10px;" if item['level'] > 1 else ""
                html_parts.append(f'<li style="{sub_indent}"><a href="#{item["anchor"]}" style="{toc_link_style}; text-decoration: none;">{item["text"]}</a></li>')
            html_parts.append('</ul>')
            
        html_parts.append('</li>')

    html_parts.append(f"</ul><br/><hr style=\"{divider_style}\" /><br/>")
    
    # 3. Notes Content
    for data in processed_notes_data:
        note = data['note']
        anchor = data['anchor']
        processed_content = data['content']
        idx = data['idx']
        
        # Use new modular helper
        html_parts.append(generate_note_title_block(note, idx, anchor, theme))
        
        if for_preview:
            # Buffer limit for preview to avoid browser crash
            if len(processed_content) > 2000000:
                processed_content = processed_content[:2000000] + '<br/><p style="color: red; font-weight: bold;">⚠️ Content truncated for preview</p>'
        
        html_parts.append(processed_content)
        
        if theme == 1:
            back_link_style = "text-decoration: none; color: #66b3ff; font-size: 6pt;"
        else:
            back_link_style = "text-decoration: none; color: #0366d6; font-size: 6pt;"
        
        html_parts.append(f"""
        <p style="text-align: right; margin-top: 10px;">
            <a href="#toc_anchor" style="{back_link_style}">↑ Back to Table of Contents</a>
        </p>
        <br/><hr style="{divider_style}" /><br/>
        """)
        
    return "".join(html_parts)

def export_folder_to_pdf(folder, output_path, progress_callback=None, theme=0):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setColorMode(QPrinter.ColorMode.Color)
    printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
    page_metrics = {
        'usable_width': int(page_rect.width()),
        'usable_height': int(page_rect.height()) - 50
    }

    doc = QTextDocument()
    doc.setDocumentMargin(5)
    doc.setDefaultFont(QFont("Segoe UI", 7))
    
    all_whiteboard_images = {}
    for note in folder.notes:
        wb_imgs = getattr(note, 'whiteboard_images', {})
        all_whiteboard_images.update(wb_imgs)

    html_content = generate_folder_html(folder, for_preview=False, theme=theme)
    html_content = process_images_for_pdf(html_content, all_whiteboard_images, page_metrics, theme)
    html_content = apply_theme_to_html(html_content, theme)
    html_content = force_code_block_styles(html_content)
    
    doc.setHtml(html_content)
    logger.info(f"Exporting folder '{folder.name}' to {output_path} (Native + Footer)...")
    _print_document_with_footer(doc, printer, folder.name, progress_callback, theme)

def export_html_to_pdf(html_content, output_path, footer_text="Highlights", theme=0):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setColorMode(QPrinter.ColorMode.Color)
    printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

    doc = QTextDocument()
    doc.setDocumentMargin(10)
    doc.setDefaultFont(QFont("Segoe UI", 10))
    doc.setHtml(html_content)

    logger.info(f"Exporting HTML to {output_path} (Theme: {theme})...")
    _print_document_with_footer(doc, printer, footer_text, theme=theme)
