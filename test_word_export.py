
from word_export.exporter import html_to_docx
from docx import Document
import os

html_content = """
<h1>Test Note Title</h1>
<p>This is a <b>bold</b> paragraph with some <i>italic</i> text and <span style="color:#FF0000">red color</span>.</p>
<h2>Subheading</h2>
<ul>
    <li>Item 1</li>
    <li>Item 2: <b>Bold Item</b></li>
</ul>
<table style="background-color: #FFFFE0; border: 1px solid #ccc;">
    <tr>
        <td>
            <p><b>Note:</b> This simulates a Level 1 Note Box.</p>
        </td>
    </tr>
</table>
<hr>
<p style="text-align: center">Centered Text</p>
"""

try:
    doc = Document()
    doc.add_heading("Manual Test", 0)
    html_to_docx(doc, html_content)
    doc.save("test_export_output.docx")
    print("Successfully generated test_export_output.docx")
except Exception as e:
    print(f"Export Failed: {e}")
    import traceback
    traceback.print_exc()
