
try:
    import docx
    print("python-docx is available")
    doc = docx.Document()
    doc.add_paragraph("Hello World")
    doc.save("test_doc.docx")
    print("Successfully saved test_doc.docx")
except ImportError:
    print("python-docx is NOT available")
except Exception as e:
    print(f"Error: {e}")
