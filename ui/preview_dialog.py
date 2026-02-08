from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, 
                             QLabel, QProgressBar, QRadioButton, QButtonGroup, QWidget, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QTextCursor
import threading
import ui.styles as styles
from ui.zen_dialog import ZenDialog
from util.icon_factory import get_premium_icon

class PreviewWorker(QThread):
    """Background worker to generate PDF preview content without freezing UI."""
    progress = pyqtSignal(int, int, str)  # current, total, status_text
    chunkReady = pyqtSignal(str)          # HTML chunk to append
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, folder, whiteboard_images, theme, start_index=1):
        super().__init__()
        self.folder = folder
        self.whiteboard_images = whiteboard_images
        self.theme = theme
        self.start_index = start_index
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        from pdf_export.exporter import (
            generate_folder_header_html, prepare_note_for_export, 
            generate_note_title_block, apply_theme_to_html, 
            force_code_block_styles, process_images_for_pdf
        )
        from models.note import Note
        
        try:
            sorted_notes = sorted(self.folder.notes, key=Note.sort_key)
            total = len(sorted_notes)
            
            # --- PHASE 1: PREPARE HEADER & TOC ---
            if not self._is_running: return
            self.progress.emit(0, total, "Preparing Header & TOC...")
            
            header_html = generate_folder_header_html(self.folder, self.theme)
            
            # Metadata for TOC
            processed_notes_data = []
            
            # We need to scan all notes FIRST to build the Master TOC
            toc_entries = []
            for idx, note in enumerate(sorted_notes, self.start_index):
                if not self._is_running: return
                self.progress.emit(idx, total, f"Scanning Note {idx}/{total}...")
                
                # Heavy processing (Cleanup, Regex scan)
                note_data = prepare_note_for_export(note, idx, for_preview=True, theme=self.theme)
                processed_notes_data.append(note_data)
                
                # Add to Master TOC
                toc_entries.append(f'<li><a href="#{note_data["anchor"]}" style="text-decoration: underline; color: {"#66b3ff" if self.theme == 1 else "#007ACC"};"><b>{idx}. {note.title}</b></a>')
                
                # Add Sub-items to TOC
                if note_data['sub_toc']:
                    toc_entries.append('<ul style="font-size: 11pt; list-style-type: circle; color: #555;">')
                    for item in note_data['sub_toc']:
                        sub_indent = "margin-left: 10px;" if item['level'] > 1 else ""
                        toc_entries.append(f'<li style="{sub_indent}"><a href="#{item["anchor"]}" style="text-decoration: none; color: {"#66b3ff" if self.theme == 1 else "#007ACC"};">{item["text"]}</a></li>')
                    toc_entries.append('</ul>')
                toc_entries.append('</li>')

            # Build Full Preface
            toc_html = f'<div id="toc_anchor"><h2>Table of Contents</h2></div><ul style="font-size: 14pt; line-height: 1.6;">{"".join(toc_entries)}</ul><br/><hr/><br/>'
            
            preface_full = header_html + toc_html
            preface_full = apply_theme_to_html(preface_full, self.theme)
            
            if self._is_running:
                self.chunkReady.emit(preface_full)
            
            # --- PHASE 2: STREAM CONTENT ---
            for idx, (note, data) in enumerate(zip(sorted_notes, processed_notes_data), self.start_index):
                if not self._is_running: return
                self.progress.emit(idx, total, f"Rendering Note {idx}/{total}...")
                
                # Title Block
                title_html = generate_note_title_block(note, idx, data['anchor'], self.theme)
                
                # Content (Image processing is heavy)
                content_html = data['content']
                content_html = process_images_for_pdf(content_html, self.whiteboard_images, theme=self.theme)
                content_html = force_code_block_styles(content_html)
                
                # Back link
                back_link_style = f"text-decoration: none; color: {'#66b3ff' if self.theme == 1 else '#0366d6'}; font-size: 10pt;"
                back_link = f'<p style="text-align: right; margin-top: 10px;"><a href="#toc_anchor" style="{back_link_style}">↑ Back to Table of Contents</a></p><br/><hr/><br/>'
                
                full_note_chunk = title_html + content_html + back_link
                
                if self._is_running:
                    self.chunkReady.emit(full_note_chunk)

            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))

class PDFPreviewDialog(ZenDialog):
    exportConfirmed = pyqtSignal(int)

    def __init__(self, folder, whiteboard_images, parent=None, current_theme_mode="light", start_index=1):
        # Auto-detect theme
        theme_mode = "light"
        if parent and hasattr(parent, 'theme_mode'):
            theme_mode = parent.theme_mode
        elif parent and hasattr(parent, 'data_manager'):
            theme_mode = parent.data_manager.get_setting("theme_mode", "light")
            
        super().__init__(parent, title="PDF Preview", theme_mode=theme_mode)
        self.folder = folder
        self.whiteboard_images = whiteboard_images
        self.start_index = start_index
        self.current_theme = 1 if current_theme_mode == "dark" else 0
        
        self.resize(1000, 950)
            
        self._setup_ui_local()
        self._start_preview_worker()
        self._apply_theme_local()

    def _setup_ui_local(self):
        # Performance Header
        perf_layout = QHBoxLayout()
        self.status_label = QLabel("Initializing background worker...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        perf_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        perf_layout.addWidget(self.progress_bar, 1)
        self.content_layout.addLayout(perf_layout)
        
        # Preview Browser
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(False)
        self.preview_browser.setObjectName("PdfPreviewBrowser")
        self.content_layout.addWidget(self.preview_browser)
        
        # Footer Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        
        self.export_btn = QPushButton(" Export to PDF")
        self.export_btn.setIcon(get_premium_icon("download", color="white"))
        self.export_btn.setMinimumWidth(150)
        self.export_btn.clicked.connect(self.accept_export)
        self.export_btn.setEnabled(False) # Enable only after loading
        btn_layout.addWidget(self.export_btn)
        
        self.content_layout.addLayout(btn_layout)

    def _start_preview_worker(self):
        """Initializes and starts the background preview worker."""
        self.worker = PreviewWorker(self.folder, self.whiteboard_images, self.current_theme, self.start_index)
        self.worker.progress.connect(self._update_progress)
        self.worker.chunkReady.connect(self._append_chunk)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        
        self.preview_browser.clear()
        self.worker.start()

    @pyqtSlot(int, int, str)
    def _update_progress(self, current, total, status_text):
        self.status_label.setText(status_text)
        if total > 0:
            val = int((current / total) * 100)
            self.progress_bar.setValue(val)

    @pyqtSlot(str)
    def _append_chunk(self, html_chunk):
        """Append HTML piece to the browser without a full reload."""
        cursor = self.preview_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_chunk)
        if self.preview_browser.verticalScrollBar().value() == 0:
            self.preview_browser.verticalScrollBar().setValue(0)

    def _on_worker_finished(self):
        self.status_label.setText(f"Preview ready ({len(self.folder.notes)} notes)")
        self.status_label.setStyleSheet("color: #7B9E87; font-weight: bold;")
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        self.export_btn.setEnabled(True)

    def _on_worker_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.progress_bar.hide()

    def closeEvent(self, event):
        """Safely stop the worker when closing the dialog."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)

    def accept_export(self):
        self.exportConfirmed.emit(self.current_theme)
        self.accept()

    def _apply_theme_local(self):
        c = styles.ZEN_THEME.get(self.theme_mode, styles.ZEN_THEME["light"])
        
        self.status_label.setStyleSheet(f"font-weight: bold; color: {c['primary']};")
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {c['border']};
                border-radius: 4px;
                background: {c['secondary']};
            }}
            QProgressBar::chunk {{
                background-color: {c['primary']};
                border-radius: 3px;
            }}
        """)
        
        self.preview_browser.setStyleSheet(f"""
            QTextBrowser {{
                border: 1px solid {c['border']};
                background-color: {c['card']};
                color: {c['card_foreground']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        btn_base = f"""
            QPushButton {{
                padding: 8px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
        """
        self.export_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['primary_foreground']};
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:disabled {{
                background-color: {c['muted']};
                color: {c['muted_foreground']};
            }}
        """)
        
        self.close_btn.setStyleSheet(btn_base + f"""
            QPushButton {{
                background-color: transparent;
                color: {c['foreground']};
                border: 1px solid {c['border']};
            }}
            QPushButton:hover {{ background-color: {c['muted']}; }}
        """)
