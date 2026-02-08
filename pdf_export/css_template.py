from datetime import datetime

def wrap_with_template(title, body_html):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            /* Match the clean Sans-Serif look */
            font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #2c3e50;
            background: #ffffff;
            padding: 0px; 
            max-width: 100%;
            margin: 0 auto;
        }}
        
        /* Typography & Borders to match usage */
        h1 {{
            font-size: 28px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            /* Main Title Separator */
            border-bottom: 2px solid #eaeaea; 
        }}
        
        h2 {{
            font-size: 20px; /* Distinct section headers */
            font-weight: 600;
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
            padding-top: 15px;
            /* Section Separator: Line above H2 */
            border-top: 1px solid #eaeaea;
        }}
        
        h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        p {{
            margin-bottom: 10px;
            text-align: justify;
        }}

        /* Fix list spacing */
        li p {{ margin: 0; padding: 0; }}

        ul, ol {{
            margin-bottom: 15px;
            padding-left: 25px;
        }}
        
        li {{
            margin-bottom: 5px;
            line-height: 1.6;
        }}

        /* Table Styles */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 8px 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #ffffff;
        }}
        tr:nth-child(odd) {{
            background-color: #fafbfc;
        }}
        
        /* Code Blocks like Joplin */
        pre {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 15px;
            line-height: 1.45;
        }}

        code {{
            font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace;
            background-color: rgba(27,31,35,0.05);
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}
        
        pre code {{
            background: transparent;
            padding: 0;
            font-size: 100%;
        }}
        
        /* Quotes */
        blockquote {{
            margin: 0 0 16px;
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }}

        /* Links */
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        /* Print Specifics */
        @media print {{
            body {{ padding: 0; }}
            h1, h2, h3 {{ page-break-after: avoid; }}
            ul, ol, table, pre {{ page-break-inside: avoid; }}
            .page-break {{ page-break-before: always; }}
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {body_html}
    <div class="footer" style="margin-top: 40px; border-top: 1px solid #eaeaea; padding-top: 10px; text-align: center; color: #999; font-size: 11px;">
        Generated on {datetime.now().strftime("%Y-%m-%d")}
    </div>
</body>
</html>"""
