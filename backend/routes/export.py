from flask import Blueprint, request, send_file, jsonify, current_app
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls, qn
from docx.oxml import parse_xml
import io
import os
import requests
import re

export_bp = Blueprint('export', __name__, url_prefix='/api/export')

def hex_to_rgb(hex_color):
    """Convert hex string (e.g., #ff0000) to RGB tuple"""
    if not hex_color or not hex_color.startswith('#'):
        return None
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return None

def get_image_stream(src):
    """Get image file stream from URL or local path"""
    try:
        # Check if it's a local editor image (http://localhost:5000/editor_images/...)
        local_prefix = '/editor_images/'
        if local_prefix in src:
            filename = src.split(local_prefix)[-1]
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(base_dir, 'editor_images', filename)
            
            if os.path.exists(image_path):
                return open(image_path, 'rb')
            
        # External URL
        if src.startswith('http'):
            response = requests.get(src, stream=True, timeout=10)
            if response.status_code == 200:
                return io.BytesIO(response.content)
                
    except Exception as e:
        print(f"Error fetching image {src}: {e}")
        return None
    return None

def process_inline(paragraph, content):
    """Process inline content (text, marks, images in line)"""
    for node in content:
        node_type = node.get('type')
        
        if node_type == 'text':
            text = node.get('text', '')
            run = paragraph.add_run(text)
            
            marks = node.get('marks', [])
            for mark in marks:
                m_type = mark.get('type')
                attrs = mark.get('attrs', {})
                
                if m_type == 'bold':
                    run.bold = True
                elif m_type == 'italic':
                    run.italic = True
                elif m_type == 'underline':
                    run.underline = True
                elif m_type == 'strike':
                    run.font.strike = True
                elif m_type == 'code':
                    run.font.name = 'Courier New'
                    
                elif m_type == 'textStyle':
                    color = attrs.get('color')
                    if color:
                        rgb = hex_to_rgb(color)
                        if rgb:
                            run.font.color.rgb = RGBColor(*rgb)
                            
                    font_family = attrs.get('fontFamily')
                    if font_family:
                        # Strip quotes if present
                        font_family = font_family.replace('"', '').replace("'", "")
                        run.font.name = font_family
                        # Necessary for East Asian fonts in Word
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_family)

        elif node_type == 'image':
             src = node.get('attrs', {}).get('src')
             if src:
                 stream = get_image_stream(src)
                 if stream:
                     try:
                        paragraph.add_run().add_picture(stream, width=Inches(5))
                     except Exception as e:
                         paragraph.add_run(f"[Image Error]")


def process_node(doc, node, parent=None):
    """Recursive processing of TipTap nodes"""
    node_type = node.get('type')
    content = node.get('content', [])
    attrs = node.get('attrs', {})

    if node_type == 'doc':
        for child in content:
            process_node(doc, child)

    elif node_type == 'heading':
        level = attrs.get('level', 1)
        # We manually add heading properties to support inline styles correctly if needed
        # But doc.add_heading style inheritance is cleaner for levels. 
        # Standard headings don't always support easy run modifications unless we access paragraphs.
        p = doc.add_heading(level=level)
        process_inline(p, content)

    elif node_type == 'paragraph':
        if not content:
            doc.add_paragraph()
        else:
            p = doc.add_paragraph()
            process_inline(p, content)
            
            align = attrs.get('textAlign')
            if align == 'center':
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif align == 'right':
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif align == 'justify':
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    elif node_type == 'bulletList':
        for child in content:
            if child.get('type') == 'listItem':
                p = doc.add_paragraph(style='List Bullet')
                li_content = child.get('content', [])
                # Flatten the first paragraph of the list item into the bullet point
                if li_content and li_content[0].get('type') == 'paragraph':
                     process_inline(p, li_content[0].get('content', []))
                     for sub in li_content[1:]:
                         process_node(doc, sub)
                else:
                    for sub in li_content:
                        process_node(doc, sub)

    elif node_type == 'orderedList':
        for child in content:
            if child.get('type') == 'listItem':
                p = doc.add_paragraph(style='List Number')
                li_content = child.get('content', [])
                if li_content and li_content[0].get('type') == 'paragraph':
                     process_inline(p, li_content[0].get('content', []))
                     for sub in li_content[1:]:
                         process_node(doc, sub)
                else:
                    for sub in li_content:
                        process_node(doc, sub)

    elif node_type == 'blockquote':
        for child in content:
            if child.get('type') == 'paragraph':
                p = doc.add_paragraph(style='Quote')
                process_inline(p, child.get('content', []))
            else:
                process_node(doc, child)

    elif node_type == 'codeBlock':
        code_text = ""
        for child in content:
            if child.get('type') == 'text':
                code_text += child.get('text', '')
        
        if code_text:
            p = doc.add_paragraph(code_text)
            p.style = 'No Spacing' 
            # Simple simulation of code block
            if p.runs:
                 p.runs[0].font.name = 'Courier New'

    elif node_type == 'horizontalRule':
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("─" * 20)
        run.font.color.rgb = RGBColor(180, 180, 180)

    elif node_type == 'image':
        src = attrs.get('src')
        if src:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            stream = get_image_stream(src)
            if stream:
                try:
                    r = p.add_run()
                    r.add_picture(stream, width=Inches(5))
                except Exception as e:
                    p.add_run(f"[Image Error]")
    
    elif node_type == 'table':
        rows = content
        if rows:
            num_rows = len(rows)
            first_row_cells = rows[0].get('content', [])
            num_cols = len(first_row_cells)
            
            if num_rows > 0 and num_cols > 0:
                table = doc.add_table(rows=num_rows, cols=num_cols)
                table.style = 'Table Grid'
                
                for r_idx, row in enumerate(rows):
                    cells = row.get('content', [])
                    for c_idx, cell in enumerate(cells):
                        if c_idx >= num_cols: break
                        cell_content_nodes = cell.get('content', [])
                        cell_p = table.cell(r_idx, c_idx).paragraphs[0]
                        
                        if not cell_content_nodes: continue
                        
                        for i, block in enumerate(cell_content_nodes):
                            if i == 0:
                                if block.get('type') == 'paragraph':
                                    process_inline(cell_p, block.get('content', []))
                                else:
                                    pass # Complex content in cell?
                            else:
                                if block.get('type') == 'paragraph':
                                    new_p = table.cell(r_idx, c_idx).add_paragraph()
                                    process_inline(new_p, block.get('content', []))
                        
                        if cell.get('type') == 'tableHeader':
                            for p in table.cell(r_idx, c_idx).paragraphs:
                                for run in p.runs:
                                    run.bold = True


@export_bp.route('/docx', methods=['POST'])
def export_docx():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        title = data.get('title', 'Document')
        editor_json = data.get('content', {})
        
        if not editor_json:
             return jsonify({'error': 'No content provided'}), 400

        doc = Document()
        # Ensure default styles exist or we use "Normal"
        
        # We can add a title if it's not in the content. 
        # But usually content starts with H1.
        # doc.add_heading(title, 0) 

        if not isinstance(editor_json, dict):
             process_node(doc, {'type': 'doc', 'content': []})
        else:
             process_node(doc, editor_json)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        # Clean title for filename
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
        if not safe_title: safe_title = "document"

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=f"{safe_title}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

