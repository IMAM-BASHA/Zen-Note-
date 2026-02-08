
import sys

def check_deps():
    print("Checking dependencies...")
    try:
        import fitz
        print(f"PyMuPDF (fitz) is available: {fitz.__doc__}")
    except ImportError:
        print("PyMuPDF (fitz) is NOT installed.")
        
    try:
        from PyQt6 import QtPdf, QtPdfWidgets
        print("PyQt6.QtPdf and QtPdfWidgets are available.")
    except ImportError:
        print("PyQt6.QtPdf / QtPdfWidgets are NOT installed.")

if __name__ == "__main__":
    check_deps()
