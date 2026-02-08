
import os
import json
import base64
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt6.QtGui import QPainter, QPdfWriter, QPageSize, QFont, QPageLayout, QTextDocument, QImage, QPixmap, QColor, QBrush
from PyQt6.QtCore import QSizeF, QRectF, Qt, QMarginsF, QBuffer, QIODevice, QByteArray
from PyQt6.QtPrintSupport import QPrinter
from scrble_ink1 import InkCanvas, Page

def _render_canvas_to_pixmap(canvas, page_data):
    """
    Render the page data to a high-res pixmap using InkCanvas logic.
    This is a stateless helper adapted from WhiteboardWidget.
    """
    # Load data into canvas
    canvas.load_page_data(page_data)
    
    # 1. Calculate Bounds
    bounds = QRectF()
    
    # Strokes
    for s in canvas.strokes:
        if hasattr(s, 'path'):
            r = s.path.boundingRect()
            w = s.width / 2 + 5 
            r.adjust(-w, -w, w, w)
            bounds = bounds.united(r)
            
    # Shapes
    for s in canvas.shapes:
        r = QRectF(s.start, s.end).normalized()
        adj = s.width / 2 + 5
        r.adjust(-adj, -adj, adj, adj)
        bounds = bounds.united(r)
        
    # Images
    for img in canvas.images:
        r = QRectF(img.position, QSizeF(img.size))
        bounds = bounds.united(r)
        
    if bounds.isEmpty():
        bounds = QRectF(0, 0, 800, 600)
        
    # Add Padding
    padding = 50
    bounds.adjust(-padding, -padding, padding, padding)
    
    # 2. Determine Scale for High-Res Output
    TARGET_WIDTH = 2000 
    scale_factor = TARGET_WIDTH / bounds.width()
    scale_factor = max(scale_factor, 1.0)
    
    w = int(bounds.width() * scale_factor)
    h = int(bounds.height() * scale_factor)
    
    # Cap max dimensions
    MAX_DIM = 4000
    if w > MAX_DIM or h > MAX_DIM:
        ratio = min(MAX_DIM/w, MAX_DIM/h)
        scale_factor *= ratio
        w = int(bounds.width() * scale_factor)
        h = int(bounds.height() * scale_factor)

    image = QImage(w, h, QImage.Format.Format_ARGB32)
    
    # Use canvas background color (loaded from page data)
    if canvas.background_color:
        image.fill(canvas.background_color)
    else:
        # If no color, default to WHITE in light mode, DARK in dark mode?
        # Actually, whiteboard data usually has its own background.
        image.fill(Qt.GlobalColor.white) # Fallback to white

    # 3. Layered Rendering for Eraser Correctness
    # Layer B: Content (Transparent)
    content_layer = QImage(w, h, QImage.Format.Format_ARGB32)
    content_layer.fill(Qt.GlobalColor.transparent)
    
    content_painter = QPainter(content_layer)
    content_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    content_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # Apply Transforms to Content Painter
    content_painter.scale(scale_factor, scale_factor)
    content_painter.translate(-bounds.topLeft())
    
    # Draw Content
    # Images
    for img_obj in canvas.images:
        content_painter.drawImage(QRectF(img_obj.position, QSizeF(img_obj.size)), img_obj.image)
        
    # Shapes
    for shape in canvas.shapes:
        canvas._draw_shape(content_painter, shape)
        
    # Strokes
    for stroke in canvas.strokes:
        canvas._draw_stroke(content_painter, stroke)
        
    content_painter.end()
    
    # 4. Compose
    final_painter = QPainter(image)
    final_painter.drawImage(0, 0, content_layer)
    final_painter.end()

    return QPixmap.fromImage(image)

def export_whiteboard_to_pdf(whiteboard_path, output_path, parent=None, theme=0):
    """
    Exports a whiteboard.json file to a PDF with Table of Contents using HTML generation.
    matches the internal WhiteboardWidget export style.
    """
    try:
        # 1. Load Data
        with open(whiteboard_path, 'r') as f:
            data = json.load(f)
        
        pages_data = data.get('pages', [])
        if not pages_data:
            raise Exception("No pages found in whiteboard file.")
            
        pages = [Page.from_dict(p) for p in pages_data]
        folder_name = os.path.basename(os.path.dirname(whiteboard_path))
        
        # 2. Setup Hidden Canvas for Rendering
        temp_canvas = InkCanvas()
        
        # 3. Generate HTML with Theme Support
        # Theme-aware colors
        bg_color_html = "white" if theme == 0 else "#1e1e1e"
        text_color_html = "#000" if theme == 0 else "#e0e0e0"
        header_color_html = "#333" if theme == 0 else "#f0f0f0"
        border_color_html = "#ccc" if theme == 0 else "#444"
        img_border_html = "#ddd" if theme == 0 else "#555"
        link_color_html = "#007ACC" if theme == 0 else "#4dabf7"

        html_parts = []
        
        # Title Page
        html_parts.append(f"""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="font-size: 32pt; font-weight: bold; color: {text_color_html};">{folder_name}</h1>
            <p style="color: {header_color_html}; font-size: 14pt;">Whiteboard Export</p>
        </div>
        <br/><hr style="border: 1px solid {border_color_html};"/><br/>
        """)
        
        # TOC
        html_parts.append(f'<div id="toc"><h2 style="color: {text_color_html};">Table of Contents</h2></div><ul style="font-size: 14pt; line-height: 1.6; color: {text_color_html};">')
        
        current_section = None
        for i, page in enumerate(pages):
            anchor = f"page_{i}"
            page_name = page.name if page.name else f"Page {i+1}"
            
            # Check for new section
            if page.section and page.section != current_section:
                current_section = page.section
                html_parts.append(f'<li style="list-style: none; margin-top: 15px; font-weight: bold; font-size: 16pt; color: {header_color_html};">📝 {current_section}</li>')
            
            # Indent pages under section
            indent = 'margin-left: 20px;' if current_section else ''
            html_parts.append(f'<li style="{indent}"><a href="#{anchor}" style="text-decoration: underline; color: {link_color_html};">{page_name}</a></li>')
            
        html_parts.append(f"</ul><br/><hr style='border: 1px solid {border_color_html};'/><br/><br/>")
        
        # 4. Setup Printer FIRST
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        
        layout_rect = printer.pageRect(QPrinter.Unit.Point)
        usable_w = layout_rect.width()
        usable_h = layout_rect.height() - 40
        
        # 5. Render Pages
        for i, page in enumerate(pages):
            temp_canvas.load_page_data(page)
            pixmap = _render_canvas_to_pixmap(temp_canvas, page)
            
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buf, "PNG")
            b64_data = ba.toBase64().data().decode()
            
            img_w = pixmap.width()
            img_h = pixmap.height()
            
            scale_factor = usable_w / img_w
            projected_h = img_h * scale_factor
            
            if projected_h <= usable_h:
                final_w = usable_w
                final_h = int(projected_h)
            else:
                final_h = usable_h
                final_w = int(img_w * (usable_h / img_h))
            
            anchor = f"page_{i}"
            page_name = page.name if page.name else f"Page {i+1}"
            
            html_parts.append(f"""<div id="{anchor}" style="page-break-before: always; width: 100%;">
<h2 style="color: {header_color_html}; border-bottom: 2px solid {border_color_html}; margin: 0; padding: 20px 20px 10px 20px;">{i+1}. {page_name}</h2>
<table style="width: 100%; margin: 10px 0; border-collapse: collapse;">
<tr>
<td style="text-align: left; padding: 0 20px; border: none;">
<img src="data:image/png;base64,{b64_data}" width="{final_w - 40}" height="{final_h}" style="display: block; border: 1px solid {img_border_html}; margin: 0; max-width: 100%; height: auto;"/>
</td>
</tr>
</table>
<div style="text-align: right; margin-top: 10px; padding-right: 20px;">
<a href="#toc" style="text-decoration: none; color: {link_color_html}; font-size: 10pt;">↑ Back to Table of Contents</a>
</div>
</div>""")
            
        # 6. Print to PDF
        html_content = f"<html><body style='margin: 0; padding: 0; background-color: {bg_color_html};'>" + "".join(html_parts) + "</body></html>"
        
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Segoe UI", 10))
        doc.setPageSize(QSizeF(layout_rect.width(), layout_rect.height()))
        doc.setDocumentMargin(0) 
        doc.setHtml(html_content)
        
        # Manual Print Loop for theme background support
        painter = QPainter(printer)
        device_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        
        scale = 1.0
        if layout_rect.width() > 0:
            scale = device_rect.width() / layout_rect.width()
        
        page_count = doc.pageCount()
        
        for i in range(page_count):
            if i > 0:
                printer.newPage()
            
            # Paint dark background if theme is Dark (1)
            if theme == 1:
                painter.save()
                page_rect_dev = printer.pageRect(QPrinter.Unit.DevicePixel)
                paper_rect_dev = printer.paperRect(QPrinter.Unit.DevicePixel)
                
                left_margin = page_rect_dev.left() - paper_rect_dev.left()
                top_margin = page_rect_dev.top() - paper_rect_dev.top()
                
                full_page_rect = QRectF(
                    -left_margin,
                    -top_margin,
                    paper_rect_dev.width(),
                    paper_rect_dev.height()
                )
                
                painter.fillRect(full_page_rect, QBrush(QColor("#1e1e1e")))
                painter.restore()
            
            # Draw document content
            painter.save()
            painter.scale(scale, scale)
            painter.translate(0, -i * layout_rect.height())
            clip_rect = QRectF(0, i * layout_rect.height(), layout_rect.width(), layout_rect.height())
            doc.drawContents(painter, clip_rect)
            painter.restore()
        
        painter.end()
        return True
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if parent:
             QMessageBox.critical(parent, "Export Failed", f"Failed to export whiteboard PDF:\n{str(e)}")
        raise e

