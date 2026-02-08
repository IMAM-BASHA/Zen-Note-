from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QToolBar, QApplication, QComboBox, QColorDialog, QSpinBox,
    QDialog, QGridLayout, QPushButton, QToolButton, QMenu, QMessageBox, QSplitter, QListWidget, QListWidgetItem, QLabel,
    QLineEdit
)
from PyQt6.QtGui import (
    QAction, QTextCursor, QTextListFormat, QColor, QTextImageFormat, 
    QTextCharFormat, QFont, QDesktopServices, QTextDocument, QImage, QPainter,
    QPixmap, QPolygonF, QPen, QBrush, QIcon, QClipboard, QTextFormat
)
from util.icon_factory import get_premium_icon
import ui.styles as styles
from PyQt6.QtCore import Qt, pyqtSignal, QSizeF, QSize, QUrl, QByteArray, QBuffer, QTimer, QThreadPool, QRunnable, pyqtSlot, QObject, QEvent
import time
# Monkey Patch for libraries using deprecated time.clock (Python 3.8+)
if not hasattr(time, 'clock'):
    time.clock = time.perf_counter

import base64
try:
    from pygments import highlight as pyg_highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    from util.logger import logger
    logger.debug("Pygments NOT detected")

import uuid
from util.logger import logger

class FindBar(QWidget):
    """Collapsible Search Bar for finding text within the editor."""
    search_next = pyqtSignal(str)
    search_prev = pyqtSignal(str)
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Floating Card Style
        self.setFixedWidth(320)
        # Shadow effect via stylesheet is limited in Qt without QGraphicsEffect, using border for now
        # Floating Card Style initialized with default; updated via set_theme_mode
        self.set_theme_mode("light")
        
        # Components
        
        # Components
        self.lbl_icon = QLabel("🔍")
        self.lbl_icon.setStyleSheet("border: none; background: transparent;")
        self.layout.addWidget(self.lbl_icon)
        
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Find...")
        self.inp_search.returnPressed.connect(self.on_return_pressed)
        # Connect textChanged for live search/count
        self.inp_search.textChanged.connect(self.on_text_changed)
        self.layout.addWidget(self.inp_search)
        
        # Match Count Label
        self.lbl_count = QLabel("")
        self.lbl_count.setObjectName("MatchCount")
        self.layout.addWidget(self.lbl_count)
        
        self.btn_prev = QPushButton("⬆")
        self.btn_prev.setToolTip("Previous Match (Shift+Enter)")
        self.btn_prev.setFixedSize(24, 24)
        self.btn_prev.clicked.connect(lambda: self.search_prev.emit(self.inp_search.text()))
        self.layout.addWidget(self.btn_prev)
        
        self.btn_next = QPushButton("⬇")
        self.btn_next.setToolTip("Next Match (Enter)")
        self.btn_next.setFixedSize(24, 24)
        self.btn_next.clicked.connect(lambda: self.search_next.emit(self.inp_search.text()))
        self.layout.addWidget(self.btn_next)
        
        # self.lbl_status = QLabel("")
        # self.layout.addWidget(self.lbl_status)
        
        # self.layout.addStretch() # No stretch for compact card
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Close (Esc)")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.clicked.connect(self.close_bar)
        self.layout.addWidget(self.btn_close)
        
        self.setVisible(False)
        
    def on_return_pressed(self):
        text = self.inp_search.text()
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.search_prev.emit(text)
        else:
            self.search_next.emit(text)
            
    def on_text_changed(self, text):
        # Emit search_next to update selection/count live
        # Using a specialized signal or reusing search_next with a flag?
        # Let's just emit search_next to find first match.
        if text:
             self.search_next.emit(text)
        else:
             self.lbl_count.setText("")

    def close_bar(self):
        self.setVisible(False)
        self.inp_search.clear() # Clear on close
        self.closed.emit()
        
    def show_bar(self):
        self.setVisible(True)
        self.inp_search.setFocus()
        self.inp_search.selectAll()
        # Trigger initial count if text exists
        if self.inp_search.text():
            self.search_next.emit(self.inp_search.text())
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        else:
            super().keyPressEvent(event)

    def set_theme_mode(self, mode):
        """Update FindBar styling based on theme."""
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        self.setStyleSheet(f"""
            QWidget {{ 
                background-color: {c['popover']}; 
                border: 1px solid {c['border']}; 
                border-radius: 12px; 
                color: {c['foreground']};
            }}
            QLineEdit {{ 
                border: 1px solid {c['input']}; 
                border-radius: 4px; 
                padding: 4px; 
                background: {c['background']}; 
                color: {c['foreground']}; 
                selection-background-color: {c['secondary']};
                selection-color: {c['secondary_foreground']};
            }}
            QLineEdit:focus {{ border: 1px solid {c['ring']}; }}
            
            QPushButton {{ 
                border: 1px solid transparent; 
                padding: 4px; 
                border-radius: 4px; 
                color: {c['foreground']}; 
                background: transparent;
            }}
            QPushButton:hover {{ 
                background-color: {c['accent']}; 
                color: {c['accent_foreground']};
            }}
            
            QLabel {{
                color: {c['muted_foreground']}; 
                font-size: 11px; 
                border: none; 
                background: transparent;
                padding: 0 4px;
            }}
        """)

class ImageProcessor(QObject):
    """Async image processing worker to prevent UI blocking."""
    
    finished = pyqtSignal(dict)  # Signal with processed data
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        
    def process_async(self):
        """Process image data asynchronously."""
        try:
            # Handle input types (QImage or Data Dict)
            if isinstance(self.data, QImage):
                view_image = self.data
                source_image = self.data
                meta = {}
            else:
                view_image = self.data['view']
                source_image = self.data['source']
                meta = self.data['meta']
            
            if view_image.isNull():
                return
            
            # Don't upscale - preserve original quality
            # Images will be resized by CSS/HTML during display if needed
            scaled_view = view_image
            
            # Convert to base64
            def img_to_b64(img, quality=95):
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QBuffer.OpenModeFlag.WriteOnly)
                img.save(buf, "PNG", quality=quality)
                return ba.toBase64().data().decode()
            
            result = {
                'view_b64': img_to_b64(scaled_view, 95),  # High quality for crisp display
                'source_b64': img_to_b64(source_image, 100),  # Maximum quality for editing
                'meta': meta,
                'view_image': scaled_view,
                'source_image': source_image,
                'original_width': view_image.width(),
                'original_height': view_image.height()
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Error processing image asynchronously: {e}")

class ImageProcessingTask(QRunnable):
    """Runnable task for async image processing."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.setAutoDelete(True)
        
    def run(self):
        self.processor.process_async()

    # Obsolete PersistentTextEdit removed
    
    # Obsolete PersistentTextEdit removed

class MarkdownTextEdit(QTextEdit):
    """Custom QTextEdit with Markdown paste support"""
    
    def _fix_paste_color(self, start_pos):
        """Ensure pasted text in Level Boxes respects adaptive contrast."""
        end_pos = self.textCursor().position()
        if end_pos <= start_pos: return
        
        # Access parent TextEditor
        editor_widget = self.parent()
        if not hasattr(editor_widget, 'level1_color'): return
        
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        curr_table = cursor.currentTable()
        if not curr_table: return
        
        # Check if Level Box Content Cell (col 1)
        cell = curr_table.cellAt(cursor)
        if not cell.isValid() or cell.column() != 1: return
        
        # Identify Level
        cell_zero = curr_table.cellAt(0, 0)
        c0 = cell_zero.firstCursorPosition()
        text0 = c0.block().text().strip()
        
        target_color = None
        import re
        if re.match(r'^\[\d+(\.\d+)+\]$', text0):
            # Check L1 or L2
            if re.match(r'^\[\d+\.\d+\]$', text0): target_color = editor_widget.level1_color
            elif re.match(r'^\[\d+\.\d+\.\d+\]$', text0): target_color = editor_widget.level2_color
        
        if target_color:
             contrast = editor_widget._get_contrast_text_color(target_color)
             
             # Select the pasted range
             update_cursor = self.textCursor()
             update_cursor.setPosition(start_pos)
             update_cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
             
             fmt = QTextCharFormat()
             fmt.setForeground(QColor(contrast))
             update_cursor.mergeCharFormat(fmt)

    def insertFromMimeData(self, source):
        """Override to handle Markdown conversion on paste"""
        start_pos = self.textCursor().position()
        is_markdown = False
        
        # Priority 1: Image data
        if source.hasImage():
            # Let parent handle images normally
            super().insertFromMimeData(source)
            return
            
        # Priority 2: Check for Markdown patterns in text
        if source.hasText():
            text = source.text()
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # Detect Markdown or Code
            # NEW: We skip markdown detection if we have HTML, UNLESS it's a triple-backtick code block.
            # This ensures rich text from Gemini/Web is pasted as HTML, but code snippets stay pretty.
            has_code_fence = "```" in text
            
            if has_code_fence:
                is_markdown = True
            elif not source.hasHtml():
                # Only check for markdown symbols if NO HTML is available
                if "`" in text: is_markdown = True
                elif "**" in text or "*" in text or "__" in text: is_markdown = True
                elif "##" in text: is_markdown = True
                # Check for markdown table
                if "|" in text and "\n" in text and ("---" in text or ":-" in text):
                     is_markdown = True
                elif "\n-" in text or "\n*" in text: is_markdown = True
                elif "[" in text and "](" in text: is_markdown = True

            # Auto-Detect Code logic (Pygments + Heuristics)
            # Only run if not already marked markdown and NO HTML is present
            if not is_markdown and not source.hasHtml() and PYGMENTS_AVAILABLE:
                try:
                    text_stripped = text.strip()
                    # Only check reasonably length content
                    if len(text_stripped) > 5:
                        is_likely_code = False
                        
                        # IMPROVED STRICT HEURISTICS
                        # We use Regex to look for structural patterns, not just keywords.
                        # This prevents "HOW return WORKS" from triggering code block.
                        
                        import re
                        
                        # 1. Reject simple single-line sentences unless they look like specific statements
                        lines = text_stripped.split('\n')
                        if len(lines) == 1:
                            # If single line, must end with ; or { or } to be "code-like" (C/JS/Java)
                            # OR start with specific Python keywords
                            if not (text_stripped.endswith(';') or text_stripped.endswith('{') or text_stripped.endswith('}')):
                                 # Python/Shell exceptions: def, import, class, from, #
                                 if not re.match(r'^\s*(def|class|import|from|#)\s+', text_stripped):
                                     pass # Continue to check regular patterns, but be skeptical
                        
                        # 2. Strict Pattern Matching
                        patterns = [
                            r'^\s*def\s+\w+\(',          # def func(
                            r'^\s*class\s+\w+',          # class Name
                            r'^\s*import\s+[\w\.]+',     # import os
                            r'^\s*from\s+[\w\.]+\s+import', # from x import
                            r'^\s*if\s*\(.+\)\s*\{',     # if (...) {
                            r'^\s*if\s+.+:\s*$',         # if ...:
                            r'^\s*for\s*\(.+\)\s*\{',    # for (...) {
                            r'^\s*for\s+.+:\s*$',        # for ...:
                            r'^\s*return\s+[\w\'"]+',    # return val
                            r'^\s*print\s*\(',           # print(
                            r'console\.log\(',
                            r'public\s+static\s+void',
                            r'^\s*(const|let|var)\s+\w+\s*=', # const x =
                            r'^\s*#include\s+<',
                            r'^\s*\w+\s*=\s*[^=]+;?$',   # x = 5; (Simple assignment, risky but common)
                            r'=>',                       # Arrow function
                        ]
                        
                        for pat in patterns:
                            if re.search(pat, text_stripped, re.MULTILINE):
                                is_likely_code = True
                                break
                                
                        # 3. Structure Checks (Indentation + Braces) - Fallback for multi-line
                        if not is_likely_code and len(lines) > 1:
                            has_indent = any(line.startswith('    ') or line.startswith('\t') for line in lines)
                            if has_indent and ('{' in text and '}' in text):
                                is_likely_code = True
                            if has_indent and text_stripped.endswith(':'): # Python
                                is_likely_code = True

                        if is_likely_code:
                            # Trust our heuristics!
                            is_markdown = True
                            text = f"```\n{text}\n```"

                except Exception as e:
                     pass
            
            if is_markdown:
                try:
                    from markdown_it import MarkdownIt
                    
                    # Custom Highlighter
                    def highlight_func(str_content, lang, attrs):
                        if PYGMENTS_AVAILABLE:
                            try:
                                if lang and lang.strip():
                                    lexer = get_lexer_by_name(lang)
                                else:
                                    lexer = guess_lexer(str_content)
                                
                                # Notion-like Dark Theme
                                # background: #2F3437 (Notion Code Block BG)
                                # noclasses=True -> Inline styles
                                # nowrap=True -> We handle the wrapping (Qt handles tables better than divs)
                                # Theme-Aware Highlighting
                                # We use noclasses=True -> Inline styles (More robust for Qt & PDF)
                                # We enforce 'monokai' (Dark) to match the code block background.
                                formatter = HtmlFormatter(noclasses=True, style='monokai', nowrap=True)
                                highlight = pyg_highlight(str_content, lexer, formatter)
                                
                                # Use strict tables for layout, but rely on CSS for colors
                                return (
                                    f'<table class="code-block-table" border="0" style="margin-top: 10px; margin-bottom: 10px; width: 100%; border-collapse: separate; border-radius: 6px; border: 1px solid gray; page-break-inside: avoid; background-color: #2F3437;">'
                                    f'<tr><td class="code-block-cell" style="padding: 15px; background-color: #2F3437; color: #F8F8F2;">'
                                    f'<pre class="code-block-pre highlight" style="font-family: Consolas, Monaco, \'Courier New\', monospace; font-size: 13px; margin: 0; white-space: pre-wrap;">'
                                    f'{highlight}'
                                    f'</pre></td></tr></table>'
                                )
                            except Exception as e:
                                print(f"Highlight error: {e}")
                                pass
                        
                        # Fallback (Table based)
                        return (
                            f'<table class="code-block-table" border="0" style="margin-top: 10px; margin-bottom: 10px; width: 100%; border-radius: 6px; border: 1px solid gray; page-break-inside: avoid;">'
                            f'<tr><td class="code-block-cell" style="padding: 15px;">'
                            f'<pre class="code-block-pre" style="font-family: Consolas, monospace; margin: 0;">{str_content}</pre>'
                            f'</td></tr></table>'
                        )

                    # Use 'gfm-like' defaults but override highlighter
                    md = MarkdownIt("commonmark", {
                        'breaks': True, 
                        'html': True, 
                        'highlight': highlight_func
                    }).enable('table')
                    
                    html = md.render(text)
                    
                    # Post-process for consistency if highlighter wasn't triggered for inline code
                    html = html.replace('<code>', '<code style="background: rgba(135,131,120,0.15); color: #EB5757; padding: 2px 5px; border-radius: 3px; font-family: Consolas, monospace;">')
                    
                    # Table Styling
                    html = html.replace('<table>', '<table border="1" style="border-collapse: collapse; width: 100%; border-color: #555; margin: 10px 0;">')
                    html = html.replace('<th>', '<th style="background-color: #373737; color: white; padding: 8px; border: 1px solid #555;">')
                    html = html.replace('td>', 'td style="padding: 8px; border: 1px solid #555;">')
                    
                    self.insertHtml(html)
                    return
                except (ImportError, Exception) as e:
                    print(f"Markdown render error: {e}")
                    # Fallback regex parser (Simplified for brevity, assuming MarkdownIt mostly works)
                    import re
                    from html import escape
                    html = escape(text)
                    
                    # Basic Code Block Regex fallback
                    def code_block_repl_fallback(match):
                        content = match.group(1)
                        if PYGMENTS_AVAILABLE:
                            try:
                                lexer = guess_lexer(content)
                                # Dynamic classes -> Inline Styles
                                formatter = HtmlFormatter(noclasses=True, style='monokai', wrapcode=False)
                                highlighted = pyg_highlight(content, lexer, formatter)
                                return f'<div class="code-block-div highlight" style="margin: 10px 0; background-color: #2F3437; color: #F8F8F2; padding: 10px; border-radius: 6px;">{highlighted}</div>'
                            except: pass
                        return f'<pre style="padding: 15px;"><code>{content}</code></pre>'

                    html = re.sub(r'```(.*?)```', code_block_repl_fallback, html, flags=re.DOTALL)
                    self.insertHtml(html)
                    self._fix_paste_color(start_pos)
                    return
        
        if source.hasHtml() and not is_markdown:
            html = source.html()
            
            # DARK MODE FIX: Prevent "Black-on-Dark" invisibility
            # Find TextEditor parent (could be nested in Splitter)
            p = self.parent()
            theme = 'light'
            while p:
                if hasattr(p, 'theme_mode'):
                    theme = p.theme_mode
                    break
                p = p.parent()
            
            if theme == 'dark':
                import re
                # SUPER NUCLEAR RESET: Strip ALL hardcoded color/background styles
                # Robust regex to catch rgb(...), hex, named colors
                html = re.sub(r'color\s*:[^;>]+(?:;)?', '', html, flags=re.IGNORECASE)
                html = re.sub(r'background(?:-color)?\s*:[^;>]+(?:;)?', '', html, flags=re.IGNORECASE)
                html = re.sub(r'bgcolor\s*=\s*["\']?[^"\'>\s]+["\']?', '', html, flags=re.IGNORECASE)
                
                # Strip class attributes which might carry Stylesheet colors
                html = re.sub(r'class\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)

                # Get colors from Shadcn palette
                c = styles.ZEN_THEME["dark"]
                html = f'<div style="color: {c["foreground"]}; background-color: {c["background"]};">{html}</div>'

            # CORE FIX: Check for nested block insertion
            if self.textCursor().currentTable():
                html = self._clean_nested_paste(html)
                self.insertHtml(html)
            else:
                self.insertHtml(html)
                
            self._fix_paste_color(start_pos)
            return
            
        # Fallback
        super().insertFromMimeData(source)
        self._fix_paste_color(start_pos)

    def _clean_nested_paste(self, html):
        """
        Smartly unwraps "Box" HTML (Code Blocks, Level Boxes, Note Blocks) 
        when pasting into an existing Box to prevent double-boxing.
        Returns the inner content (e.g. <pre>...</pre> or inner spans).
        """
        import re
        
        # 1. Detect Code Block Table (Robust Check: Style-based or Content-based)
        # Class attributes are often stripped by Qt on copy, so we check for background color or structure.
        # Check for table ... background-color: #2F3437 ... pre ...
        # OR just a table wrapping a pre.
        
        # Regex to find a table wrapping a PRE tag.
        # We look for the pre content.
        code_match = re.search(r'<table[^>]*>[\s\S]*?(<pre[^>]*>[\s\S]*?</pre>)[\s\S]*?</table>', html, re.IGNORECASE)
        if code_match:
            # Verify if it looks like our code block (optional: check BG color in HTML or just assume table+pre = code block wrapper)
            # Given we use tables mostly for this, it's a safe assumption for "Unwrapping" to avoid nesting tables.
            return code_match.group(1)
            
        # 2. Detect Level Box / General Box (Checked by border/bg styles on table)
        # If it's a table with a background color or border, it's likely a "Box".
        # We want to extract the content. usually in a <td>.
        # But a table might have multiple cells.
        
        # Heuristic: If it matches our Level Box pattern ([1.1])
        if re.search(r'\[\s*\d+(?:\.\d+)+\s*\]', html):
            # It's a Level Box. Content is usually in the 2nd cell.
            # <td...>...</td> <td...>(CONTENT)</td>
            cells = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL | re.IGNORECASE)
            if len(cells) >= 2:
                return cells[1].strip()
        
        # 3. Generic Table Unwrap (Note Blocks, or just copied tables)
        # If the input is fundamentally JUST a table, we unwrap its cell contents.
        # This catches "Note Blocks", "Code Blocks" (if regex failed), or any other box container.
        stripped = html.strip()
        
        # Check if it starts/ends with table tags (allowing for some potential leading/trailing tags/whitespace)
        # Qt often wraps things in fragments, so we check if a table is the MAIN block.
        table_match = re.search(r'^\s*(?:<[^>]+>)*\s*<table[^>]*>([\s\S]*)</table>\s*(?:<[^>]+>)*\s*$', stripped, re.IGNORECASE)
        
        if table_match:
             # Extract all cells.
             # We want to flatten them into paragraphs? Or just join them?
             # For a single cell box (Note Block), getting the cells is correct.
             cells = re.findall(r'<td[^>]*>(.*?)</td>', stripped, re.DOTALL | re.IGNORECASE)
             if cells:
                 # Filter out empty cells if needed?
                 # Join with breaks to separate cell content
                 return "<br>".join(cells)

        return html

    def mouseMoveEvent(self, event):
        """Update cursor when hovering over links."""
        is_link = False
        if self.anchorAt(event.pos()):
            is_link = True
        else:
            cursor = self.cursorForPosition(event.pos())
            fmt = cursor.charFormat()
            if fmt.isAnchor() and fmt.anchorHref():
                is_link = True

        if is_link:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Handle link clicks, images, and checklists."""
        url_str = ""
        
        # 1. Try anchorAt first (standard Qt method)
        anchor = self.anchorAt(event.pos())
        if anchor:
            url_str = anchor
            
        # 2. Fallback to cursor analysis for complex styled spans (like our buttons)
        if not url_str:
            cursor = self.cursorForPosition(event.pos())
            fmt = cursor.charFormat()
            if fmt.isAnchor() and fmt.anchorHref():
                url_str = fmt.anchorHref()
        
        # 3. Handle URL Actions
        if url_str:
             print(f"DEBUG: LINK CLICK DETECTED: Raw URL='{url_str}'")
             qurl = QUrl(url_str)
             scheme = qurl.scheme()
             print(f"DEBUG: PARSED URL: Scheme='{scheme}', Host='{qurl.host()}', Query='{qurl.query()}'")
             
             # Check for Note Link
             if scheme == "note":
                 note_id = qurl.host() if qurl.host() else qurl.path().strip("/")
                 query = qurl.query()
                 print(f"DEBUG: NOTE LINK ACTION: note_id='{note_id}', is_overlay={'overlay=true' in query}")
                 
                 # Traverse to TextEditor
                 p = self.parent()
                 while p:
                     if hasattr(p, 'request_open_note'):
                         if "overlay=true" in query:
                             p.request_open_note_overlay.emit(note_id)
                         else:
                             p.request_open_note.emit(note_id)
                         event.accept()
                         return
                     p = p.parent()

             # Check for Image/Action Link (delegated to parent)
             elif scheme == "action" or (anchor and not url_str.startswith("http")):
                 # Valid fallback for image actions if they use anchors
                 p = self.parent()
                 while p:
                     if hasattr(p, '_handle_image_action'):
                         click_cursor = self.cursorForPosition(event.pos())
                         p._handle_image_action(qurl, cursor=click_cursor)
                         event.accept()
                         return
                     p = p.parent()

             # External Link
             else:
                 QDesktopServices.openUrl(qurl)
             return

        # 4. Checklist Toggling (Delegated to parent helper)
        # Check right character
        cursor = self.cursorForPosition(event.pos())
        cursor.setPosition(self.cursorForPosition(event.pos()).position())
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
        char_right = cursor.selectedText()
        
        p = self.parent()
        editor_widget = None
        while p:
            if hasattr(p, '_toggle_checklist_char'):
                editor_widget = p
                break
            p = p.parent()
            
        if editor_widget:
             if editor_widget._toggle_checklist_char(cursor, char_right):
                 pass # Event accepted/handled
             else:
                 # Check Left
                 cursor.setPosition(self.cursorForPosition(event.pos()).position())
                 cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
                 char_left = cursor.selectedText()
                 if editor_widget._toggle_checklist_char(cursor, char_left):
                     pass

        super().mousePressEvent(event)
    
class SymbolDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Symbol")
        self.selected_symbol = None
        self.layout = QGridLayout(self)
        
        symbols = [
            "←", "↑", "→", "↓", "↔", "↕",
            "★", "☆", "○", "●", "□", "■",
            "☺", "☹", "♥", "♦", "♣", "♠",
            "✓", "✗", "∞", "≈", "≠", "≤",
            "≥", "±", "÷", "×", "°", "π",
            "Ω", "μ", "Σ", "€", "£", "¥",
            "©", "®", "™", "§", "¶", "†"
        ]
        
        row = 0
        col = 0
        max_cols = 6
        
        for sym in symbols:
            btn = QPushButton(sym)
            btn.setFixedSize(40, 40)
            # Use a partial or lambda to capture the symbol
            # Note: loop variable 'sym' needs to be captured correctly
            btn.clicked.connect(lambda checked, s=sym: self.select_symbol(s))
            self.layout.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def select_symbol(self, symbol):
        self.selected_symbol = symbol
        self.accept()

class TextEditor(QWidget):
    contentChanged = pyqtSignal()
    exportNoteRequest = pyqtSignal()
    edit_whiteboard_requested = pyqtSignal(dict) # Metadata
    request_open_note = pyqtSignal(str) # Note ID
    request_open_note_overlay = pyqtSignal(str) # Note ID for overlay

    request_open_link_dialog = pyqtSignal()
    requestShortcutDialog = pyqtSignal()

    def __init__(self, parent=None, data_manager=None, shortcut_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.shortcut_manager = shortcut_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar Actions (Initialized here, but not added to a local toolbar)
        self._init_actions()
        
        # Find Bar (Floating Overlay - Not in Layout)
        self.find_bar = FindBar(self)
        self.find_bar.search_next.connect(lambda t: self.find_text(t, forward=True))
        self.find_bar.search_prev.connect(lambda t: self.find_text(t, forward=False))
        
        # Connect Ctrl+F
        self.find_action = QAction(self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.find_action.triggered.connect(self.toggle_find_bar)
        self.addAction(self.find_action)

        # Editor Area
        self.editor = MarkdownTextEdit()
        self.editor.setFont(QFont("Segoe UI", 12))
        # Replace layout-breaking setTextWidth with proper viewport margins
        self.editor.setViewportMargins(30, 20, 30, 20)
        self.editor.textChanged.connect(self.contentChanged.emit)
        self.editor.installEventFilter(self) # Handle link clicks
        self.find_bar.closed.connect(self.editor.setFocus)
        # Sync font size spinbox with current selection
        self.editor.cursorPositionChanged.connect(self.update_format_ui)
        # Enable clickable links in QTextEdit
        self.editor.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction | 
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.layout.addWidget(self.editor)
        # Override mousePressEvent to handle anchor clicks - MOVED TO MarkdownTextEdit.mousePressEvent
        # self.editor.mousePressEvent = self._editor_mouse_press
        
        # Override keyPressEvent to handle custom auto-lists (Checkboxes, Symbols)
        self.editor.keyPressEvent = self._editor_key_press
        
        # Override paste event to handle image pasting - handled by class methods
        
        # Track current folder for image storage
        self.current_folder = None
        
        # FIX: Track files we're actively refreshing to prevent watcher loop
        self._refreshing_files = set()
        
        # Load custom highlight color from settings
        saved_color = "cyan"
        if self.data_manager:
            saved_color = self.data_manager.get_setting("custom_highlight_color", "cyan")
        self.custom_highlight_color = QColor(saved_color)
        
        # Local image data storage for persistence
        self.whiteboard_images = {}
        self._last_resize_width = -1
        self._image_dimensions_cache = {}
        
        # Debounce Timer for Highlights
        self.highlight_debounce_timer = QTimer()
        self.highlight_debounce_timer.setSingleShot(True)
        self.highlight_debounce_timer.setInterval(200)
        
        # Debounce Timer for Autosave
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(2000)
        
        self._resize_debounce_timer = QTimer()
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_debounce_timer.timeout.connect(self._resize_images_to_fit)
        
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(2)
        
        # --- Auto-Refresh Watcher ---
        from PyQt6.QtCore import QFileSystemWatcher
        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.fileChanged.connect(self._handle_file_change)
        self.watched_images = {}
        
        # Level Numbering Support
        self.base_note_index = 0
        if self.data_manager:
            self.level1_color = QColor(self.data_manager.get_setting("level1_color", "#FFEB3B"))
            self.level2_color = QColor(self.data_manager.get_setting("level2_color", "#00FF00"))
        else:
            self.level1_color = QColor("#FFEB3B")
            self.level2_color = QColor("#00FF00")
        
        # --- TOC & Editor Layout ---
        from PyQt6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QWidget, QSplitter, QLabel, QPushButton
        
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setHandleWidth(4)
        self.editor_splitter.addWidget(self.editor)
        
        self.toc_panel = QWidget()
        self.toc_panel.setMinimumWidth(100)
        
        toc_layout = QVBoxLayout(self.toc_panel)
        toc_layout.setContentsMargins(0, 0, 0, 0)
        toc_layout.setSpacing(0)
        
        self.toc_header = QWidget()
        header_layout = QHBoxLayout(self.toc_header)
        header_layout.setContentsMargins(10, 5, 5, 5)
        
        self.lbl_toc = QLabel("Table of Contents")
        header_layout.addWidget(self.lbl_toc)
        header_layout.addStretch()
        
        self.btn_close_toc = QPushButton("×")
        self.btn_close_toc.setFixedSize(20, 20)
        self.btn_close_toc.clicked.connect(self.toggle_toc)
        header_layout.addWidget(self.btn_close_toc)
        
        toc_layout.addWidget(self.toc_header)
        
        self.toc_list = QListWidget()
        self.toc_list.setFrameShape(QListWidget.Shape.NoFrame)
        self.toc_list.setWordWrap(True)
        self.toc_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.toc_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.toc_list.itemClicked.connect(self._on_toc_item_clicked)
        toc_layout.addWidget(self.toc_list)
        
        self.editor_splitter.addWidget(self.toc_panel)
        self.editor_splitter.setStretchFactor(0, 4)
        self.editor_splitter.setStretchFactor(1, 1)
        self.layout.addWidget(self.editor_splitter)
        
        # Navigation Back Button
        self.btn_back = QPushButton(self.editor)
        self.btn_back.hide()
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self._on_back_clicked)
        
        # Load Persistence
        show_toc = False
        if self.data_manager:
            show_toc = self.data_manager.get_setting("show_toc", "false") == "true"
        self.toc_panel.setVisible(show_toc)
        
        self.editor.cursorPositionChanged.connect(self._enforce_readonly_numbers)
        self.editor.textChanged.connect(lambda: self.refresh_toc() if self.toc_list.isVisible() else None)
        
        self.theme_mode = "light"
        self._update_toc_style()    

    def _init_actions(self):
        """Initialize all actions so they can be retrieved by external TitleBar."""
        # --- Row 1 Logic ---
        # 1. Font Family
        self.combo_font = QComboBox()
        self.combo_font.addItems(["Segoe UI", "Arial", "Times New Roman", "Courier New", "Verdana", "Georgia", "Tahoma", "Trebuchet MS"])
        self.combo_font.setCurrentText("Segoe UI")
        self.combo_font.currentTextChanged.connect(self.set_font_family)
        self.combo_font.setFixedWidth(120)
        self.combo_font.setToolTip("Font Family")

        # 2. Font Size
        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 72)
        self.spin_size.setValue(12)
        self.spin_size.valueChanged.connect(self.text_size)
        self.spin_size.setFixedWidth(42) # Optimized width
        self.spin_size.setToolTip("Font Size")

        self.action_font_inc = QAction(get_premium_icon("plus_circle"), "", self)
        self.action_font_inc.setToolTip(f"Increase Font Size ({self._get_shortcut('editor_font_inc', 'Ctrl++')})")
        self.action_font_inc.triggered.connect(self.font_size_step_up)

        self.action_font_dec = QAction(get_premium_icon("minus_circle"), "", self)
        self.action_font_dec.setToolTip(f"Decrease Font Size ({self._get_shortcut('editor_font_dec', 'Ctrl+-')})")
        self.action_font_dec.triggered.connect(self.font_size_step_down)
        
        # 3. Text Formatting Actions
        self.action_bold = QAction(get_premium_icon("bold"), "Bold", self)
        self.action_bold.setShortcut("Ctrl+B")
        self.action_bold.setCheckable(True)
        self.action_bold.triggered.connect(self.text_bold)
        
        self.action_italic = QAction(get_premium_icon("italic"), "Italic", self)
        self.action_italic.setShortcut("Ctrl+I")
        self.action_italic.setCheckable(True)
        self.action_italic.triggered.connect(self.text_italic)
        
        self.action_underline = QAction(get_premium_icon("underline"), "Underline", self)
        self.action_underline.setShortcut("Ctrl+U")
        self.action_underline.setCheckable(True)
        self.action_underline.triggered.connect(self.text_underline)
        
        self.action_strike = QAction(get_premium_icon("strike"), "Strikethrough", self)
        self.action_strike.setCheckable(True)
        self.action_strike.triggered.connect(self.text_strike)
        
        self.action_numbering = QAction(get_premium_icon("list_ordered"), "Numbered List", self)
        self.action_numbering.setCheckable(True)
        self.action_numbering.triggered.connect(self.text_number_list)

        # Super/Sub Script
        self.action_super = QAction(get_premium_icon("superscript"), "Superscript", self)
        self.action_super.setToolTip("Superscript")
        self.action_super.triggered.connect(self.text_super)

        self.action_sub = QAction(get_premium_icon("subscript"), "Subscript", self)
        self.action_sub.setToolTip("Subscript")
        self.action_sub.triggered.connect(self.text_sub)
        
        # 4. Highlighter & Colors
        self.action_highlight = QAction(get_premium_icon("highlight"), "Highlight", self)
        self.action_highlight.setToolTip("Highlight Text (Ctrl+H)")
        self.action_highlight.setShortcut("Ctrl+H")
        self.action_highlight.triggered.connect(self.text_highlight)
        
        # Custom Highlighter (Ctrl+J)
        self.btn_custom_hl = QToolButton()
        if hasattr(self, 'custom_highlight_color'):
             self._update_custom_hl_icon(self.custom_highlight_color)
        else:
             self.btn_custom_hl.setText("🌈") 
        self.btn_custom_hl.setToolTip("Custom Highlight (Ctrl+J)")
        
        custom_hl_action = QAction(self.btn_custom_hl.icon(), "", self)
        custom_hl_action.setShortcut(self._get_shortcut("editor_custom_highlight", "Ctrl+J"))
        custom_hl_action.triggered.connect(self.apply_custom_highlight)
        self.btn_custom_hl.setDefaultAction(custom_hl_action)
        self.btn_custom_hl.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        
        custom_hl_menu = QMenu(self.btn_custom_hl)
        pick_color_action = QAction("Choose Color...", self)
        pick_color_action.triggered.connect(self.pick_custom_highlight_color)
        custom_hl_menu.addAction(pick_color_action)
        self.btn_custom_hl.setMenu(custom_hl_menu)

        self.action_color = QAction(get_premium_icon("color"), "Text Color", self)
        self.action_color.triggered.connect(self.text_color)
        self.action_color.setToolTip("Text Color")

        # 5. Headings & Lists
        self.combo_header = QComboBox()
        self.combo_header.addItems(["Par", "H1", "H2", "H3", "L1", "L2"])
        self.combo_header.currentIndexChanged.connect(self.text_heading)
        self.combo_header.setFixedWidth(50)
        self.combo_header.setToolTip("Text Style")

        self.combo_list = QComboBox()
        self.combo_list.addItems(["List", "•", "1.", "A.", "I.", "☑", "Ω"])
        self.combo_list.setFixedWidth(55)
        self.combo_list.setToolTip("List Style")
        self.combo_list.currentIndexChanged.connect(self.change_list_style)
        
        self.action_check = QAction(get_premium_icon("check"), "Checklist", self)
        self.action_check.setShortcut("Ctrl+Shift+C")
        self.action_check.triggered.connect(self.insert_checklist)
        
        self.action_indent = QAction(get_premium_icon("indent"), "Indent", self)
        self.action_indent.setShortcut("Tab")
        self.action_indent.triggered.connect(self.text_indent)
        
        self.action_outdent = QAction(get_premium_icon("outdent"), "Outdent", self)
        self.action_outdent.setShortcut("Shift+Tab")
        self.action_outdent.triggered.connect(self.text_outdent)
        
        self.action_bullet = QAction(get_premium_icon("list"), "Bullet List", self)
        self.action_bullet.setCheckable(True)
        self.action_bullet.triggered.connect(self.text_bullet)

        # 6. Navigation
        self.action_scroll_top = QAction(get_premium_icon("top"), "Scroll to Top", self)
        self.action_scroll_top.triggered.connect(self.scroll_to_top)

        self.action_scroll_bottom = QAction(get_premium_icon("bottom"), "Scroll to Bottom", self)
        self.action_scroll_bottom.triggered.connect(self.scroll_to_bottom)

        # 7. Structure & Inserts (Row 2 equivalent)
        # Level 1 Button
        self.lvl1_btn = QToolButton()
        self.lvl1_btn.setIcon(get_premium_icon("level1"))
        self.lvl1_btn.setToolTip("Level 1 Box")
        self.lvl1_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.lvl1_btn.setFixedWidth(40)
        self.lvl1_btn.clicked.connect(self.apply_level_1)
        
        lvl1_menu = QMenu(self.lvl1_btn)
        lvl1_color_action = QAction("Choose Color...", self)
        lvl1_color_action.triggered.connect(self._pick_level1_color)
        lvl1_menu.addAction(lvl1_color_action)
        self.lvl1_btn.setMenu(lvl1_menu)

        # Level 2 Button
        self.lvl2_btn = QToolButton()
        self.lvl2_btn.setIcon(get_premium_icon("level2"))
        self.lvl2_btn.setToolTip("Level 2 Box")
        self.lvl2_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.lvl2_btn.setFixedWidth(40)
        self.lvl2_btn.clicked.connect(self.apply_level_2)
        
        lvl2_menu = QMenu(self.lvl2_btn)
        lvl2_color_action = QAction("Choose Color...", self)
        lvl2_color_action.triggered.connect(self._pick_level2_color)
        lvl2_menu.addAction(lvl2_color_action)
        self.lvl2_btn.setMenu(lvl2_menu)

        self.action_code_block = QAction(get_premium_icon("square"), "Rectangular Box", self)
        self.action_code_block.triggered.connect(self.insert_code_block)
        self.action_code_block.setToolTip("Rectangular Box")

        self.action_note_box = QAction(get_premium_icon("bookmark"), "Insert Note Box", self)
        self.action_note_box.triggered.connect(self.insert_note_box)
        self.action_note_box.setToolTip("Insert Note Box")

        self.btn_hr = QToolButton()
        self.btn_hr.setIcon(get_premium_icon("hr"))
        self.action_hr = QAction(get_premium_icon("hr"), "", self)
        self.action_hr.setShortcut(self._get_shortcut("editor_insert_hr", "Ctrl+L"))
        self.action_hr.triggered.connect(self.insert_hr)
        self.btn_hr.setToolTip(f"Horizontal Line ({self._get_shortcut('editor_insert_hr', 'Ctrl+L')})")
        self.btn_hr.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_hr.setDefaultAction(self.action_hr)
        
        hr_menu = QMenu(self.btn_hr)
        thick_menu = hr_menu.addMenu("Thickness")
        for t in [1, 2, 3, 4, 5, 8, 10]:
            a = QAction(f"{t}px", self)
            a.triggered.connect(lambda checked, val=t: self.set_hr_thickness(val))
            thick_menu.addAction(a)
        col_action = QAction("Color...", self)
        col_action.triggered.connect(self.set_hr_color)
        hr_menu.addAction(col_action)
        self.btn_hr.setMenu(hr_menu)

        self.action_draw = QAction(get_premium_icon("palette"), "Drawing (Whiteboard)", self)
        self.action_draw.triggered.connect(self.insert_drawing)
        self.action_draw.setToolTip("Drawing (Whiteboard)")

        self.action_import_wb = QAction(get_premium_icon("image"), "Import Image", self)
        self.action_import_wb.setShortcut(self._get_shortcut("editor_import_image", "Ctrl+Shift+I"))
        self.action_import_wb.triggered.connect(self.import_whiteboard_image)
        self.action_import_wb.setToolTip(f"Import Image ({self._get_shortcut('editor_import_image', 'Ctrl+Shift+I')})")

        self.action_link = QAction(get_premium_icon("link"), "Link Note", self)
        self.action_link.setShortcut("Ctrl+K")
        self.action_link.triggered.connect(self.insert_link)
        self.action_link.setToolTip(f"Insert Link to Note ({self._get_shortcut('editor_insert_link', 'Ctrl+K')})")

        self.action_clear = QAction(get_premium_icon("trash"), "Clear All", self)
        self.action_clear.triggered.connect(self.clear)
        self.action_clear.setToolTip("Clear All Content")

        self.action_shortcuts = QAction(get_premium_icon("keyboard"), "Shortcuts", self)
        self.action_shortcuts.triggered.connect(self.requestShortcutDialog.emit)
        self.action_shortcuts.setToolTip("Keyboard Shortcuts")

        self.toc_action = QAction(get_premium_icon("list"), "TOC", self)
        self.toc_action.triggered.connect(self.toggle_toc)
        self.toc_action.setToolTip("Toggle Table of Contents")

        self.action_export = QAction(get_premium_icon("export"), "Export PDF", self)
        self.action_export.triggered.connect(self.exportNoteRequest.emit)
        self.action_export.setToolTip("Export Note as PDF")

    def get_toolbar_actions(self):
        """Returns ordered list of widgets/actions for the Main Window Title Bar."""
        return [
            self.combo_font,
            self.spin_size,
            self.action_font_inc,
            self.action_font_dec,
            "SEPARATOR",
            self.action_bold,
            self.action_italic,
            self.action_underline,
            self.action_strike,
            self.action_super,
            self.action_sub,
            "SEPARATOR",
            self.action_highlight,
            self.btn_custom_hl,
            self.action_color,
            "SEPARATOR",
            self.combo_header,
            "SEPARATOR",
            self.action_bullet,
            self.action_numbering,
            self.action_check,
            "SEPARATOR",
            self.action_indent,
            self.action_outdent,
            "SEPARATOR",
            self.lvl1_btn,
            self.lvl2_btn,
            self.action_code_block,
            self.action_note_box,
            self.btn_hr,
            "SEPARATOR",
            self.action_draw,
            self.action_import_wb,
            self.action_link, 
            "SEPARATOR",
            self.action_scroll_top,
            self.action_scroll_bottom,
            "SEPARATOR",
            self.action_clear,
            self.action_shortcuts,
            self.toc_action,
            "SEPARATOR",
            self.action_export
        ]

    def request_link_dialog(self):
        """Emit signal for opening link dialog."""
        self.request_open_link_dialog.emit()

    def insert_internal_link(self):
         self.request_open_link_dialog.emit()

    def set_theme_mode(self, mode):
        """Set the current theme mode (light/dark) to adjust highlighter colors."""
        old_mode = self.theme_mode
        self.theme_mode = mode
        
        # Refresh Toolbar Icons and Style
        self._refresh_toolbar_icons(mode)
        self._update_toolbar_style(mode)
        
        # Update FindBar Style
        self.find_bar.set_theme_mode(mode)
        
        # Update TOC Style
        self._update_toc_style()
        
        # Update Back Button Style
        self._update_back_btn_style(mode)
        
        # Sync Default Highlight Color (Theme Aware)
        try:
            import ui.styles as styles
            
            # Determine defaults for old and new modes
            
            # Auto-Refresh Level Boxes to ensure contrast is correct in new theme (though boxes rely on levelX_color, refreshing ensures consistency)
            self.renumber_all_levels()
            # Fallback to hardcoded known defaults if styles dict is missing specific keys to prevent crash
            # Fallback Highlight Colors (Yellow for light, darker Gold for dark)
            HIGHLIGHT_DEFAULTS = {
                "light": "#FFF176", 
                "dark": "#FACC15" # Yellow-400 (Shadcn/Tailwind friendly)
            }
            
            old_def_hex = HIGHLIGHT_DEFAULTS.get(old_mode, '#FFF176')
            new_def_hex = HIGHLIGHT_DEFAULTS.get(mode, '#FFF176')
            
            old_default = QColor(old_def_hex)
            new_default = QColor(new_def_hex)
            
            # Check if current color is using the generic 'cyan' fallback OR the old default
            # We want to migrate it to the new theme's default if it wasn't manually customized to something else
            current_hex = self.custom_highlight_color.name().upper()
            old_def_hex_norm = old_default.name().upper()
            
            # Also handle legacy "cyan" default
            if current_hex == old_def_hex_norm or current_hex == "#00FFFF":
                print(f"DEBUG: Migrating Highlight Color from {current_hex} to {new_default.name()}")
                self.custom_highlight_color = new_default
                if self.data_manager:
                    self.data_manager.set_setting("custom_highlight_color", new_default.name())
                
                # Update UI Button
                if hasattr(self, 'btn_custom_hl'):
                    self._update_custom_hl_icon(new_default)
                    
        except Exception as e:
            print(f"Error syncing highlight color: {e}")

    def _refresh_toolbar_icons(self, mode):
        """Updates toolbar icons based on the current theme."""
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        is_dark = mode == "dark"
        color = c['primary'] # Use Primary color for branding, or Foreground? 
        # Zen Design: Icons are usually branded or dark grey.
        # Let's use Foreground for general icons, Primary for specific ones if we wanted.
        # But 'color' arg in get_premium_icon sets the stroke.
        # Light: #3D3A38, Dark: #E7E5E4.
        color = c['foreground']
        
        def set_icon(action_attr, icon_name):
            if hasattr(self, action_attr):
                getattr(self, action_attr).setIcon(get_premium_icon(icon_name, color=color))

        # Core
        set_icon('action_search', 'search')
        set_icon('action_undo', 'undo')
        set_icon('action_redo', 'redo')
        
        # Formatting
        set_icon('action_bold', 'bold')
        set_icon('action_italic', 'italic')
        set_icon('action_underline', 'underline')
        set_icon('action_strike', 'strike')
        set_icon('action_super', 'superscript')
        set_icon('action_sub', 'subscript')
        set_icon('action_highlight', 'highlight')
        set_icon('action_color', 'color')
        set_icon('action_font_inc', 'plus_circle')
        set_icon('action_font_dec', 'minus_circle')
        set_icon('action_indent', 'indent')
        set_icon('action_outdent', 'outdent')
        set_icon('action_bullet', 'list')
        set_icon('action_numbering', 'list_ordered')
        set_icon('action_check', 'check_square')
        
        # Scroll
        set_icon('action_scroll_top', 'top')
        set_icon('action_scroll_bottom', 'bottom')
        
        # Insert
        set_icon('action_code_block', 'square')
        set_icon('action_note_box', 'bookmark')
        set_icon('action_hr', 'hr')
        if hasattr(self, 'btn_hr'):
            self.btn_hr.setIcon(get_premium_icon("hr", color=color))
            
        # Draw & Link
        set_icon('action_draw', 'palette')
        set_icon('action_import_wb', 'image')
        set_icon('action_link', 'link')
        set_icon('action_clear', 'trash')
        set_icon('action_shortcuts', 'keyboard')
        set_icon('toc_action', 'list')
        set_icon('action_export', 'export')
        
        # Tool Buttons
        if hasattr(self, 'lvl1_btn'):
            self.lvl1_btn.setIcon(get_premium_icon("level1", color=color))
        if hasattr(self, 'lvl2_btn'):
            self.lvl2_btn.setIcon(get_premium_icon("level2", color=color))
        
        if hasattr(self, 'btn_custom_hl'):
             # Custom update for highlight icon to keep the rainbow bar if we want,
             # but standard set_icon will overwrite it. 
             # Let's use the rainbow icon check
             self._update_custom_hl_icon(self.custom_highlight_color)

    def _update_back_btn_style(self, mode):
        """Dynamic styling for the floating back button."""
        c = styles.ZEN_THEME.get(mode, styles.ZEN_THEME["light"])
        is_dark = mode == "dark"
        
        bg = "#ECEFF1" if not is_dark else "#1F2937"
        fg = "#455A64" if not is_dark else "#E5E7EB"
        border = "#B0BEC5" if not is_dark else "#374151"
        hover_bg = "#CFD8DC" if not is_dark else "#374151"
        hover_fg = "#263238" if not is_dark else "#FFFFFF"
        
        # Or use Shadcn tokens for better consistency
        bg = c['secondary']
        fg = c['secondary_foreground']
        border = c['border']
        hover_bg = c['accent']
        hover_fg = c['accent_foreground']

        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 18px;
                padding: 8px 20px;
                font-weight: bold;
                font-family: 'Segoe UI';
                font-size: 13px;
                /* Subtle elevation effect */
                border-bottom: 2px solid {border};
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_fg};
                border-color: {c['ring']};
            }}
            QPushButton:pressed {{
                border-bottom: 1px solid {border};
                padding-top: 9px;
                padding-bottom: 7px;
            }}
        """)

    def _update_toolbar_style(self, mode):
        """Toolbar is now in the TitleBar, which handles its own styling."""
        pass

    def _update_toc_style(self):
        """Update TOC sidebar styling based on current theme mode."""
        if not hasattr(self, 'toc_list'): return
        
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        # Map Zen specific colors to TOC components
        panel_bg = c['background'] # Match editor background or slightly different?
        # To distinguish TOC, maybe use 'muted' or 'sidebar_bg'?
        panel_bg = c['sidebar_bg']
        header_bg = c['background']
        header_border = c['border']
        text_color = c['foreground']
        label_color = c['muted_foreground']
        item_border = c['border']
        selected_bg = c['active_item_bg']
        hover_bg = c['accent']
        handle_color = c['border']
        btn_color = c['muted_foreground']
        btn_hover = c['foreground']

        # Apply Styles
        self.editor_splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {handle_color}; }}")
        
        self.toc_header.setStyleSheet(f"background-color: {header_bg}; border-bottom: 1px solid {header_border};")
        self.lbl_toc.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 11px;")
        
        self.btn_close_toc.setStyleSheet(f"QPushButton {{ border: none; color: {btn_color}; font-weight: bold; }} QPushButton:hover {{ color: {btn_hover}; }}")

        self.toc_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {panel_bg};
                color: {text_color};
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {item_border};
            }}
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
        """)

    def resizeEvent(self, event):
        """Handle window resize and scale images proportionally."""
        super().resizeEvent(event)
        # Performance: Only resize if width actually changed
        current_width = self.editor.viewport().width()
        if abs(current_width - self._last_resize_width) > 10:
            self._last_resize_width = current_width
            # Use debounced timer to prevent frequent resizing
            self._resize_debounce_timer.start(300)  # 300ms delay
            
        # Reposition Find Bar if visible
        self._reposition_find_bar()
        
    def _reposition_find_bar(self):
        if hasattr(self, 'find_bar') and self.find_bar and self.find_bar.isVisible():
            # Position: Top-Right corner of the widget
            # Toolbar is now in TitleBar, so we use 0 offset from top
            toolbar_height = 0
            x = self.width() - self.find_bar.width() - 25 # 25px right margin
            y = toolbar_height + 10 # 10px top margin
            self.find_bar.move(x, y)
            self.find_bar.raise_() # Ensure on top

    def _resize_images_to_fit(self):
        """Resize all images to fit within the current editor width with performance optimizations."""
        try:
            doc = self.editor.document()
            if not doc:
                return
            
            # Calculate available width for images
            # Use the actual viewport width minus the margins we set in __init__
            # We set 30px left/right, so effective width is -60
            new_width = self.editor.viewport().width() - 60 
            
            if new_width < 100:
                return  # Too small, likely during initialization
            
            # REMOVED: conflicting setTextWidth and setPageSize calls
            # These were forcing the document layout to a fixed width which prevented
            # proper reflow during resize and caused text disappearance.
            # We now rely on setViewportMargins in __init__ for padding.
            
            # Iterate through all blocks and collect necessary image updates
            # We collect first and apply later to avoid modifying the document while iterating
            updates = []
            
            block = doc.begin()
            
            # Safety: Prevent infinite loops in case of corrupt document structure
            processed_blocks = 0
            MAX_BLOCKS = 100000 
            
            while block.isValid():
                if processed_blocks > MAX_BLOCKS:
                    print("Warning: Aborted image resize loop - excessive blocks detected.")
                    break
                processed_blocks += 1

                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid() and frag.charFormat().isImageFormat():
                        img_fmt = frag.charFormat().toImageFormat()
                        name = img_fmt.name()
                        
                        # CRITICAL FIX: Always try to get natural dimensions from resource first
                        # to prevent stretching beyond original size if cache was seeded with scaled values.
                        img_dims = None
                        try:
                            img = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(name))
                            if img and isinstance(img, QImage) and img.width() > 0:
                                img_dims = (img.width(), img.height())
                                # Update cache with true natural size
                                self._image_dimensions_cache[name] = img_dims
                        except:
                            pass

                        if not img_dims:
                            # Fallback to cache if resource fetch failed or isn't a QImage
                            img_dims = self._image_dimensions_cache.get(name)
                        
                        if not img_dims:
                            # Final fallback: handle data URI if not in resource yet
                            if name.startswith("data:image/"):
                                try:
                                    header, encoded = name.split(",", 1)
                                    import base64
                                    data = base64.b64decode(encoded)
                                    img = QImage.fromData(data)
                                    if img and not img.isNull():
                                        img_dims = (img.width(), img.height())
                                        self._image_dimensions_cache[name] = img_dims
                                except Exception:
                                    pass
                            
                            if not img_dims:
                                it += 1
                                continue
                        
                        img_width, img_height = img_dims
                    
                        # Calculate target width: fit to viewport but max out at original image width
                        # This PREVENTS STRETCHING
                        target_width = min(float(img_width), float(new_width))
                        
                        # Calculate proportional target height based on NATURAL aspect ratio
                        ratio = target_width / float(img_width)
                        target_height = img_height * ratio

                        # Check if this would actually change the current size
                        current_width = img_fmt.width()
                        
                        # Update if the size is different (handling both shrinking and growing back)
                        # We compare against current_width. If it's different, we update.
                        # This fixes the issue where images stayed small after window expansion.
                        if abs(current_width - target_width) > 1:
                            new_fmt = QTextImageFormat()
                            new_fmt.setName(name)
                            new_fmt.setWidth(target_width)
                            new_fmt.setHeight(target_height)
                            
                            updates.append((frag.position(), frag.length(), new_fmt))
                    
                    it += 1
                block = block.next()
                
            # Apply updates
            if updates:
                cursor = QTextCursor(doc)
                # Group formatting changes
                cursor.beginEditBlock()
                for pos, length, fmt in updates:
                    cursor.setPosition(pos)
                    cursor.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
                    cursor.mergeCharFormat(fmt)
                cursor.endEditBlock()
                
            # FORCE LAYOUT REFRESH: Mark contents dirty to ensure QTextDocument re-calculates layout
            doc.markContentsDirty(0, doc.characterCount())
            self.editor.viewport().update()
            
        except Exception as e:
            print(f"Error resizing images: {e}")

    def _get_shortcut(self, action_id, default=""):
        """Safely get a shortcut string from manager."""
        if self.shortcut_manager and hasattr(self.shortcut_manager, 'get_shortcut'):
            return self.shortcut_manager.get_shortcut(action_id)
        return default




    def text_bold(self):
        # Use clean format for merge to avoid side effects
        fmt = QTextCharFormat()
        current_weight = self.editor.currentCharFormat().fontWeight()
        # Toggle: If Bold (700) -> Normal (400), else -> Bold
        target_weight = QFont.Weight.Bold if current_weight != QFont.Weight.Bold else QFont.Weight.Normal
        fmt.setFontWeight(target_weight)
        self.editor.mergeCurrentCharFormat(fmt)

    def set_font_family(self, font_name):
        """Apply font family to selection."""
        fmt = QTextCharFormat()
        fmt.setFontFamily(font_name)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def set_highlight_color(self, color_name):
        """Quickly apply a specific highlight color."""
        self.text_highlight(color=color_name)

    # --- New Formatting Handlers ---

    def text_strike(self):
        fmt = self.editor.currentCharFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        self.editor.mergeCurrentCharFormat(fmt)

    def text_super(self):
        fmt = self.editor.currentCharFormat()
        align = fmt.verticalAlignment()
        if align == QTextCharFormat.VerticalAlignment.AlignSuperScript:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
        self.editor.mergeCurrentCharFormat(fmt)

    def text_sub(self):
        fmt = self.editor.currentCharFormat()
        align = fmt.verticalAlignment()
        if align == QTextCharFormat.VerticalAlignment.AlignSubScript:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
        self.editor.mergeCurrentCharFormat(fmt)

    def text_color(self):
        col = QColorDialog.getColor(self.editor.textColor(), self)
        if not col.isValid(): return
        fmt = self.editor.currentCharFormat()
        fmt.setForeground(col)
        self.editor.mergeCurrentCharFormat(fmt)

    def text_size(self, size):
        """Apply font size to selection."""
        fmt = self.editor.currentCharFormat()
        fmt.setFontPointSize(size)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus() # Return focus to editor
        
    def font_size_step_up(self):
        """Increase font size by 2."""
        val = self.spin_size.value()
        self.spin_size.setValue(min(val + 2, 72))
        
    def font_size_step_down(self):
        """Decrease font size by 2."""
        val = self.spin_size.value()
        self.spin_size.setValue(max(val - 2, 8))

    def update_format_ui(self):
        """Update toolbar widgets based on cursor position with recursion prevention."""
        # Block signals to prevent recursive updates
        self.spin_size.blockSignals(True)
        self.combo_header.blockSignals(True)
        self.combo_list.blockSignals(True)
        
        try:
            fmt = self.editor.currentCharFormat()
            
            # 1. Update Font Size
            size = fmt.fontPointSize()
            if size > 0:
                self.spin_size.setValue(int(size))
            else:
                 # Default size if none set (usually 12)
                self.spin_size.setValue(12)
                 
            # 2. Update Header Combo (Basic detection)
            # We check font size/weight to guess header level
            # This is a bit rough but works for our simple implementation
            weight = fmt.fontWeight()
            size = fmt.fontPointSize()
            
            if weight == QFont.Weight.Bold and size == 24:
                self.combo_header.setCurrentIndex(1) # H1
            elif weight == QFont.Weight.Bold and size == 18:
                self.combo_header.setCurrentIndex(2) # H2
            elif weight == QFont.Weight.Bold and size == 14:
                self.combo_header.setCurrentIndex(3) # H3
            else:
                self.combo_header.setCurrentIndex(0) # Paragraph

            # 3. Update List Combo
            # Check for checklist manually first
            cursor = self.editor.textCursor()
            # Get block text to check for checklist
            block_text = cursor.block().text()
            if block_text.startswith("☐ ") or block_text.startswith("☑ "):
                 self.combo_list.setCurrentIndex(5) # Checklist
            else:
                curr_list = cursor.currentList()
                if curr_list:
                    style = curr_list.format().style()
                    if style == QTextListFormat.Style.ListDisc:
                        self.combo_list.setCurrentIndex(1) # Bullet
                    elif style == QTextListFormat.Style.ListDecimal:
                        self.combo_list.setCurrentIndex(2) # Number
                    elif style == QTextListFormat.Style.ListUpperAlpha:
                        self.combo_list.setCurrentIndex(3) # Alpha
                    elif style == QTextListFormat.Style.ListUpperRoman:
                        self.combo_list.setCurrentIndex(4) # Roman
                    else:
                        self.combo_list.setCurrentIndex(0) # Unknown or other
                else:
                    self.combo_list.setCurrentIndex(0) # No List
        except Exception:
            pass  # Prevent UI update errors from crashing
        finally:
            self.spin_size.blockSignals(False)
            self.combo_header.blockSignals(False)
            self.combo_list.blockSignals(False)

    def insert_code_block(self):
        """Insert a Notion-style code block."""
        # Check theme for colors
        is_dark = getattr(self, "theme_mode", "light") == "dark"
        
        # Notion Colors
        bg_color = "#2d2d2d" if is_dark else "#F7F6F3"
        text_color = "#f8f8f2" if is_dark else "#37352F"
        border_color = "#444444" if is_dark else "#E0E0E0"
        
        # We use a Table to create the 'Block' effect
        html = f"""
        <br>
        <table width="100%" cellpadding="10" cellspacing="0" style="
            border-collapse: collapse; 
            background-color: {bg_color}; 
            border-radius: 4px; 
            border: 1px solid {border_color};
            font-family: Consolas, Monaco, monospace;
        ">
            <tr>
                <td style="color: {text_color}; font-family: Consolas, Monaco, monospace;">
                    <br>
                </td>
                <td width="30" style="vertical-align: top; text-align: right; padding: 5px;">
                     <a href="action://delete_level" style="text-decoration: none; color: #888888; font-weight: bold; font-size: 14px; font-family: Arial;">✕</a>
                </td>
            </tr>
        </table>
        <br>
        """
        self.editor.insertHtml(html)
        self.editor.setFocus()

    def text_heading(self, index):
        from PyQt6.QtGui import QTextBlockFormat
        cursor = self.editor.textCursor()
        
        # Handle Level 1 and Level 2 (new feature)
        if index == 4:  # Level 1
            self.apply_level_1()
            return
        elif index == 5:  # Level 2
            self.apply_level_2()
            return
        
        # We process the block format 
        # But for font size/weight we need char format applied to the selection or current block
        
        fmt = QTextCharFormat()
        
        if index == 0: # Paragraph
            fmt.setFontWeight(QFont.Weight.Normal)
            fmt.setFontPointSize(12)
        elif index == 1: # H1
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontPointSize(24)
        elif index == 2: # H2
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontPointSize(18)
        elif index == 3: # H3
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontPointSize(14)
            
        self.editor.mergeCurrentCharFormat(fmt)
        
        # Restore focus
        self.editor.setFocus()
    
    def apply_level_1(self):
        """Insert a Level 1 box with pre-filled number using a 2-column table for protection."""
        cursor = self.editor.textCursor()
        
        # Calculate next Level 1 number
        level1_count = self._count_levels_in_document(1)
        new_number = f"{self.base_note_index}.{level1_count + 1}"
        
        # Insert a table-based box
        # Cell 1: Number (nowrap to prevent ugly breaking)
        # Cell 2: Content (empty)
        # Cell 3: Delete Button
        # Force adaptive contrast color
        color = self.level1_color.name()
        text_col = self._get_contrast_text_color(self.level1_color)
        
        box_html = (
            f'<table width="100%" border="0" cellpadding="8" cellspacing="0" '
            f'style="background-color: {color}; margin-top: 8px; margin-bottom: 8px;">'
            f'<tr>'
            f'<td width="80" style="border-left: 4px solid #333333; vertical-align: top; padding-right: 5px; white-space: nowrap;">'
            f'<span style="font-weight: bold; font-size: 11pt; color: {text_col};">[{new_number}]</span>'
            f'</td>'
            f'<td style="vertical-align: top;">'
            f'<span style="font-size: 11pt; color: {text_col};"></span>' # Empty content, adaptive text
            f'</td>'
            f'<td width="1%" style="vertical-align: top; padding-left: 5px;">'
            f'<a href="action://delete_level" style="text-decoration: none; color: #444444; font-weight: bold; font-size: 12px; font-family: Arial;">✕</a>'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'<p></p>'
        )
        
        cursor.insertHtml(box_html)
        self.editor.setFocus()
        self.renumber_all_levels()
    
    def apply_level_2(self):
        """Insert a Level 2 box with pre-filled number using a 2-column table."""
        level1_count = self._count_levels_in_document(1)
        if level1_count == 0:
            QMessageBox.warning(self, "No Level 1 Found", "Level 2 requires at least one Level 1.")
            return
        
        cursor = self.editor.textCursor()
        current_level1, level2_count = self._get_current_level_context(cursor)
        if current_level1 == 0: current_level1 = level1_count
        
        new_number = f"{self.base_note_index}.{current_level1}.{level2_count + 1}"
        
        # Force Green color for Level 2 as requested if not set
        color = self.level2_color.name()
        text_col = self._get_contrast_text_color(self.level2_color)
        
        box_html = (
            f'<table width="95%" border="0" cellpadding="8" cellspacing="0" '
            f'style="background-color: {color}; margin-top: 8px; margin-bottom: 8px; margin-left: 30px;">'
            f'<tr>'
            f'<td width="80" style="border-left: 4px solid #666666; vertical-align: top; padding-right: 5px; white-space: nowrap;">'
            f'<span style="font-weight: bold; font-size: 10pt; color: {text_col};">[{new_number}]</span>'
            f'</td>'
            f'<td style="vertical-align: top;">'
            f'<span style="font-size: 10pt; color: {text_col};"></span>'
            f'</td>'
            f'<td width="1%" style="vertical-align: top; padding-left: 5px;">'
            f'<a href="action://delete_level" style="text-decoration: none; color: #444444; font-weight: bold; font-size: 12px; font-family: Arial;">✕</a>'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'<p></p>'
        )
        
        cursor.insertHtml(box_html)
        self.editor.setFocus()
        self.renumber_all_levels()
    
    def _count_levels_in_document(self, level):
        """Count how many level markers of a specific level exist based on text content."""
        text = self.editor.toPlainText()
        import re
        if level == 1:
            # Match [X.Y] at start of line
            pattern = r'^\s*\[\d+\.\d+\]'
        else:
            # Match [X.Y.Z] at start of line
            pattern = r'^\s*\[\d+\.\d+\.\d+\]'
            
        return len(re.findall(pattern, text, re.MULTILINE))
    
    def _get_current_level_context(self, cursor):
        """
        Determine which Level 1 we are currently under based on cursor position.
        Returns (current_level1_index, count_of_level2s_in_this_section).
        """
        # Scan blocks backwards from cursor to find the last Level 1
        curr_block = self.editor.document().findBlock(cursor.position())
        
        current_level1 = 0
        level2_count = 0
        
        # 1. Count global Level 1s up to this point
        import re
        l1_pattern = re.compile(r'^\s*\[\d+\.\d+\]')
        l2_pattern = re.compile(r'^\s*\[\d+\.\d+\.\d+\]')
        
        # Traverse from start to current block
        it_block = self.editor.document().begin()
        while it_block.isValid() and it_block.blockNumber() <= curr_block.blockNumber():
            text = it_block.text()
            if l1_pattern.match(text):
                current_level1 += 1
                level2_count = 0 # New section
            elif l2_pattern.match(text):
                level2_count += 1
            
            if it_block == curr_block:
                break
            it_block = it_block.next()
            
        # If we didn't find any L1, fall back to global count
        if current_level1 == 0:
            current_level1 = self._count_levels_in_document(1)
            
        return (current_level1, level2_count)

    def _get_contrast_text_color(self, bg_color):
        """Return 'black' or 'white' based on background brightness."""
        if not bg_color.isValid(): return "#000000"
        # Calculate luminance (standard formula)
        lum = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        return "#000000" if lum > 128 else "#FFFFFF"

    def renumber_all_levels(self):
        """Renumber all Level 1 and Level 2 boxes based on base_note_index using cursor traversal."""
        if self.base_note_index == 0:
            return
            
        import re
        l1_pattern = re.compile(r'^\s*\[(\d+\.\d+)\]')
        l2_pattern = re.compile(r'^\s*\[(\d+\.\d+\.\d+)\]')
        
        doc = self.editor.document()
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        level1_counter = 0
        level2_counter = 0
        current_level1 = 0
        
        block = doc.begin()
        while block.isValid():
            text = block.text()
            
            # Check for Level 1
            l1_match = l1_pattern.match(text)
            if l1_match:
                level1_counter += 1
                current_level1 = level1_counter
                level2_counter = 0
                
                new_number = f"{self.base_note_index}.{level1_counter}"
                current_number = l1_match.group(1)
                
                if new_number != current_number:
                    # Select just the number part [X.Y]
                    cursor.setPosition(block.position())
                    # Move past whitespace
                    while doc.characterAt(cursor.position()).isspace():
                        cursor.movePosition(cursor.MoveOperation.Right)
                    
                    # Select [
                    cursor.movePosition(cursor.MoveOperation.Right)
                    # Select number text
                    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(current_number))
                    
                    # Replace
                    cursor.insertText(new_number)
                
                # --- Fix Color Deeply (Adaptive Contrast - Robust) ---
                # Use stored level1_color to determine contrast, ensuring consistency even if HTML parsing delays
                color_bg = self.level1_color
                contrast_col = self._get_contrast_text_color(color_bg)
                
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(contrast_col))
                
                curr_table = cursor.currentTable()
                if curr_table:
                       # Update Table Background & Constraints
                       from PyQt6.QtGui import QTextLength
                       tf = curr_table.format()
                       tf.setBackground(color_bg)
                       
                       # Enforce Fixed Width for Number Column (80px) to prevent wrapping
                       constraints = [
                           QTextLength(QTextLength.Type.FixedLength, 80),
                           QTextLength(QTextLength.Type.VariableLength, 0),
                           QTextLength(QTextLength.Type.FixedLength, 30)
                       ]
                       tf.setColumnWidthConstraints(constraints)
                       curr_table.setFormat(tf)
                       
                       # Apply to Number Cell (0,0)
                       cell_num = curr_table.cellAt(0, 0)
                       if cell_num.isValid():
                           c_num = cell_num.firstCursorPosition()
                           c_num.setPosition(cell_num.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                           c_num.mergeCharFormat(fmt)
                       
                       # Apply to Content Cell (0,1)
                       cell_content = curr_table.cellAt(0, 1)
                       if cell_content.isValid():
                           c_cont = cell_content.firstCursorPosition()
                           c_cont.setPosition(cell_content.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                           c_cont.mergeCharFormat(fmt)
            
            else:
                l2_match = l2_pattern.match(text)
                if l2_match:
                    level2_counter += 1
                    
                    new_number = f"{self.base_note_index}.{current_level1}.{level2_counter}"
                    current_number = l2_match.group(1)
                    
                    if new_number != current_number:
                        cursor.setPosition(block.position())
                        while doc.characterAt(cursor.position()).isspace():
                            cursor.movePosition(cursor.MoveOperation.Right)
                        cursor.movePosition(cursor.MoveOperation.Right) # Skip [
                        cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(current_number))
                        cursor.insertText(new_number)

                    # --- Fix Color Deeply (Adaptive Contrast - Robust) ---
                    # Use stored level2_color
                    color_bg = self.level2_color
                    contrast_col = self._get_contrast_text_color(color_bg)
                    
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(contrast_col))
                    
                    curr_table = cursor.currentTable()
                    if curr_table:
                            # Update Table Background & Constraints
                            from PyQt6.QtGui import QTextLength
                            tf = curr_table.format()
                            tf.setBackground(color_bg)
                            
                            # Enforce Fixed Width for Number Column (80px)
                            constraints = [
                                QTextLength(QTextLength.Type.FixedLength, 80),
                                QTextLength(QTextLength.Type.VariableLength, 0),
                                QTextLength(QTextLength.Type.FixedLength, 30)
                            ]
                            tf.setColumnWidthConstraints(constraints)
                            curr_table.setFormat(tf)
                            
                            # Apply to Number Cell (0,0)
                            cell_num = curr_table.cellAt(0, 0)
                            if cell_num.isValid():
                                c_num = cell_num.firstCursorPosition()
                                c_num.setPosition(cell_num.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                                c_num.mergeCharFormat(fmt)
                            
                            # Apply to Content Cell (0,1)
                            cell_content = curr_table.cellAt(0, 1)
                            if cell_content.isValid():
                                c_cont = cell_content.firstCursorPosition()
                                c_cont.setPosition(cell_content.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                                c_cont.mergeCharFormat(fmt)
            
            block = block.next()
            
        cursor.endEditBlock()
    
    def set_base_note_index(self, index):
        """
        Called by MainWindow to set the current note's index.
        Triggers renumbering of all levels.
        """
        self.base_note_index = index
        self.renumber_all_levels()
        
    def _enforce_readonly_numbers(self):
        """
        1. Prevent user from editing the number cells in level boxes by moving cursor out.
        2. Enforce correct text contrast when typing in the content cell.
        """
        cursor = self.editor.textCursor()
        curr_table = cursor.currentTable()
        
        # Check if we are inside a table
        if curr_table:
            cell = curr_table.cellAt(cursor)
            # Check for Level Box Table (1 row, 2 cols usually, but we check number pattern)
            if curr_table.columns() >= 2 and cell.row() == 0:
                
                # Logic for Number Cell (0,0) - Read Only
                if cell.column() == 0:
                    block_text = cursor.block().text().strip()
                    import re
                    if re.match(r'^\[\d+(\.\d+)+\]$', block_text):
                        # Move to Content Cell
                        next_cell = curr_table.cellAt(0, 1)
                        if next_cell:
                            next_cursor = next_cell.firstCursorPosition()
                            self.editor.setTextCursor(next_cursor)
                            return # Cursor moved, handled.

                # Logic for Content Cell (0,1) - Enforce Contrast on Typing
                if cell.column() == 1:
                     # Identify Level based on Neighbour (0,0)
                     cell_zero = curr_table.cellAt(0, 0)
                     if cell_zero:
                         # We need to read text from cell_zero to identify Level 1 or 2
                         # Use a cursor to get text
                         c0 = cell_zero.firstCursorPosition()
                         # Text is in the block
                         text0 = c0.block().text().strip()
                         
                         target_color = None
                         import re
                         if re.match(r'^\[\d+\.\d+\]$', text0): # Level 1 [1.1]
                             target_color = self.level1_color
                         elif re.match(r'^\[\d+\.\d+\.\d+\]$', text0): # Level 2 [1.1.1]
                             target_color = self.level2_color
                             
                         if target_color:
                             # Enforce Contrast Color on Cursor AND Content
                             # This ensures that even if user types with wrong color (e.g. default white), it gets corrected immediately.
                             contrast = self._get_contrast_text_color(target_color)
                             
                             # 1. Apply to Existing Text in Cell (Fixes just-typed chars)
                             c_cell = cell.firstCursorPosition()
                             c_cell.setPosition(cell.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                             
                             new_fmt = QTextCharFormat()
                             new_fmt.setForeground(QColor(contrast))
                             c_cell.mergeCharFormat(new_fmt)
                             
                             # 2. Apply to Current Cursor (Fixes future typing)
                             # Check if strictly needed to avoid signal loops? 
                             # mergeCurrentCharFormat is safe.
                             if self.editor.currentCharFormat().foreground().color().name().upper() != contrast.upper():
                                  self.editor.mergeCurrentCharFormat(new_fmt)

    def _delete_level_box(self, cursor=None):
        """Remove the level box table at current cursor or provided cursor."""
        if cursor is None:
            cursor = self.editor.textCursor()
            
        table = cursor.currentTable()
        if table:
             # Strategy: Select from just before table to just after table
             # Table start position.
             t_pos = table.firstPosition()
             
             # Move cursor to before the table
             start_pos = t_pos - 1
             end_pos = table.lastPosition() + 1 # Include closing char
             
             c = self.editor.textCursor()
             c.setPosition(start_pos)
             c.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
             c.removeSelectedText()
             
             # Renumber remaining boxes
             self.renumber_all_levels()

    def _pick_level1_color(self):
        """Pick persistent color for Level 1."""
        from PyQt6.QtWidgets import QColorDialog
        col = QColorDialog.getColor(self.level1_color, self, "Select Level 1 Box Color")
        if col.isValid():
            self.level1_color = col
            if self.data_manager:
                self.data_manager.set_setting("level1_color", col.name())
            self.renumber_all_levels() # Apply new color to existing boxes

    def _pick_level2_color(self):
        """Pick persistent color for Level 2."""
        from PyQt6.QtWidgets import QColorDialog
        col = QColorDialog.getColor(self.level2_color, self, "Select Level 2 Box Color")
        if col.isValid():
            self.level2_color = col
            if self.data_manager:
                self.data_manager.set_setting("level2_color", col.name())
            self.renumber_all_levels() # Apply new color to existing boxes
        
    # --- Table of Contents Logic ---
    def toggle_toc(self):
        """Toggle TOC sidebar visibility."""
        # Use toc_panel instead of toc_list
        is_visible = self.toc_panel.isVisible()
        self.toc_panel.setVisible(not is_visible)
        
        # Save Persistence
        if self.data_manager:
              self.data_manager.set_setting("show_toc", "true" if not is_visible else "false")
              
        if not is_visible:
            self.refresh_toc()
            
    def refresh_toc(self):
        """Scan document for Level Headers and populate TOC."""
        self.toc_list.clear()
        doc = self.editor.document()
        block = doc.begin()
        
        import re
        # Pattern to find Level Numbers: [1.1] or [1.1.1]
        # Allow optional spaces inside brackets: [ 1.1 ]
        pattern = re.compile(r'^\[\s*(\d+(?:\.\d+)+)\s*\]')
        
        # DEBUG: Print scan start
        # logger is implicit or use print for now
        # print("DEBUG: Starting TOC Refresh...")
        
        while block.isValid():
            text = block.text().strip()
            # print(f"DEBUG: Scanning Block: '{text}'") # Keep this commented to avoid spam, or uncomment if needed
            



            # Check for Level Boxes [1.1]
            match = pattern.match(text)
            if match:
                # Level Box Logic
                content_block = block.next()
                content_text = content_block.text().strip() if content_block.isValid() else ""
                
                level = match.group(1) # "1.1"
                display_text = f"{level} {content_text}"
                
                dots = level.count('.')
                indent = "    " * (dots - 1) if dots > 1 else ""
                
                item = QListWidgetItem(f"{indent}{display_text}")
                item.setData(Qt.ItemDataRole.UserRole, block.position())
                item.setToolTip(display_text)
                self.toc_list.addItem(item)
                
            # 2. Standard Headers (H1-H3) are EXCLUDED per user request.
            # Only Level Boxes ([1.1], [1.1.1]) are shown.
            
            block = block.next()
            
    def _on_toc_item_clicked(self, item):
        """Scroll to the selected header."""
        pos = item.data(Qt.ItemDataRole.UserRole)
        if pos is not None:
            cursor = self.editor.textCursor()
            cursor.setPosition(pos)
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()
            self.editor.setFocus()

    # --- End New Handlers ---

    # ... (rest of old handlers below) ...

    # ... (handlers) ...


    def insert_image_from_path(self, file_path, metadata=None):
        """Public method to insert image from a given path.
        
        Args:
            file_path: Path to the image file
            metadata: Optional dictionary with image metadata (e.g. whiteboard page)
        """
        if file_path:
            from PyQt6.QtGui import QImage
            image = QImage(file_path)
            if not image.isNull():
                # Provide dict with meta to preserve path
                meta = {'path': file_path}
                
                # Merge provided metadata
                if metadata:
                    meta.update(metadata)
                    # Mark as whiteboard for edit button if applicable
                    if 'wb_page' in metadata:
                        meta['bg_mode'] = True 
                
                data = {
                    'view': image,
                    'source': image,
                    'meta': meta
                }
                self._process_and_insert_image(data)

    def eventFilter(self, obj, event):
        """Handle clicks on Edit buttons in editor"""
        if obj == self.editor and event.type() == QEvent.Type.MouseButtonRelease:
            anchor = self.editor.anchorAt(event.pos())
            if anchor:
                if anchor.startswith("action://edit/"):
                    res_name = anchor.split('/')[-1]
                    self._handle_edit_whiteboard(res_name)
                    return True
        return super().eventFilter(obj, event)

    def _handle_edit_whiteboard(self, res_name):
        """Handle Edit button click"""
        import json
        meta_json = self.whiteboard_images.get(res_name + "_meta")
        if meta_json:
            try:
                meta = json.loads(meta_json)
                # Inject resource name so MainWindow knows WHICH image we are editing
                meta['_res_name'] = res_name
                self.edit_whiteboard_requested.emit(meta)
            except Exception as e:
                print(f"Error parsing metadata for edit: {e}")

    def insert_image_from_file(self):
        # Legacy/Internal usage fallback if needed, but primarily used via signal now
        self.requestInsertImage.emit()

    whiteboard_active = False

    def insert_drawing_split_view(self):
        """Launch whiteboard in split view mode"""
        self._launch_whiteboard_split()

    def _launch_whiteboard_split(self):
        """Launch external Scrble Ink application in split view."""
        import subprocess
        import sys
        import os
        from PyQt6.QtWidgets import QMessageBox
        
        # Path to external app
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrble_ink1.py")
        
        if not os.path.exists(script_path):
            self.show_message(QMessageBox.Icon.Critical, "Error", f"External whiteboard app not found at:\n{script_path}")
            return
            
        try:
            # Calculate Geometry for Split View Overlay (Left 50%)
            parent = self.window()
            if parent:
                geo = parent.geometry()
                
                # We need global coordinates
                pos = parent.mapToGlobal(parent.rect().topLeft())
                
                x = geo.x()
                y = geo.y()
                w = geo.width() // 2
                h = geo.height()
                
                # Use frameless and always-on-top for split view effect
                args = [
                    sys.executable, script_path,
                    "--x", str(x),
                    "--y", str(y),
                    "--width", str(w),
                    "--height", str(h),
                    "--always-on-top",
                    "--frameless"
                ]
                
                # Determine persistent whiteboard file for current folder
                if hasattr(self, 'current_folder') and self.current_folder:
                     folder_path = self.data_manager.get_folder_path(self.current_folder)
                     if folder_path:
                         wb_path = os.path.join(folder_path, "whiteboard.json")
                         args.extend(["--file", wb_path])
                
                from PyQt6.QtCore import QProcess

                # Cleanup previous process
                self.cleanup()
                
                # Setup QProcess
                self.whiteboard_process = QProcess(self)
                self.whiteboard_process.setProgram(sys.executable)
                q_args = [script_path] + args[2:]
                
                # Handle Output for IPC
                def handle_stdout():
                    data = self.whiteboard_process.readAllStandardOutput().data().decode().strip()
                    if "IPC_SAVE_IMAGE:" in data:
                        for line in data.split('\n'):
                            if line.startswith("IPC_SAVE_IMAGE:"):
                                image_path = line.split(":", 1)[1].strip()
                                self.insert_image_from_path(image_path, is_whiteboard=True)
                                
                self.whiteboard_process.readyReadStandardOutput.connect(handle_stdout)
                
                # Start
                self.whiteboard_process.start(sys.executable, q_args)
                
                # Connect finished signal to restore view when whiteboard closes
                self.whiteboard_process.finished.connect(self.restore_full_view)

                # Split View Effect: Shift Text Editor Content to the Right
                if hasattr(self, 'editor'):
                    wb_right = x + w
                    
                    editor_pos = self.editor.mapToGlobal(self.editor.rect().topLeft())
                    editor_left = editor_pos.x()
                    
                    # Calculate overlap
                    if editor_left < wb_right:
                        overlap = wb_right - editor_left
                        margin = overlap + 20 
                        self.editor.setViewportMargins(margin, 0, 0, 0)
                    else:
                        self.editor.setViewportMargins(0, 0, 0, 0)

            else:
                subprocess.Popen([sys.executable, script_path])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch whiteboard:\n{str(e)}")

    def insert_drawing(self):
        """Launch whiteboard in split view - call MainWindow method"""
        # Find main window and call show_whiteboard_split_view()
        parent = self.window()
        if parent and hasattr(parent, 'show_whiteboard_split_view'):
            parent.show_whiteboard_split_view()
        else:
            # Fallback: Show message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Whiteboard", "Split view whiteboard not available in this context.")


    def restore_full_view(self):
        """Reset editor view to full width and close whiteboard."""
        # Note: Main logic now in main_window.py
        # This is kept for compatibility but can be simplified
        
        # 1. Reset Margins
        if hasattr(self, 'editor'):
            self.editor.setViewportMargins(0, 0, 0, 0)
            self.editor.viewport().update()
            
        # 2. Close Whiteboard Subprocess if exists
        if hasattr(self, 'whiteboard_process') and self.whiteboard_process:
            try:
                self.whiteboard_process.terminate()
                self.whiteboard_process = None
            except Exception as e:
                print(f"Error closing whiteboard: {e}")





    def import_whiteboard_image(self):
        """Manually import an image saved from the whiteboard."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from PyQt6.QtGui import QImage
        import os
        
        # Load settings to get last used directory from DataManager
        from util.logger import logger
        
        last_dir = ""
        if self.data_manager:
            last_dir = self.data_manager.get_setting("last_image_import_dir", "")
        
        target_dir = last_dir
        if not target_dir or not os.path.exists(target_dir):
             target_dir = os.path.expanduser("~/Pictures") 
        
        logger.debug(f"Import Image - Target Dir: {target_dir}")
        
        target_file = None
        # Try to find the latest image file to pre-select
        if os.path.exists(target_dir):
            try:
                extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
                files = [os.path.join(target_dir, f) for f in os.listdir(target_dir)]
                images = [f for f in files if os.path.isfile(f) and f.lower().endswith(extensions)]
                
                logger.debug(f"Found {len(images)} images in directory.")
                
                if images:
                    # Debug Sorting
                    images_sorted = sorted(images, key=os.path.getmtime, reverse=True)
                    latest_img = images_sorted[0]
                    target_file = os.path.normpath(latest_img)
                    
                    import datetime
                    ts = os.path.getmtime(latest_img)
                    dt = datetime.datetime.fromtimestamp(ts)
                    logger.debug(f"Latest Image Identified: {os.path.basename(latest_img)} ({dt})")
                else:
                    logger.debug("No images found to pre-select.")

            except Exception as e:
                logger.error(f"Error finding latest image: {e}")

        # Use standard QFileDialog.getOpenFileName which invokes the Native Windows Dialog
        # We pass the full path of the latest file as the 'directory' argument to pre-select it.
        
        norm_dir = os.path.normpath(target_dir)
        norm_dir = os.path.normpath(target_dir)
        initial_selection = norm_dir
        if target_file and os.path.exists(target_file):
            initial_selection = os.path.normpath(target_file)
            logger.debug(f"Invoking Native Dialog with selection: {initial_selection}")
            
        # Update title to help user understand they control the sort order
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Image (Right-Click > Sort by Date to fix order)", initial_selection, 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.PNG *.JPG *.JPEG *.BMP *.GIF);;All Files (*)"
        )
        
        if file_path:
            logger.debug(f"User selected: {file_path}")
            
            # Save directory for next time
            try:
                directory = os.path.dirname(file_path)
                if self.data_manager:
                    self.data_manager.set_setting("last_image_import_dir", directory)
                    self.data_manager.save_data() 
            except Exception as e:
                logger.error(f"Warning: Could not save settings: {e}")
            
            image = QImage(file_path)
            if not image.isNull():
                data = {
                    'view': image,
                    'source': image,
                    'meta': {'path': file_path}
                }
                self._process_and_insert_image(data)
                QMessageBox.information(self, "Success", "Image imported successfully!")
            else:
                 QMessageBox.critical(self, "Error", "Failed to load image. It may be corrupted or in an unsupported format.")



    # --- Search Implementation ---
    def toggle_find_bar(self):
        if self.find_bar.isVisible():
            self.find_bar.close_bar()
        else:
            self.find_bar.show_bar()
            self._reposition_find_bar()
            
    def find_text(self, text, forward=True):
        if not text: 
            self.find_bar.lbl_count.setText("")
            return
        
        # Use find flags
        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        
        # Perform Search
        found = self.editor.find(text, flags)
        
        if not found:
            # Wrap Around logic
            cursor = self.editor.textCursor()
            if forward:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            
            # Try again
            found = self.editor.find(text, flags)
            
        # Match Counting Logic (Perform full scan)
        # Match Counting Logic (Iterative Find for consistency)
        # Match Counting Logic (Iterative Find for consistency)
        doc = self.editor.document()
        try:
            # Save current position
            current_cursor = self.editor.textCursor()
            current_sel_start = current_cursor.selectionStart()
            
            # Helper to find all
            temp_cursor = QTextCursor(doc)
            temp_cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            match_starts = []
            
            # Use basic flags for searching (without backward)
            search_flags = QTextDocument.FindFlag(0)
            
            # Loop to find all occurrences
            while True:
                # Find from current temp_cursor
                result_cursor = doc.find(text, temp_cursor, search_flags)
                if result_cursor.isNull():
                    break
                    
                start_pos = result_cursor.selectionStart()
                
                # Prevent infinite loop if empty match (unlikely with text requirement)
                if result_cursor.position() == temp_cursor.position() and not result_cursor.hasSelection():
                     temp_cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
                     continue
                     
                match_starts.append(start_pos)
                temp_cursor = result_cursor
            
            total_matches = len(match_starts)
            current_idx = 0
            
            if total_matches > 0:
                 # Find which match corresponds to current selection
                 # We look for the match that starts exactly at current_sel_start
                 try:
                     # 1-based index
                     current_idx = match_starts.index(current_sel_start) + 1
                 except ValueError:
                     # Fallback: find nearest match <= current position
                     import bisect
                     idx = bisect.bisect_right(match_starts, current_sel_start)
                     current_idx = idx if idx > 0 else 1
            
            if total_matches > 0:
                self.find_bar.lbl_count.setText(f"{current_idx}/{total_matches}")
            else:
                self.find_bar.lbl_count.setText("0/0")

        except Exception as e:
            print(f"Count Error: {e}")
            self.find_bar.lbl_count.setText("?")

        # Visual Feedback
        if found:
            self.find_bar.inp_search.setStyleSheet("border: 1px solid #ccc; padding: 2px 5px; background: white; color: black;")
            self.editor.ensureCursorVisible()
            self.editor.setFocus() 
            self.find_bar.inp_search.setFocus()
        else:
            self.find_bar.inp_search.setStyleSheet("border: 1px solid red; background: #fee; padding: 2px 5px; color: black;")
            self.find_bar.lbl_count.setText("0/0")



    def _editor_key_press(self, event):
        """Custom key press handler for auto-list behavior and shortcuts."""
        
        # Dynamic Shortcut Handling
        if self.shortcut_manager:
            from PyQt6.QtGui import QKeySequence
            
            # Construct key string to match (same logic as in ShortcutDialog)
            key_val = event.key()
            mods = event.modifiers()
            
            # We construct a QKeySequence from key + mods
            # But we must be careful. QKeySequence(key | mods) works usually.
            qt_key = key_val
            mod_val = 0
            if mods & Qt.KeyboardModifier.ControlModifier:
                mod_val |= Qt.Modifier.CTRL.value
            if mods & Qt.KeyboardModifier.ShiftModifier:
                mod_val |= Qt.Modifier.SHIFT.value
            if mods & Qt.KeyboardModifier.AltModifier:
                mod_val |= Qt.Modifier.ALT.value
            if mods & Qt.KeyboardModifier.MetaModifier:
                mod_val |= Qt.Modifier.META.value
            
            final_key = qt_key | mod_val
            
            seq_str = QKeySequence(final_key).toString()
            
            # Check if this key maps to a Global action
            # If so, we MUST ignore it so it bubbles up to MainWindow
            mapped_action = None
            if hasattr(self.shortcut_manager, 'get_action_for_key'):
                mapped_action = self.shortcut_manager.get_action_for_key(seq_str)
                
            if mapped_action and mapped_action.startswith("global_"):
                event.ignore()
                return

            # Helper to check match
            def check(action_id):
                target = self._get_shortcut(action_id)
                return target and seq_str == target
                
            if check("editor_insert_note_box"):
                self.insert_note_box()
                return
            elif check("editor_insert_drawing"):
                self.insert_drawing()
                return
            elif check("editor_smart_copy"):
                # Smart Copy Logic
                if not self.editor.textCursor().hasSelection():
                    self.insert_code_block()
                    return
                # Else fall through to normal copy
        
        # Legacy Fallback (keeping for safety if shortcut manager fails/missing, though initialized in init)
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_N:
                self.insert_note_box()
                return
            elif event.key() == Qt.Key.Key_Q:
                self.insert_drawing()
                return
            elif event.key() == Qt.Key.Key_C:
                if not self.editor.textCursor().hasSelection():
                    self.insert_code_block()
                    return

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            cursor = self.editor.textCursor()
            
            # If pressing enter at the start of a line, just insert a new line above (default behavior)
            # Do NOT trigger auto-list logic, which would duplicate the symbol onto the new line
            if cursor.atBlockStart():
                QTextEdit.keyPressEvent(self.editor, event)
                return

            block_text = cursor.block().text()
            
            # 1. Checklist Auto-Continue
            if block_text.startswith("☐ ") or block_text.startswith("☑ "):
                 # Check if line is "empty" (just the checklist prefix)
                 if block_text.strip() in ["☐", "☑"]:
                     # Terminate list: clear line
                     cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                     cursor.removeSelectedText()
                     cursor.insertBlock() # Insert clean new block
                     self.editor.setTextCursor(cursor)
                     return
                 else:
                     # Continue list
                     QTextEdit.keyPressEvent(self.editor, event)
                     self.editor.insertPlainText("☐ ")
                     return

            # 2. Custom Symbol Auto-Continue
            # We check for our defined symbols
            symbols = ["→", "↑", "↓", "↔", "↕", "★", "☆", "○", "●", "□", "■", "☺", "☹", "♥", "♦", "♣", "♠", "✓", "✗", "∞", "≈", "≠", "≤", "≥", "±", "÷", "×", "°", "π", "Ω", "μ", "Σ", "€", "£", "¥", "©", "®", "™", "§", "¶", "†"]
            
            matched_sym = None
            for sym in symbols:
                # Check for symbol start (with or without space)
                # We check "startswith(sym)" but ensure we don't match partial words if sym is a letter (A, I, etc.)
                # But our symbols are special chars, so safe to check directly.
                if block_text.startswith(sym):
                    matched_sym = sym
                    break
            
            if matched_sym:
                 # Check if line is "empty" (just the symbol, with optional space)
                 if block_text.strip() == matched_sym:
                     # Terminate list
                     cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                     cursor.removeSelectedText()
                     cursor.insertBlock()
                     self.editor.setTextCursor(cursor)
                 else:
                     # Continue list
                     QTextEdit.keyPressEvent(self.editor, event)
                     self.editor.insertPlainText(f"{matched_sym} ")
                 return

        # Default handler
        QTextEdit.keyPressEvent(self.editor, event)

    def _toggle_checklist_char(self, cursor, char):
        """Helper to toggle checklist characters."""
        if char == "☐":
             cursor.insertText("☑")
             return True
        elif char == "☑":
              cursor.insertText("☐")
              return True
        return False

    def _handle_image_action(self, url, cursor=None):
        """Handle clicks on edit/delete links for whiteboard images and level boxes."""
        url_str = url.toString()
        
        # New: Handle Level Box Delete
        if url_str == "action://delete_level":
            self._delete_level_box(cursor=cursor)
            return
        
        if url_str.startswith("action://"):
            parts = url_str.replace("action://", "").split("/")
            if len(parts) == 2:
                action, res_name = parts
                if action == "delete":
                    self._delete_whiteboard_image(res_name)
                elif action == "edit":
                    self._edit_whiteboard_image(res_name)
                elif action == "view":
                    self._view_external_image(res_name)
                elif action == "refresh":
                    self._refresh_external_image(res_name)
                if action == "delete":
                    self._delete_whiteboard_image(res_name)
                elif action == "edit":
                    self._edit_whiteboard_image(res_name)
                elif action == "view":
                    self._view_external_image(res_name)
                elif action == "refresh":
                    self._refresh_external_image(res_name)


    def handle_link_click(self, url):
        """Handle link clicks from the editor."""
        qurl = QUrl(url)
        scheme = qurl.scheme()
        
        if scheme == "note":
            # note://uuid?overlay=true
            note_id = qurl.host()
            query = qurl.query()
            
            if "overlay=true" in query:
                self.request_open_note_overlay.emit(note_id)
            else:
                self.request_open_note.emit(note_id)
                
        else:
            # Open External Link
            QDesktopServices.openUrl(qurl)

    def insert_link(self):
        """Open dialog to insert a link to another note."""
        if not self.data_manager:
            return
            
        from ui.link_note_dialog import LinkNoteDialog
        
        # Get current note ID if possible (from parent or context)
        # TextEditor doesn't strictly know its Note ID unless passed.
        # But we can pass None for now or try to find it.
        # Actually, MainWindow usually manages the editor content.
        # We can try to traverse up or just pass None.
        current_note_id = None
        # Optimization: We could store current_note_id in TextEditor if needed.
        
        dialog = LinkNoteDialog(self, self.data_manager, current_note_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_id = dialog.selected_note_id
            note_title = dialog.selected_note_title
            
            if note_id and note_title:
                # Insert HTML Link
                # <a href="note://uuid?overlay=true">Title</a>
                
                url = f"note://{note_id}"
                if getattr(dialog, 'open_in_overlay', False):
                    url += "?overlay=true"
                    
                # Use insertHtml for clickable link
                # Style as a yellow button using TABLE for better block behavior and padding support
                # Qt supports cellpadding in tables which mimics padding better than spans
                # New "Pill" style for internal links (Indigo theme)
                link_html = (
                    f'&nbsp;<table border="0" cellpadding="0" cellspacing="0" style="background-color: #E8EAF6; border: 1px solid #C5CAE9; border-radius: 12px; margin: 2px;">'
                    f'<tr><td style="padding: 4px 12px;">'
                    f'<a href="{url}" style="text-decoration: none; color: #3F51B5; font-weight: bold; font-family: Segoe UI; font-size: 13px;">'
                    f'{note_title}</a>'
                    f'</td></tr></table>&nbsp;'
                )
                print(f"DEBUG: INSERTING LINK HTML: {link_html}")
                self.editor.insertHtml(link_html)
                
                # Reset cursor format to avoid typing inside the link
                cursor = self.editor.textCursor()
                original_format = QTextCharFormat()
                cursor.setCharFormat(original_format)
                self.editor.setTextCursor(cursor)
                self.editor.setFocus()

    def _view_external_image(self, res_name):
        """Open the image in the default system viewer."""
        import os
        import json
        import tempfile
        from PyQt6.QtCore import QByteArray
        
        # 1. Check if we have a real file path
        meta_json = self.whiteboard_images.get(res_name + "_meta")
        file_path = None
        if meta_json:
            try:
                meta = json.loads(meta_json)
                if 'path' in meta and os.path.exists(meta['path']):
                    file_path = meta['path']
            except:
                pass
        
        # 2. If no path, save to temp file
        if not file_path:
            # Check for source b64
            source_b64 = self.whiteboard_images.get(res_name + "_source")
            if not source_b64:
                # Fallback to view
                source_b64 = self.whiteboard_images.get(res_name)
                
            if source_b64:
                try:
                    data = QByteArray.fromBase64(source_b64.encode())
                    # Create a named temp file that persists until app close or user saves elsewhere
                    # We use .png by default
                    tfile = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    tfile.write(data.data())
                    tfile.close()
                    file_path = tfile.name
                    
                    # Store this temp path in meta so "Refresh" can find it later
                    # (Only for this session)
                    if meta_json:
                         meta = json.loads(meta_json)
                    else:
                         meta = {}
                    meta['path'] = file_path
                    meta['is_temp'] = True
                    self.whiteboard_images[res_name + "_meta"] = json.dumps(meta)
                except Exception as e:
                    print(f"Error creating temp file: {e}")
                    return

        # 3. Open
        if file_path:
            # Register for auto-refresh
            self._watch_image_path(res_name, file_path)
            
            try:
                os.startfile(file_path)
            except Exception as e:
                print(f"Error opening file: {e}")

    def _handle_file_change(self, path):
        """Handle auto-refresh when watched file changes."""
        path = path.replace("\\", "/")
        if path in self.watched_images:
            # FIX: Skip if we're already refreshing this file to prevent infinite loop
            if path in self._refreshing_files:
                return
            
            # File changed! Refresh associated images
            res_names = self.watched_images[path]
            for res_name in res_names:
                # Mark this file as being refreshed
                self._refreshing_files.add(path)
                # Add tiny delay to ensure write is complete
                QTimer.singleShot(100, lambda r=res_name: self._refresh_external_image(r))

    def _watch_image_path(self, res_name, path):
        """Register path for auto-refresh monitoring."""
        path = path.replace("\\", "/")
        if path not in self.watched_images:
            self.watched_images[path] = []
            self.file_watcher.addPath(path)
            
        if res_name not in self.watched_images[path]:
            self.watched_images[path].append(res_name)

    def _refresh_external_image(self, res_name, retry_count=0):
        """Reload image from its source path."""
        import os
        import json
        from PyQt6.QtGui import QImage
        from PyQt6.QtCore import QUrl
        
        # 1. Get path
        meta_json = self.whiteboard_images.get(res_name + "_meta")
        file_path = None
        if meta_json:
            try:
                meta = json.loads(meta_json)
                if 'path' in meta and os.path.exists(meta['path']):
                    file_path = meta['path']
            except:
                pass
        
        if file_path:
            # Register for auto-refresh since we are refreshing it now
            self._watch_image_path(res_name, file_path)
            
            try:
                # Reload QImage
                new_img = QImage(file_path)
                if not new_img.isNull():
                    # Update Doc Resource
                    # Use existing doc
                    doc = self.editor.document()
                    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), new_img)
                    
                    # Update Base64 storage (Source)
                    # We need to re-encode to update persistence
                    def img_to_b64(img, quality=100):
                        from PyQt6.QtCore import QBuffer, QIODevice
                        ba = QByteArray()
                        buf = QBuffer(ba)
                        buf.open(QIODevice.OpenModeFlag.WriteOnly)
                        img.save(buf, "PNG", quality=quality)
                        return ba.toBase64().data().decode()
                        
                    self.whiteboard_images[res_name + "_source"] = img_to_b64(new_img, quality=100)
                    # ... (rest of function)
                    
                    # Force View Update
                    self.editor.setLineWrapColumnOrWidth(self.editor.lineWrapColumnOrWidth()) 
                    # Hack to force layout update? Or simpler:
                    self.editor.viewport().update()
                    
                    # FIX: Remove file from refreshing set after successful refresh
                    if file_path in self._refreshing_files:
                        self._refreshing_files.discard(file_path)
                    
                    self.contentChanged.emit() # Save changes
                    
                    # Visual feedback? (Optional or small)
                    # from PyQt6.QtWidgets import QApplication
                    # QApplication.instance().activeWindow().statusBar().showMessage(f"Refreshed image from {os.path.basename(file_path)}", 3000)
                else:
                    # Image is null - likely still being written, retry
                    if retry_count < 3:
                        from PyQt6.QtCore import QTimer
                        delay = 200 * (2 ** retry_count)  # 200ms, 400ms, 800ms
                        QTimer.singleShot(delay, lambda: self._refresh_external_image(res_name, retry_count + 1))
            except Exception as e:
                # File locked or corrupted during write - retry
                if retry_count < 3:
                    from PyQt6.QtCore import QTimer
                    delay = 200 * (2 ** retry_count)  # 200ms, 400ms, 800ms
                    QTimer.singleShot(delay, lambda: self._refresh_external_image(res_name, retry_count + 1))
                # Silently fail after max retries - will refresh on next file change

    # ... delete method ...

    def _insert_image_controls(self, cursor, res_name):
        """Insert edit/delete controls for whiteboard images using a VERTICAL layout on the Right."""
        # Define theme-aware styles for BUTTONS
        if self.theme_mode == "light":
            btn_style = "text-decoration: none; color: black; background: #e3f2fd; padding: 6px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #007ACC; display: inline-block; width: 60px; text-align: center; margin-bottom: 5px;"
            del_style = "text-decoration: none; color: black; background: #ffebee; padding: 6px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #d32f2f; display: inline-block; width: 60px; text-align: center; margin-bottom: 5px;"
        else:
            btn_style = "text-decoration: none; color: white; background: #007ACC; padding: 6px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #005a9e; display: inline-block; width: 60px; text-align: center; margin-bottom: 5px;"
            del_style = "text-decoration: none; color: white; background: #d32f2f; padding: 6px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #b71c1c; display: inline-block; width: 60px; text-align: center; margin-bottom: 5px;"
        
        # We need to wrap the PREVIOUS image in a table structure. 
        # But wait, the image is already inserted. Modifying structure backwards is hard in QTextCursor.
        # It's better to insert the Table structure first, then put image in Cell 1 and Buttons in Cell 2.
        # BUT this method is called AFTER image insertion.
        
        # New Strategy: The caller (`_insert_processed_image`) should handle the Table structure.
        # This method just returns the HTML for the buttons? No, it inserts.
        # Let's Modify THIS method to effectively "wrap" the preceding image? No, risky.
        
        # Let's assume we modify `_process_and_insert_image` to create the table structure and call this 
        # to get button HTML. 
        # OR better: We simply insert a Table here, and move the previous character (the Image) into it? 
        # Moving images in QTextEdit is tricky.
        
        # EASIEST PATH: Update `_insert_processed_image` (and sync) to generate the full Table HTML directly,
        # instead of Image then Controls.
        pass # We will modify the caller instead.

    def _get_image_controls_html(self, res_name, is_whiteboard=False):
        """Generate vertical button HTML for image controls."""
        if self.theme_mode == "light":
            # Light Mode: Clean white/grad buttons
            btn_style = "text-decoration: none; color: black; background: #f5f5f5; padding: 6px; border-radius: 4px; font-size: 16px; border: 1px solid #ccc; display: block; text-align: center; margin: 2px 0; width: 32px;"
            del_style = "text-decoration: none; color: white; background: #e53935; padding: 6px; border-radius: 4px; font-size: 16px; border: 1px solid #d32f2f; display: block; text-align: center; margin: 2px 0; width: 32px;"
        else:
            # Dark Mode: Dark grey buttons
            btn_style = "text-decoration: none; color: white; background: #444; padding: 6px; border-radius: 4px; font-size: 16px; border: 1px solid #666; display: block; text-align: center; margin: 2px 0; width: 32px;"
            del_style = "text-decoration: none; color: white; background: #d32f2f; padding: 6px; border-radius: 4px; font-size: 16px; border: 1px solid #b71c1c; display: block; text-align: center; margin: 2px 0; width: 32px;"

        # Use title attribute for tooltips
        # Note: formatting as a table ensures vertical layout since flexbox is not supported by QTextEdit
        html = '<table border="0" cellspacing="2" cellpadding="0">'
        html += f'<tr><td><a href="action://view/{res_name}" title="View External" style="{btn_style}">🖼️</a></td></tr>'
        html += f'<tr><td><a href="action://refresh/{res_name}" title="Refresh Image" style="{btn_style}">🔄</a></td></tr>'
        
        # Only show Edit button for whiteboard drawings
        if is_whiteboard:
            html += f'<tr><td><a href="action://edit/{res_name}" title="Edit" style="{btn_style}">✏️</a></td></tr>'
            
        html += f'<tr><td><a href="action://delete/{res_name}" title="Delete" style="{del_style}">🗑️</a></td></tr>'
        html += '</table>'
        
        return html

    def _delete_whiteboard_image(self, res_name):
        """Delete a whiteboard image and its control links from the document."""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        # Confirm deletion
        reply = self.show_message(
            QMessageBox.Icon.Question,
            "Delete Image",
            "Are you sure you want to delete this image?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        doc = self.editor.document()
        cursor = self.editor.textCursor()
        
        # Strategy: Find the block containing a link with res_name
        # With the new table layout, image + controls are in the same block
        # We need to delete the entire table block
        
        block = doc.begin()
        target_block = None
        
        while block.isValid():
            # Check if this block's HTML contains our res_name
            block_text = block.text()
            
            # Also check fragments for anchor links
            it = block.begin()
            found = False
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    fmt = frag.charFormat()
                    anchor_href = fmt.anchorHref()
                    if anchor_href and res_name in anchor_href:
                        found = True
                        break
                    
                    # Also check if fragment is an image with this name
                    if fmt.isImageFormat():
                        img_fmt = fmt.toImageFormat()
                        if img_fmt.name() == res_name:
                            found = True
                            break
                it += 1
            
            if found:
                target_block = block
                break
                
            block = block.next()
        
        if not target_block:
            QMessageBox.warning(self, "Delete Failed", "Could not find image in document.")
            return
        
        # Delete the block containing the table
        cursor.setPosition(target_block.position())
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        
        # Also delete the following <br> if present
        cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor)
        
        cursor.removeSelectedText()
        cursor.deleteChar()  # Clean up any remaining newline
        
        # Remove from storage
        if res_name in self.whiteboard_images:
            del self.whiteboard_images[res_name]
        if res_name + "_meta" in self.whiteboard_images:
            del self.whiteboard_images[res_name + "_meta"]
        if res_name + "_source" in self.whiteboard_images:
            del self.whiteboard_images[res_name + "_source"]
        
        # Emit content changed to trigger save
        self.contentChanged.emit()
        
        # Show success message if status bar exists
        main_window = QApplication.instance().activeWindow()
        if main_window and hasattr(main_window, 'statusBar'):
            main_window.statusBar().showMessage("Image deleted successfully", 3000)

    def replace_image_resource(self, res_name, new_path, metadata=None):
        """Replace an existing image resource with a new file."""
        import os
        from PyQt6.QtGui import QImage
        from PyQt6.QtCore import QUrl
        
        if not os.path.exists(new_path):
             print(f"Replacement path not found: {new_path}")
             return False
             
        new_img = QImage(new_path)
        if new_img.isNull():
             print(f"Replacement image invalid: {new_path}")
             return False
        
        # 1. Update Resource
        doc = self.editor.document()
        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), new_img)
        
        # 2. Update Persisted Metadata
        # Merge new metadata with old if provided
        key_meta = res_name + "_meta"
        key_source = res_name + "_source"
        
        import json
        current_meta = {}
        if key_meta in self.whiteboard_images:
             try:
                 current_meta = json.loads(self.whiteboard_images[key_meta])
             except: pass
        
        # Update path
        current_meta['path'] = new_path
        if metadata:
             current_meta.update(metadata)
        
        self.whiteboard_images[key_meta] = json.dumps(current_meta)
        
        # 3. Update Base64 Source (for persistence)
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        new_img.save(buf, "PNG", quality=100)
        new_b64 = ba.toBase64().data().decode()
        
        self.whiteboard_images[key_source] = new_b64
        
        # 4. Force specific image refresh
        # The QImageResource is updated, but QTextEdit might cache the layout.
        # We can force update the viewport.
        self.editor.setLineWrapColumnOrWidth(self.editor.lineWrapColumnOrWidth()) 
        self.editor.viewport().update()
        
        # 5. Emit Change
        self.contentChanged.emit()
        return True

    def _edit_whiteboard_image(self, res_name):
        """Reopen a whiteboard image for editing via signal."""
        # Use simple signal emission to let MainWindow handle the view switch
        self._handle_edit_whiteboard(res_name)
            



    def _handle_whiteboard_edit_save(self, res_name, data):
        """Deprecated logic for internal whiteboard editing."""
        pass


    def _handle_whiteboard_save(self, data):
        # Handle dict or legacy QImage
        if isinstance(data, dict):
             if data['view'].isNull(): return
        elif data.isNull(): 
             return
             
        self._process_and_insert_image(data, draw_border=True)

    def insert_image(self, image_path):
        """Insert an image from a file path."""
        import os
        from PyQt6.QtGui import QImage
        
        if not os.path.exists(image_path):
            return
            
        image = QImage(image_path)
        if image.isNull():
            return
            
        # Create metadata to link back to source file (important for "Edit" later if we want)
        # But for simple insertion, we just treat it as an image.
        # If we want the "Edit" button to appear, we need to mimic the data structure.
        # Whiteboard snapshots ARE whiteboard images, so we SHOULD allow editing if possible?
        # But for now, just inserting it is enough. 
        # Actually, passing 'meta': {'path': image_path} helps persistence optimization.
        
        data = {
            'view': image,
            'source': image,
            'meta': {'path': image_path, 'bg_mode': 'transparent'} # bg_mode triggers "Edit" button in controls
        }
        
        self._process_and_insert_image(data, draw_border=True)

    def insert_note_box(self):
        """Insert a styled note box (Callout)."""
        # Using HTML Table for "box" effect
        # Width="100%" on table tag is crucial for QTextEdit to render full width
        # FIX: Removed <thead> to prevent header repetition on new pages in PDF export
        html = """
        <br>
        <table width="100%" border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; border: 2px solid #007ACC; background-color: #f9f9f9;">
            <tr>
                <td style="background-color: #e3f2fd; font-weight: bold; color: #007ACC; border-bottom: 2px solid #007ACC;">Note: ✒️</td>
                <td width="30" style="background-color: #e3f2fd; border-bottom: 2px solid #007ACC; text-align: right; vertical-align: middle;">
                    <a href="action://delete_level" style="text-decoration: none; color: #007ACC; font-weight: bold; font-size: 14px;">✕</a>
                </td>
            </tr>
            <tr>
                <td colspan="2"><br></td>
            </tr>
        </table>
        <br>
        """
        self.editor.insertHtml(html)

    def set_current_folder(self, folder):
        """Set the current folder - legacy method kept for compatibility."""
        self.current_folder = folder
    
    def get_images_dir(self, folder):
        """Obsolete method."""
        pass

    # Obsolete image persistence methods removed

    def _process_and_insert_image_async(self, data, draw_border=False):
        """Async version of image processing to prevent UI blocking."""
        processor = ImageProcessor(data)
        processor.finished.connect(lambda result: self._insert_processed_image(result, draw_border))
        task = ImageProcessingTask(processor)
        self._thread_pool.start(task)
    
    def _insert_processed_image(self, result, draw_border=False):
        """Insert processed image into document using resources instead of base64."""
        try:
            from PyQt6.QtGui import QTextImageFormat
            import json
            
            view_b64 = result['view_b64']
            source_b64 = result['source_b64']
            meta = result['meta']
            view_image = result['view_image']
            source_image = result['source_image']
            
            doc = self.editor.document()
            # Generate unique ID
            res_name = f"wb_drawing_{uuid.uuid4().hex[:12]}"
            
            # Manage Image Storage (whiteboard_images is the source of truth)
            self.whiteboard_images[res_name] = view_b64
            self.whiteboard_images[res_name + "_source"] = source_b64
            
            # Store metadata for editing
            self.whiteboard_images[res_name + "_meta"] = json.dumps(meta)
            
            # Add image to document resources
            # For file-backed images, load original file directly for best quality
            if 'path' in meta and meta['path']:
                import os
                if os.path.exists(meta['path']):
                    # Load fresh from file for maximum quality
                    fresh_image = QImage(meta['path'])
                    if not fresh_image.isNull():
                        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), fresh_image)
                    else:
                        # Fallback to processed version
                        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), view_image)
                else:
                    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), view_image)
            else:
                # No file path - use processed version
                doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), view_image)
            
            # Insert image at cursor position using resource-based approach
            cursor = self.editor.textCursor()
            
            # Insert line break before image if not at start of line
            if not cursor.atBlockStart():
                cursor.insertText("\n")
            
            # Insert the image using resource reference (no base64 in HTML!)
            image_format = QTextImageFormat()
            image_format.setName(res_name)
            
            # Calculate display size to fit editor
            available_width = self.editor.viewport().width() - 60
            if available_width < 400: 
                available_width = 800
                
            img_width = view_image.width()
            img_height = view_image.height()
            
            if img_width > available_width:
                ratio = available_width / img_width
                display_width = available_width
                display_height = int(img_height * ratio)
            else:
                display_width = img_width
                display_height = img_height
            
            # Auto-Refresh Registration
        # Auto-Refresh Registration
            if 'path' in meta and meta['path']:
                self._watch_image_path(res_name, meta['path'])

            # Generate Controls HTML (Vertical Buttons)
            buttons_html = ""
            if draw_border or 'bg_mode' in meta or 'path' in meta:
                # Only show Edit for whiteboard-created images (with bg_mode flag)
                is_wb = 'bg_mode' in meta
                buttons_html = self._get_image_controls_html(res_name, is_whiteboard=is_wb)

            # Insert using Table Layout (Image Left | Buttons Right)
            border_style = '1px solid #ccc' if draw_border else 'none'
            
            # Calculate max-width for responsive sizing without forced scaling
            available_width = self.editor.viewport().width() - 100  # Account for buttons + margins
            if available_width < 400:
                available_width = 800
            
            # Calculate display dimensions maintaining aspect ratio
            img_width = view_image.width()
            img_height = view_image.height()
            
            if img_width > available_width:
                # Scale down to fit
                ratio = available_width / img_width
                display_width = int(available_width)
                display_height = int(img_height * ratio)
            else:
                # Use natural size
                display_width = img_width
                display_height = img_height
            
            # CRITICAL: Cache the ORIGINAL dimensions to allow responsive resizing up to strict max
            # We must store the true source size so we know the upper bound for resizing
            self._image_dimensions_cache[res_name] = (view_image.width(), view_image.height())
            


            
            
            # Use CSS max-width instead of fixed dimensions for sharper rendering
            # This allows browser to display at native resolution when smaller than max
            # CRITICAL: Use explicit width/height attributes to preserve aspect ratio in QTextEdit
            html = f'''
            <table border="0" style="margin-top: 5px; margin-bottom: 5px;">
                <tr>
                    <td style="vertical-align: top; padding-right: 10px;">
                        <img src="{res_name}" width="{display_width}" height="{display_height}" style="border: {border_style}; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" />
                    </td>
                    <td style="vertical-align: top;">
                        {buttons_html}
                    </td>
                </tr>
            </table>
            <br>
            '''
            


            
            # CRITICAL: Preserve Scroll Position
            # Capture current scroll before insertion affects layout
            v_scroll = self.editor.verticalScrollBar().value()
            
            cursor.insertHtml(html)
            
            # CRITICAL: Ensure cursor moves to the start of the NEXT line/block
            # insertHtml leaves cursor at the end of the inserted content.
            # We ONLY insert a block break, we do NOT jump to the end of the document.
            cursor.insertBlock() # Create a clean new paragraph below
            
            # Restore cursor to updated position (after image)
            self.editor.setTextCursor(cursor)
            
            # Restore scroll position to prevent jumping
            # We use QTimer to allow layout to settle (async) or set immediately if synchronous enough
            # But usually setting it immediately works for small insertions.
            self.editor.verticalScrollBar().setValue(v_scroll)
            
            # Do NOT call ensureCursorVisible() here, as it forces scrolling.
            
        except Exception as e:
            print(f"Error inserting processed image: {e}")
    

    
    def _insert_image_controls(self, cursor, res_name):
        """Insert edit/delete controls for whiteboard images."""
        # Define theme-aware styles for buttons
        if self.theme_mode == "light":
            edit_style = "text-decoration: none; color: black; background: #e3f2fd; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #007ACC;"
            delete_style = "text-decoration: none; color: black; background: #ffebee; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #d32f2f;"
        else:
            edit_style = "text-decoration: none; color: white; background: #007ACC; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #005a9e;"
            delete_style = "text-decoration: none; color: white; background: #d32f2f; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #b71c1c;"
        
        # Insert controls using resource reference for efficiency
        controls_html = f'''
        <div align="center" style="margin-top: 8px; margin-bottom: 10px;">
            <a href="action://view/{res_name}" style="{edit_style}">🖼️ View</a>
            <a href="action://refresh/{res_name}" style="{edit_style}">🔄 Refresh</a>
            <a href="action://edit/{res_name}" style="{edit_style}">✏️ Edit</a>
            <a href="action://delete/{res_name}" style="{delete_style}">🗑️ Delete</a>
        </div>
        '''
        cursor.insertHtml(controls_html)

    def _process_and_insert_image(self, data, draw_border=False):
        """Unified method to insert images (Paste or Whiteboard) with optimization and controls."""
        # Use async processing for better performance
        if isinstance(data, dict) or (isinstance(data, QImage) and not data.isNull()):
            self._process_and_insert_image_async(data, draw_border)
            return
        
        # Fallback to sync processing for edge cases
        self._process_and_insert_image_sync(data, draw_border)
    
    def _process_and_insert_image_sync(self, data, draw_border=False):
        """Fallback synchronous method for edge cases."""
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        import base64
        import json
        import time
        from PyQt6.QtGui import QTextImageFormat
        
        # Handle input types (QImage or Data Dict)
        if isinstance(data, QImage):
            view_image = data
            source_image = data
            meta = {}
        else:
            view_image = data['view']
            source_image = data['source']
            meta = data['meta']
        
        if view_image.isNull(): return

        doc = self.editor.document()
        # Generate unique ID
        res_name = f"wb_drawing_{uuid.uuid4().hex[:12]}"
        
        # --- OPTIMIZATION: Scale View Image for Display ---
        # This prevents lag by ensuring the HTML <img> src is not massive
        # We cap visual width to editor, and resolution to reasonable max
        available_width = self.editor.viewport().width() - 60
        if available_width < 400: available_width = 800 # Fallback
        
        # Determine "Logical" size (how big it looks on screen)
        # If image is super huge, we shrink it to fit editor
        logic_w = view_image.width()
        logic_h = view_image.height()
        
        if logic_w > available_width:
            ratio = available_width / logic_w
            logic_w = available_width
            logic_h = int(logic_h * ratio)
            
        # Determine "Physical" size for Preview Image (Base64)
        # We don't need 4K preview if we only show 800px. 
        # But we keep it slightly larger (1.5x or 2x) for HighDPI if meaningful, 
        # but capping at say 1200px width is good for performance.
        max_preview_width = 1200
        scaled_view = view_image
        
        if view_image.width() > max_preview_width:
             scaled_view = view_image.scaled(
                max_preview_width,
                int(max_preview_width * (view_image.height() / view_image.width())),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
        # --- Helper to convert QImage to Base64 ---
        def img_to_b64(img, quality=80):
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "PNG", quality=quality)
            return ba.toBase64().data().decode()

        # 1. Store View Image (Optimized for Display)
        view_b64 = img_to_b64(scaled_view, quality=95)  # Increased from 80 to 95
        self.whiteboard_images[res_name] = view_b64
        
        # Add resource - load from file if available for best quality
        if 'path' in meta and meta['path']:
            import os
            if os.path.exists(meta['path']):
                fresh_image = QImage(meta['path'])
                if not fresh_image.isNull():
                    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), fresh_image)
                else:
                    doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), scaled_view)
            else:
                doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), scaled_view)
        else:
            doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), scaled_view)
        
        # 2. Store Source Image (Full Quality for Editing)
        if hasattr(self, 'whiteboard_images'):
            self.whiteboard_images[res_name + "_source"] = img_to_b64(source_image, quality=100)
            self.whiteboard_images[res_name + "_meta"] = json.dumps(meta)
        
        # --- Insert HTML Block with Controls ---
        cursor = self.editor.textCursor()
        
        # Insert at current cursor position (unique ID handles persistence)
        # If logic_w is large, we probably want a newline before if not at start
        if logic_w > 200 and not cursor.atBlockStart():
            cursor.insertText("\n")

        # Theme-aware styles
        if self.theme_mode == "light":
            edit_style = "text-decoration: none; color: black; background: #e3f2fd; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #007ACC;"
            delete_style = "text-decoration: none; color: black; background: #ffebee; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #d32f2f;"
        else:
            edit_style = "text-decoration: none; color: white; background: #007ACC; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #005a9e;"
            delete_style = "text-decoration: none; color: white; background: #d32f2f; padding: 5px 10px; border-radius: 4px; margin: 0 5px; font-size: 12px; font-weight: bold; border: 1px solid #b71c1c;"

        # HTML Block
        # We use logic_w/h for display size, but view_b64 is the optimized data
        border_style = '1px solid #ccc' if draw_border else 'none'
        
        # Auto-Refresh Registration
        path = None
        if 'path' in meta and meta['path']:
             path = meta['path']
             self._watch_image_path(res_name, path)

        # Generate Controls HTML (Vertical Buttons)
        buttons_html = ""
        if draw_border or 'bg_mode' in meta or path:
            # Only show Edit for whiteboard-created images (with bg_mode flag)
            is_wb = 'bg_mode' in meta
            buttons_html = self._get_image_controls_html(res_name, is_whiteboard=is_wb)

        # Insert using Table Layout (Image Left | Buttons Right)
        border_style = '1px solid #ccc' if draw_border else 'none'
        
        # CRITICAL: Cache the ORIGINAL dimensions to allow responsive resizing up to strict max
        self._image_dimensions_cache[res_name] = (view_image.width(), view_image.height())
        
        # HTML Block
        # Use explicit width/height for persistence, matching the Async implementation
        html = f'''
        <table border="0" style="margin-top: 5px; margin-bottom: 5px;">
            <tr>
                <td style="vertical-align: top; padding-right: 10px;">
                    <img src="{res_name}" width="{logic_w}" height="{logic_h}" style="border: {border_style}; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" />
                </td>
                <td style="vertical-align: top;">
                    {buttons_html}
                </td>
            </tr>
        </table>
        <br>
        '''
        
        cursor.insertHtml(html)
        
        # CRITICAL: Ensure cursor moves to the start of the NEXT line/block
        # insertHtml leaves cursor at the end of the inserted content
        cursor.movePosition(QTextCursor.MoveOperation.End) # Ensure we are at the end
        cursor.insertBlock() # Create a clean new paragraph below
        
        # Scroll to ensure visibility
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def scroll_to_bottom(self):
        # Force layout calculation of the document
        self.editor.document().adjustSize()
        
        # Ensure the new content is visible (Scroll to bottom)
        sb = self.editor.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.editor.ensureCursorVisible()

    def text_italic(self):
        # Use clean format for merge
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.editor.currentCharFormat().fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)

    # --- Safe Font Helper ---
    
    @staticmethod
    def _safe_font_update(current_font_family, mode, new_id=None):
        """
        Safely updates font family string to manage persistent IDs (persistence hack).
        mode: 'clean' (remove all), 'add' (remove all then add new_id)
        """
        try:
            import re
            # 1. Base Cleaning: Remove any existing ID markers
            # Pattern matches: optional comma/space, then hl_... or ul_...
            clean_pattern = r"(?:,\s*)?(?:hl_|ul_)[a-f0-9]{8,}"
            
            # Remove all instances to be safe
            base_font = re.sub(clean_pattern, "", str(current_font_family)).strip()
            
            # Clean dangling punctuation
            base_font = base_font.strip(",").strip()
            
            # Fallback for empty font
            if not base_font:
                base_font = "Segoe UI"
                
            if mode == 'clean':
                print(f"DEBUG: SafeFont - Cleaned to: '{base_font}'")
                return base_font
                
            if mode == 'add' and new_id:
                # 2. Injection
                new_font = f"{base_font}, {new_id}"
                print(f"DEBUG: SafeFont - Generated: '{new_font}'")
                return new_font
                
            return base_font
        except Exception as e:
            print(f"CRITICAL ERROR in _safe_font_update: {e}")
            return "Segoe UI" # Ultimate fallback

    def text_underline(self):
        """Toggle underline (Standard)."""
        try:
            # Use clean format for merge
            fmt = QTextCharFormat()
            fmt.setFontUnderline(not self.editor.currentCharFormat().fontUnderline())
            self.editor.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Error in text_underline: {e}")
        
    def text_highlight(self, color=None):
        try:
            if self.highlight_debounce_timer.isActive(): return
            self.highlight_debounce_timer.start()
            
            if isinstance(color, bool): color = None
            
            cursor = self.editor.textCursor()
            if not cursor.hasSelection(): return

            # Target Color
            target_bg = color
            if not target_bg:
                # Default "Standard" Highlight (Ctrl+H) -> Use Theme Default
                import ui.styles as styles
                current_mode = self.theme_mode if hasattr(self, 'theme_mode') else 'light'
                # Default to #FFF176 (Canary) if not found, to match base theme
                # Fallback to local defaults since THEME_COLORS is deprecated
                HIGHLIGHT_DEFAULTS = {
                    "light": "#FFF176", 
                    "dark": "#FACC15" 
                }
                theme_hex = HIGHLIGHT_DEFAULTS.get(current_mode, '#FFF176')
                from PyQt6.QtGui import QColor
                target_bg = QColor(theme_hex)
            
            if not target_bg.isValid(): 
                target_bg = QColor("#FFF176")

            # Toggle Logic: Check if already highlighted with roughly same color
            current_fmt = self.editor.currentCharFormat()
            current_bg = current_fmt.background().color()
            
            is_same_color = False
            if current_fmt.background().style() != Qt.BrushStyle.NoBrush:
                 # Compare RGBA to be rigorous
                 if current_bg.rgba() == target_bg.rgba():
                     is_same_color = True

            fmt = QTextCharFormat()
            if is_same_color:
                # REMOVE Highlight
                from PyQt6.QtGui import QBrush
                fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
                # Reset text color to default (black-ish usually)
                # We can try clearing foreground, currently just setting to black/theme auto?
                # Best way to "reset" foreground implies unsetting it. 
                # mergeCurrentCharFormat with a cleared property should work if we construct it right?
                # Actually, setting it to a specific color (WindowText) is safer for now or just standard black.
                # Let's assume standard note text is black/theme dependent.
                # A safe bet is cleaning the property.
                fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
            else:
                # APPLY Highlight
                r, g, b, _ = target_bg.getRgb()
                luminance = (0.299 * r + 0.587 * g + 0.114 * b)
                text_color = Qt.GlobalColor.white if luminance < 128 else Qt.GlobalColor.black
                
                fmt.setBackground(target_bg)
                fmt.setForeground(text_color)
            
            self.editor.mergeCurrentCharFormat(fmt)
            
        except Exception as e:
            print(f"Error in text_highlight: {e}")

    def change_list_style(self, index):
        """Handle list style changes from ComboBox."""
        cursor = self.editor.textCursor()
        
        if index == 6: # Symbol Insert Action
            self.insert_symbol()
            # Reset combo to current actual state (approximate)
            self.update_format_ui() 
            return

        if index == 5: # Checklist
            self.insert_checklist()
            return
            
        if index == 0: # No List
            # Ideally remove list but keep text. createList(0) might not work directly.
            # Standard way: set block format to non-list
            # But simple way: just pass a standard block format
            
            # If currently a list, "breaking" it out is tricky. 
            # We can use a trick: create a Standard list... no, set block format.
            block_fmt = cursor.blockFormat()
            block_fmt.setObjectIndex(-1) # Remove generic object
            # Setting a standard Block Format doesn't always remove List property in Qt easily
            # simplest way often is to toggle list off.
            
            # Let's try creating a "0" style list? No.
            # Correct: Set the text block format to have no list.
             
            # Better approach for "No List":
            if cursor.currentList():
                # This effectively removes the item from the list
                block_fmt = cursor.blockFormat()
                block_fmt.setIndent(0) # Reset indent too?
                cursor.setBlockFormat(block_fmt)
                # We need to manually remove it from the list object structure
                # Actually, creating a new list with a different style is easy.
                # Removing it... specific logic:
                list_ = cursor.currentList()
                list_.remove(cursor.block())
                
                # Reset indent visually if desired
                bf = cursor.blockFormat()
                bf.setIndent(0)
                cursor.setBlockFormat(bf)
                
        else:
            style = QTextListFormat.Style.ListDisc
            if index == 1: style = QTextListFormat.Style.ListDisc
            elif index == 2: style = QTextListFormat.Style.ListDecimal
            elif index == 3: style = QTextListFormat.Style.ListUpperAlpha
            elif index == 4: style = QTextListFormat.Style.ListUpperRoman
            
            cursor.createList(style)
        
        self.editor.setFocus()

    def scroll_to_top(self):
        """Scroll editor to the top."""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def scroll_to_bottom(self):
        """Scroll editor to the bottom."""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def text_indent(self):
        cursor = self.editor.textCursor()
        if cursor.atBlockStart():
            cursor.insertText("    ")
        else:
            # Handle list indentation logic if needed
            self.editor.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier))

    def show_back_button(self, note_id, note_title):
        """Show floating back button to return to previous note."""
        self.origin_note_id = note_id
        # Truncate title if long
        display_title = note_title
        if len(display_title) > 25:
            display_title = display_title[:22] + "..."
        
        self.btn_back.setText(f"← Back to {display_title}")
        self.btn_back.show()
        self.btn_back.raise_() # Ensure it's on top
        self._reposition_back_button()

    def hide_back_button(self):
        """Hide the floating back button."""
        self.btn_back.hide()
        self.origin_note_id = None

    def _reposition_back_button(self):
        """Position the back button at bottom-center of the editor."""
        if not self.btn_back.isVisible():
            return
            
        editor_width = self.editor.width()
        editor_height = self.editor.height()
        btn_width = self.btn_back.sizeHint().width()
        btn_height = self.btn_back.sizeHint().height()
        
        # Center horizontally, 30px from bottom
        x = (editor_width - btn_width) // 2
        y = editor_height - btn_height - 30
        
        self.btn_back.resize(btn_width, btn_height)
        self.btn_back.move(x, y)

    def _on_back_clicked(self):
        """Handle back button click."""
        if self.origin_note_id:
            from util.logger import logger
            print(f"DEBUG: Back Button Clicked. Returning to Note {self.origin_note_id}")
            self.request_open_note.emit(self.origin_note_id)
            self.hide_back_button()

    def resizeEvent(self, event):
        """Handle resize events to reposition floating elements."""
        super().resizeEvent(event)
        self._reposition_back_button()

    def text_outdent(self):
        cursor = self.editor.textCursor()
        curr_list = cursor.currentList()
        if curr_list:
            fmt = curr_list.format()
            if fmt.indent() > 1:
                fmt.setIndent(fmt.indent() - 1)
                curr_list.setFormat(fmt)
            else:
                 # Remove list style if outdenting fully
                 # This is tricky in Qt, typically involves setting standard block format
                 pass
                 fmt.setIndent(max(1, fmt.indent() - 1)) # Just Decrease for now
                 curr_list.setFormat(fmt)
        else:
            fmt = cursor.blockFormat()
            if fmt.indent() > 0:
                fmt.setIndent(fmt.indent() - 1)
                cursor.setBlockFormat(fmt)

    def insert_checklist(self):
        """Insert a checklist item start."""
        cursor = self.editor.textCursor()
        # Check if already a checklist item to avoid duplication
        text = cursor.block().text().strip()
        if text.startswith("☐") or text.startswith("☑"):
            return
            
        # Insert Checkbox + Space
        cursor.insertText("☐ ")
        self.editor.setFocus()
        
    def insert_symbol(self):
        """Show symbol picker."""
        dlg = SymbolDialog(self)
        if dlg.exec():
            if dlg.selected_symbol:
                self.editor.insertPlainText(dlg.selected_symbol)
                self.editor.setFocus()

    def text_number_list(self):
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDecimal)

    def text_bullet(self):
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDisc)

    def get_html(self):
        """Get HTML with data URIs embedded for persistence with error handling."""
        try:
            html = self.editor.toHtml()
            
            # Replace resource names with data URIs for persistence
            for res_name, b64_data in self.whiteboard_images.items():
                try:
                    data_uri = f"data:image/png;base64,{b64_data}"
                    # Replace all occurrences of resource reference with data URI
                    html = html.replace(f'src="{res_name}"', f'src="{data_uri}"')
                    # Also handle single quotes
                    html = html.replace(f"src='{res_name}'", f"src='{data_uri}'")
                except Exception:
                    pass  # Skip problematic images
            
            return html
        except Exception as e:
            print(f"Error getting HTML: {e}")
            return self.editor.toHtml()  # Fallback

    def set_html(self, html, whiteboard_images=None):
        """Set HTML content and reload associated image resources."""
        self.whiteboard_images = whiteboard_images if whiteboard_images else {}
        # Clear dimension cache when loading new note to prevent memory leak
        self._image_dimensions_cache.clear()
        
        doc = self.editor.document()
        
        # Clear existing resources first
        self.editor.clear()
        
        # Setup resources before setting HTML for legacy support
        # New notes use data URIs embedded directly in HTML, so this is backward compat
        if self.whiteboard_images:
            import base64
            from PyQt6.QtGui import QImage
            for res_name, b64_data in self.whiteboard_images.items():
                # Skip metadata entries which are JSON, not Base64
                if res_name.endswith("_meta"):
                    continue
                    
                try:
                    # Robust Base64 Decoding
                    if b64_data:
                        # Fix padding
                        missing_padding = len(b64_data) % 4
                        if missing_padding:
                            b64_data += '=' * (4 - missing_padding)
                            
                        data = base64.b64decode(b64_data)
                        image = QImage.fromData(data)
                        if not image.isNull():
                            doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_name), image)
                except Exception as e:
                    # Suppress errors for non-critical resources to avoid spamming console
                    print(f"Error loading sidecar resource {res_name}: {e}")
                    
        # Basic XSS / HTML Sanitization
        if html:
             import re
             # Remove script tags
             html = re.sub(r'<script\b[^>]*>(.*?)</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
             # Remove javascript: refs
             html = re.sub(r'href=[\'"]javascript:[^\'"]*[\'"]', '', html, flags=re.IGNORECASE)
             # Remove on* events
             html = re.sub(r' on\w+=[\'"][^\'"]*[\'"]', '', html, flags=re.IGNORECASE)

        # Wrap layout modifications in an edit block for performance and to prevent flickering/glitches
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        try:
            self.editor.setHtml(html)
            
            # CRITICAL FIX: Extract and apply image dimensions from HTML
            # QTextEdit's setHtml() doesn't reliably preserve width/height attributes,
            # so we need to extract them and apply via QTextImageFormat
            import re
            img_pattern = r'<img[^>]*src="([^"]+)"[^>]*width="(\d+)"[^>]*height="(\d+)"[^>]*>'
            
            matches_found = 0
            for match in re.finditer(img_pattern, html):
                matches_found += 1
                res_name = match.group(1)
                width = int(match.group(2))
                height = int(match.group(3))
                
                # Store in cache ONLY if not already present or if we prefer natural size
                natural_dims = None
                try:
                    img = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(res_name))
                    if img and isinstance(img, QImage) and img.width() > 0:
                        natural_dims = (img.width(), img.height())
                except:
                    pass
                
                if natural_dims:
                    self._image_dimensions_cache[res_name] = natural_dims
                else:
                    self._image_dimensions_cache[res_name] = (width, height)
                
                # Apply to document using QTextImageFormat
                doc = self.editor.document()
                block = doc.begin()
                found = False
                
                while block.isValid() and not found:
                    it = block.begin()
                    while not it.atEnd():
                        frag = it.fragment()
                        if frag.isValid() and frag.charFormat().isImageFormat():
                            img_fmt = frag.charFormat().toImageFormat()
                            if img_fmt.name() == res_name:
                                # Apply the dimensions
                                new_fmt = QTextImageFormat()
                                new_fmt.setName(res_name)
                                new_fmt.setWidth(width)
                                new_fmt.setHeight(height)
                                
                                update_cursor = QTextCursor(doc)
                                update_cursor.setPosition(frag.position())
                                update_cursor.setPosition(frag.position() + frag.length(), QTextCursor.MoveMode.KeepAnchor)
                                update_cursor.setCharFormat(new_fmt)
                                found = True
                                break
                        it += 1
                    block = block.next()
                    
            # CRITICAL: Re-apply Level Box Layout Constraints
            self.renumber_all_levels()
        finally:
            cursor.endEditBlock()
            
        # Explicit repaint and scroll restoration
        self.editor.viewport().update()
        
        # CRITICAL: Force a resize pass to ensure images fit viewport
        # Increased delay slightly for better stability
        QTimer.singleShot(100, self._resize_images_to_fit)
        
        # Refresh TOC strictly after loading to ensure visibility
        self.refresh_toc()

    def get_html(self):
        """Get current HTML content with corrected image dimensions."""
        html = self.editor.toHtml()
        
        # CRITICAL FIX: QTextEdit.toHtml() doesn't preserve width/height attributes reliably
        # We need to re-inject them from our cache to prevent images from becoming huge on reload
        import re
        
        for res_name, (width, height) in self._image_dimensions_cache.items():
            # Find img tags with this resource name and ensure they have width/height
            # Pattern: <img src="res_name" ...> (might already have or not have width/height)
            pattern = f'(<img[^>]*src="{re.escape(res_name)}"[^>]*)(/>|>)'
            
            def add_dimensions(match):
                img_tag = match.group(1)
                closing = match.group(2)
                
                # Remove existing width/height if present to avoid duplicates
                img_tag = re.sub(r'\s+width="[^"]*"', '', img_tag)
                img_tag = re.sub(r'\s+height="[^"]*"', '', img_tag)
                
                # Add our cached dimensions
                img_tag += f' width="{width}" height="{height}"'
                return img_tag + closing
            
            html = re.sub(pattern, add_dimensions, html)
        
        return html

    def get_whiteboard_images(self):
        return self.whiteboard_images
    def insertFromMimeData(self, source):
        """COMPREHENSIVE: Handle all clipboard content types with proper image pasting.
        
        NEVER falls back to parent defaults which show file paths instead of images.
        Always shows clear error messages and accepts events to prevent fallback behavior.
        """
        
        # Priority 1: Image data (direct paste of images)
        if source.hasImage():
            image = source.imageData()
            if image and isinstance(image, QImage) and not image.isNull():
                # Process image through our robust pipeline
                self._process_and_insert_image(image)
                return  # Successfully handled image
            elif image is None:
                # Clear error message for null image data
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Image Paste Error", 
                                  "Clipboard image data is null or invalid.\nTry copying an image again.")
                return  # Don't fall back
        
        # Priority 2: File URLs (drag and drop of files)
        if source.hasUrls():
            for url in source.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        image = QImage(path)
                        if not image.isNull():
                            data = {
                                'view': image,
                                'source': image,
                                'meta': {'path': path}
                            }
                            self._process_and_insert_image(data)
                            return  # Successfully handled image
                        else:
                            # Clear error for corrupted images
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.critical(self, "Image Load Error", 
                                               f"Failed to load image from:\n{path}\n\nThe file may be corrupted or in an unsupported format.")
                            return  # Don't fall back
        
        # Priority 3: Base64 image data
        if source.hasText():
            text = source.text()
            if text.startswith("data:image/"):
                try:
                    header, encoded = text.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    image = QImage.fromData(image_data)
                    if not image.isNull():
                        self._process_and_insert_image(image)
                        return  # Successfully handled image
                except Exception as e:
                    # Clear error message for base64 decoding failures
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Image Paste Error", 
                                       f"Failed to process clipboard image:\n{str(e)}\n\nThe image format may be corrupted or unsupported.\n\nTry copying a different image.")
                    return  # Don't fall back
        
        # Priority 4: Markdown / Plain Text
        # Priority 4: Markdown / Plain Text
        if source.hasText():
            text = source.text()
            
            # Normalize newlines
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # Check for specific patterns
            is_markdown = False
            # Common patterns that imply markdown
            if "```" in text or "`" in text: is_markdown = True
            elif "**" in text or "*" in text or "__" in text: is_markdown = True
            elif "##" in text: is_markdown = True
            elif "\n-" in text or "\n*" in text: is_markdown = True
            elif "[" in text and "](" in text: is_markdown = True # Links
            
            # PRIORITY: If it looks like Markdown, treat it as Markdown!
            # This overrides "junk" HTML that often wraps raw markdown symbols
            if is_markdown:
                try:
                    from markdown_it import MarkdownIt
                    md = MarkdownIt("commonmark", {'breaks': True, 'html': True})
                    
                    # render to HTML
                    html = md.render(text)
                    
                    # Styling for code blocks (QTextEdit specific adjustments)
                    html = html.replace('<pre>', '<pre style="background: #2d2d2d; color: #ccc; padding: 10px; border-radius: 4px;">')
                    html = html.replace('<code>', '<code style="background: rgba(150,150,150,0.3); padding: 2px 4px; border-radius: 3px;">')
                    
                    self.editor.insertHtml(html)
                    return
                except (ImportError, Exception) as e:
                    print(f"Markdown library failed ({e}), using fallback regex.")
                    import re
                    from html import escape
                    
                    # Fallback Regex Parser
                    html = escape(text)
                    
                    # 1. Code Blocks
                    def code_block_repl(match):
                        content = match.group(1)
                        if content.startswith("\n"): content = content[1:]
                        return f'<pre style="background: #2d2d2d; color: #ccc; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap;"><code>{content}</code></pre>'
                    html = re.sub(r'```(.*?)```', code_block_repl, html, flags=re.DOTALL)
                    
                    # 2. Inline Code
                    html = re.sub(r'`([^`\n]+)`', r'<code style="background: rgba(150,150,150,0.3); padding: 2px 4px; border-radius: 3px;">\1</code>', html)
                    
                    # 3. Bold
                    html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
                    html = re.sub(r'__(.*?)__', r'<b>\1</b>', html)
                    
                    # 4. Italic
                    html = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html)
                    
                    # 5. Headers
                    html = re.sub(r'^#{3}\s+(.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
                    html = re.sub(r'^#{2}\s+(.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
                    html = re.sub(r'^#{1}\s+(.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
                    
                    # 6. Lists
                    html = re.sub(r'^\s*[-*]\s+(.*?)$', r'<ul><li>\1</li></ul>', html, flags=re.MULTILINE)
                    html = re.sub(r'</ul>\s*<ul>', '', html)
                    
                    # 7. Newlines
                    html = html.replace('\n', '<br>')
                    html = re.sub(r'(</h[1-6]>|</ul>|</pre>)<br>', r'\1', html)
                    
                    self.editor.insertHtml(html)
                    return

        # Priority 4: Rich Text / HTML (Browser Copy, Notion, Office, etc.)
        # Only use this if we DIDN'T detect markdown above.
        if source.hasHtml():
             super().insertFromMimeData(source)
             return


        # Fallback: Plain Text
        # Delegate to super to handle normal text insertion properly
        super().insertFromMimeData(source)




    def canInsertFromMimeData(self, source):
        """Check if clipboard contains image data or file paths.
        
        FIXED: Return False when we handle clipboard content to prevent path display fallback.
        This ensures our enhanced error handling takes precedence over default behavior.
        """
        # Check all three content types - if any are handled, we take control
        if source.hasImage():
            image = source.imageData()
            if image and isinstance(image, QImage) and not image.isNull():
                return False  # We can handle this
        
        if source.hasUrls():
            for url in source.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        return False  # We can handle this
        
        if source.hasText() and source.text().startswith("data:image/"):
            return False  # We can handle this
        
        # Only let parent handle if we cannot handle the content
        # This prevents fallback to showing file path instead of image
        return super().canInsertFromMimeData(source)

    def clear(self):
        self.editor.clear()

    def insert_hr(self):
        """Insert a styled horizontal line (using table for reliability)."""
        # Get settings
        thickness = self.data_manager.get_setting("hr_thickness", 2)
        color = self.data_manager.get_setting("hr_color", "#cccccc") 
        
        # Using a table is much more reliable in simple HTML engines like QTextEdit
        # than trying to style an <hr> tag which has mixed support.
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 5px;">
            <tr>
                <td style="border-bottom: {thickness}px solid {color}; line-height: 2px;">&nbsp;</td>
            </tr>
        </table>
        <br>
        """
        self.editor.insertHtml(html)

    def cleanup(self):
        """Handle cleanup (terminate whiteboard subprocess)."""
        if hasattr(self, 'whiteboard_process') and self.whiteboard_process:
            try:
                if self.whiteboard_process.state() != self.whiteboard_process.ProcessState.NotRunning:
                    self.whiteboard_process.terminate()
                    # Wait up to 1 second for graceful shutdown
                    if not self.whiteboard_process.waitForFinished(1000):
                        # Force kill if still running
                        self.whiteboard_process.kill()
                        self.whiteboard_process.waitForFinished(500)
            except:
                pass
    
    def closeEvent(self, event):
        """Handle cleanup on close (fallback)."""
        self.cleanup()
        super().closeEvent(event)


        
    def set_hr_thickness(self, val):
        self.data_manager.set_setting("hr_thickness", val)
        
    def set_hr_color(self):
        current = self.data_manager.get_setting("hr_color", "#cccccc")
        
        # Specialized dialog to stay on top
        dlg = QColorDialog(QColor(current), self)
        dlg.setWindowTitle("Line Color")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        if dlg.exec():
            col = dlg.selectedColor()
            if col.isValid():
                self.data_manager.set_setting("hr_color", col.name())
    def apply_custom_highlight(self):
        """Apply the saved custom highlight color (Ctrl+J)"""
        # Reuse Main Highlight Logic with Custom Color
        # Ensures consistency and fragment-safety
        if hasattr(self, 'custom_highlight_color'):
            self.text_highlight(self.custom_highlight_color)
        else:
            self.text_highlight(None) # Fallback to standard

    def pick_custom_highlight_color(self):
        """Pick a new custom highlight color"""
        # specialized dialog instance to enforce TopMost
        dlg = QColorDialog(self.custom_highlight_color, self)
        dlg.setWindowTitle("Select Highlight Color")
        # Ensure it stays on top of whiteboard
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        if dlg.exec():
            color = dlg.selectedColor()
            if color.isValid():
                self.custom_highlight_color = color
                
                # Save to persistent settings
                if self.data_manager:
                    self.data_manager.set_setting("custom_highlight_color", color.name())
                
                # Update icon
                self._update_custom_hl_icon(color)
                
                # Auto-apply after picking
                self.apply_custom_highlight()

    def _update_custom_hl_icon(self, color):
        """Update the custom highlighter button icon with the selected color"""
        if not hasattr(self, 'btn_custom_hl'):
            return
            
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        
        # Add a light border for visibility if color is light
        with QPainter(pixmap) as painter:
            painter.setPen(QPen(QColor("#cccccc")))
            painter.drawRect(0, 0, 15, 15)
            
        self.btn_custom_hl.setIcon(QIcon(pixmap))
        # Update tooltip
        self.btn_custom_hl.setToolTip(f"Custom Highlight (Ctrl+J) - {color.name()}")

    def show_message(self, icon, title, text, details=None, buttons=None):
        """Helper to show messages that stay on top of the whiteboard."""
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        if details:
            msg.setDetailedText(details)
        
        if buttons:
            msg.setStandardButtons(buttons)
        
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        return msg.exec()
