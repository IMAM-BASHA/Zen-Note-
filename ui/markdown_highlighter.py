from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor

class MarkdownHighlighter(QSyntaxHighlighter):
    """Live markdown syntax highlighting for Zen Notes."""
    
    def __init__(self, document, theme='light'):
        super().__init__(document)
        self.theme = theme
        self.setup_formats()
        self.setup_patterns()
    
    def setup_formats(self):
        """Define text formats for different markdown elements."""
        is_dark = self.theme == 'dark'
        
        # Header formats (# ## ###)
        self.header_format = QTextCharFormat()
        self.header_format.setFontWeight(QFont.Weight.Bold)
        self.header_format.setForeground(QColor("#60a5fa") if is_dark else QColor("#2563eb"))
        
        # Bold (**text**)
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Weight.Bold)
        self.bold_format.setForeground(QColor("#f9fafb") if is_dark else QColor("#1f2937"))
        
        # Italic (*text*)
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        self.italic_format.setForeground(QColor("#d1d5db") if is_dark else QColor("#4b5563"))
        
        # Inline Code (`code`)
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas, Monaco, monospace")
        self.code_format.setBackground(QColor("#374151") if is_dark else QColor("#f3f4f6"))
        self.code_format.setForeground(QColor("#fca5a5") if is_dark else QColor("#dc2626"))
        
        # Links [text](url)
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#60a5fa") if is_dark else QColor("#2563eb"))
        self.link_format.setFontUnderline(True)
        
        # Level Boxes [1.1] or [1.1.1] - CUSTOM SYNTAX
        self.level_box_format = QTextCharFormat()
        self.level_box_format.setFontWeight(QFont.Weight.Bold)
        self.level_box_format.setBackground(QColor("#1e3a8a") if is_dark else QColor("#dbeafe"))
        self.level_box_format.setForeground(QColor("#93c5fd") if is_dark else QColor("#1e40af"))

        # Code Block Delimiters (```)
        self.code_block_delimiter_format = QTextCharFormat()
        self.code_block_delimiter_format.setForeground(QColor("#9ca3af") if is_dark else QColor("#6b7280"))
        self.code_block_delimiter_format.setFontWeight(QFont.Weight.Bold)

    def setup_patterns(self):
        """Define regex patterns for markdown syntax."""
        self.patterns = [
            # Headers (# ## ###) - Ensure it's at start of block
            (QRegularExpression(r'^#{1,6}\s.*'), self.header_format),
            
            # Bold (**text** or __text__)
            (QRegularExpression(r'\*\*[^\*]+\*\*'), self.bold_format),
            (QRegularExpression(r'__[^_]+__'), self.bold_format),
            
            # Italic (*text* or _text_)
            (QRegularExpression(r'\*[^\*]+\*'), self.italic_format),
            (QRegularExpression(r'_[^_]+_'), self.italic_format),
            
            # Inline code (`code`)
            (QRegularExpression(r'`[^`]+`'), self.code_format),
            
            # Links [text](url)
            (QRegularExpression(r'\[([^\]]+)\]\([^\)]+\)'), self.link_format),
            
            # Level Boxes [1.1] or [1.1.1]
            (QRegularExpression(r'\[\d+\.\d+(\.\d+)?\]'), self.level_box_format),

            # Code Block Start/End (```)
            (QRegularExpression(r'^```.*'), self.code_block_delimiter_format),
        ]
    
    def highlightBlock(self, text):
        """Apply highlighting to a block of text."""
        # Simple pattern application
        for pattern, format_style in self.patterns:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format_style)
    
    def update_theme(self, theme):
        """Update colors when theme changes."""
        self.theme = theme
        self.setup_formats()
        self.rehighlight()
