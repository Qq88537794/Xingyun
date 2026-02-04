from flask import Blueprint, request, send_file, jsonify, current_app
import zipfile
import tempfile
import shutil
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls, qn
from docx.oxml import parse_xml, OxmlElement
from docx.shared import Pt, RGBColor, Inches, Cm
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

def set_shading(element, color_hex):
    """Set background shading for run or paragraph"""
    if not color_hex: return
    color_hex = color_hex.lstrip('#')
    shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color_hex))
    element.get_or_add_pPr().append(shading_elm)

def set_run_shading(run, color_hex):
    """Set background shading for a run (e.g. inline code)"""
    if not color_hex: return
    color_hex = color_hex.lstrip('#')
    shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color_hex))
    run._element.get_or_add_rPr().append(shading_elm)

def process_inline(paragraph, content):
    """Process inline content (text, marks, images in line)"""
    for node in content:
        node_type = node.get('type')
        
        if node_type == 'hardBreak':
             paragraph.add_run().add_break()
             continue
             
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
                    # Light gray background for inline code
                    set_run_shading(run, 'f3f4f6')
                    # Distinct color for code text
                    run.font.color.rgb = RGBColor(224, 30, 90) # e01e5a
                    
                elif m_type == 'textStyle':

                    color = attrs.get('color')
                    if color:
                        rgb = hex_to_rgb(color)
                        if rgb:
                            run.font.color.rgb = RGBColor(*rgb)
                    
                    font_size = attrs.get('fontSize')
                    if font_size:
                        try:
                            # 1. If we can detect 'pt' explicitly, use it directly
                            if isinstance(font_size, str) and 'pt' in font_size.lower():
                                match = re.search(r'(\d+(\.\d+)?)', font_size)
                                if match:
                                    run.font.size = Pt(float(match.group(1)))
                            
                            # 2. If 'px' is explicit, convert to pt (1px = 0.75pt)
                            elif isinstance(font_size, str) and 'px' in font_size.lower():
                                match = re.search(r'(\d+(\.\d+)?)', font_size)
                                if match:
                                     run.font.size = Pt(float(match.group(1)) * 0.75)

                            # 3. If just a number (e.g. 16) or string number ("16"), ambiguous.
                            # The frontend editor (FontSize.js) simply sets style="font-size: X"
                            # EditorToolbar.vue treats user input as 'pt' (setSize(size.pt)).
                            # But if the editor renders it as `font-size: 16` in HTML without unit, browsers treat as px? 
                            # Or TipTap adds 'px'? 
                            # The extension reads it via element.style.fontSize.
                            # 
                            # If the user selects "14" (pt) in toolbar, FontSize.js sets { fontSize: 14 }.
                            # It renders `style="font-size: 14"`. Wait, 14 what? 
                            # CSS defaults to medium if invalid, or px if in Quirk mode? No, CSS requires units usually.
                            # 
                            # Looking at FontSize.js: `style: font-size: ${attributes.fontSize}`
                            # The toolbar passes `size.pt` (number). So it writes `font-size: 14`.
                            # This is invalid CSS strictly speaking (needs px/pt), but browsers might ignore or treat as px.
                            # However, TipTap JSON export will contain `fontSize: 14`.
                            # Since the Toolbar says "pt", we should treat bare numbers as PT to match user intent.
                            else:
                                raw_val = float(font_size) if isinstance(font_size, (int, float)) else float(re.search(r'(\d+(\.\d+)?)', str(font_size)).group(1))
                                # Default to PT if no unit found, because Toolbar logic implies PT is the primitive
                                run.font.size = Pt(raw_val)
                                
                        except Exception:
                            pass
                            
                    font_family = attrs.get('fontFamily')
                    if font_family:
                        # Strip quotes if present
                        font_family = font_family.replace('"', '').replace("'", "")
                        run.font.name = font_family
                        # Necessary for East Asian fonts in Word
                        rPr = run._element.get_or_add_rPr()
                        rFonts = rPr.get_or_add_rFonts()
                        rFonts.set(qn('w:eastAsia'), font_family)


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
            
            # Code block styling
            if p.runs:
                 run = p.runs[0]
                 run.font.name = 'Courier New'
                 run.font.color.rgb = RGBColor(248, 248, 242) # f8f8f2 (Light text)
            
            # Dark background for code block paragraph
            # We need to access the paragraph properties element
            pPr = p._element.get_or_add_pPr()
            # Set shading to dark color
            shading = parse_xml(r'<w:shd {} w:val="clear" w:color="auto" w:fill="1e1e1e"/>'.format(nsdecls('w')))
            pPr.append(shading)
            
            # Optional: Add padding (indentation) to make it look like a block
            p.paragraph_format.left_indent = Pt(6)

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


def update_doc_styles(doc, styles_list):
    """Update Word styles based on user configuration"""
    if not styles_list or not isinstance(styles_list, list):
        print("DEBUG: styles_list is empty or invalid")
        return
    
    print(f"DEBUG: Receiving styles to update: {len(styles_list)}")
    
    # Map internal element names to potential Word Style names (English and Chinese)
    element_style_map = {
        'p': ['Normal', '正文'],
        'h1': ['Heading 1', '标题 1'],
        'h2': ['Heading 2', '标题 2'],
        'h3': ['Heading 3', '标题 3'],
        'h4': ['Heading 4', '标题 4']
    }

    # Cache existing styles for easier lookup
    existing_styles = {s.name: s for s in doc.styles}
    existing_style_ids = {s.style_id: s for s in doc.styles}

    for item in styles_list:
        element = item.get('element')
        style_config = item.get('style', {})
        item_id = item.get('id')

        print(f"DEBUG: Processing style for element '{element}' (id: {item_id})")

        # Determine target style candidates
        target_candidates = element_style_map.get(element, [])
        
        # Fallback for ID-based lookup
        if not target_candidates:
             if item_id == 'heading1': target_candidates = ['Heading 1', '标题 1']
             elif item_id == 'heading2': target_candidates = ['Heading 2', '标题 2']
             elif item_id == 'heading3': target_candidates = ['Heading 3', '标题 3']
             elif item_id == 'paragraph': target_candidates = ['Normal', '正文']

        if not target_candidates:
            print(f"DEBUG: No mapping found for element '{element}'")
            continue
        
        # Find the actual style in the document
        word_style = None
        
        # 1. Try exact name match
        for name in target_candidates:
            if name in existing_styles:
                word_style = existing_styles[name]
                print(f"DEBUG: Found style by name: {name}")
                break
        
        # 2. Try style_id match (e.g. Heading1)
        if not word_style:
             for name in target_candidates:
                 # Standard Word style IDs often remove spaces (Heading 1 -> Heading1)
                 style_id_guess = name.replace(" ", "")
                 if style_id_guess in existing_style_ids:
                     word_style = existing_style_ids[style_id_guess]
                     print(f"DEBUG: Found style by ID: {style_id_guess}")
                     break

        if not word_style:
            # 3. Try case-insensitive scan
            for s in doc.styles:
                s_name_lower = s.name.lower()
                s_id_lower = s.style_id.lower()
                for candidate in target_candidates:
                    if s_name_lower == candidate.lower() or s_id_lower == candidate.replace(" ", "").lower():
                        word_style = s
                        print(f"DEBUG: Found style by partial match: {s.name}")
                        break
                if word_style: break

        if not word_style:
            print(f"DEBUG: Style not found in doc for candidates: {target_candidates}")
            continue

        try:
            font = word_style.font
            p_format = word_style.paragraph_format
            
            # --- Font Size ---
            if 'fontSize' in style_config:
                try:
                    px_val = style_config['fontSize']
                    if px_val:
                        val = None
                        if isinstance(px_val, (int, float)):
                            val = float(px_val)
                        elif isinstance(px_val, str) and px_val.strip():
                             match = re.search(r'(\d+(\.\d+)?)', px_val)
                             if match:
                                 val = float(match.group(1))
                        
                        if val is not None:
                            if isinstance(px_val, str) and 'pt' in px_val.lower():
                                font.size = Pt(val)
                            else:
                                # Default assumption for Global Styles setup in JS is px (CSS based defaultStyles)
                                font.size = Pt(val * 0.75)

                except Exception as e: 
                    print(f"DEBUG: Error setting fontSize: {e}")
                
            # --- Color ---
            if 'color' in style_config:
                try:
                    rgb = hex_to_rgb(style_config['color'])
                    if rgb:
                        font.color.rgb = RGBColor(*rgb)
                except Exception as e:
                     print(f"DEBUG: Error setting color: {e}")
            
            # --- Bold / Italic ---
            if 'bold' in style_config:
                font.bold = bool(style_config['bold'])
                
            if 'italic' in style_config:
                font.italic = bool(style_config['italic'])
                
            # --- Font Family ---
            if 'fontFamily' in style_config:
                try:
                    fname = style_config['fontFamily'].replace('"', '').replace("'", "")
                    
                    # Direct access via style element (CT_Style)
                    if hasattr(word_style, 'element'):
                        rPr = word_style.element.get_or_add_rPr()
                        rFonts = rPr.get_or_add_rFonts()
                        
                        # 1. Set explicit fonts for all regions
                        rFonts.set(qn('w:eastAsia'), fname)
                        rFonts.set(qn('w:ascii'), fname)
                        rFonts.set(qn('w:hAnsi'), fname)
                        rFonts.set(qn('w:cs'), fname)
                        
                        # 2. Critical: Remove Theme bindings effectively
                        # If these attributes exist, Word ignores the specific font names set above.
                        if qn('w:eastAsiaTheme') in rFonts.attrib:
                            del rFonts.attrib[qn('w:eastAsiaTheme')]
                        if qn('w:asciiTheme') in rFonts.attrib:
                            del rFonts.attrib[qn('w:asciiTheme')]
                        if qn('w:hAnsiTheme') in rFonts.attrib:
                            del rFonts.attrib[qn('w:hAnsiTheme')]
                        if qn('w:cstheme') in rFonts.attrib:
                            del rFonts.attrib[qn('w:cstheme')]
                            
                    # Update high-level property for consistency
                    font.name = fname
                        
                except Exception as e:
                     print(f"DEBUG: Error setting fontFamily: {e}")
            
            # --- Paragraph Formats ---
            if 'lineHeight' in style_config:
                try:
                    val = float(style_config['lineHeight'])
                    p_format.line_spacing = val 
                except Exception as e:
                    print(f"DEBUG: Error setting lineHeight: {e}")
            
            # --- Margins (marginTop / marginBottom) ---
            if 'marginTop' in style_config:
                try:
                     val = float(style_config['marginTop'])
                     # Approximate em to pt conversation if unitless, or assume defaults
                     # 1 em ~= 12pt generally in editor context fallback
                     p_format.space_before = Pt(val * 12)
                except Exception as e:
                    print(f"DEBUG: Error setting marginTop: {e}")
                
            if 'marginBottom' in style_config:
                try:
                     val = float(style_config['marginBottom'])
                     p_format.space_after = Pt(val * 12)
                except Exception as e:
                    print(f"DEBUG: Error setting marginBottom: {e}")

        except Exception as e:
            print(f"ERROR: Failed to update attributes for style {word_style.name}: {e}")

@export_bp.route('/docx', methods=['POST'])
def export_docx():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"DEBUG: /docx endpoint received keys: {list(data.keys())}")
        
        title = data.get('title', 'Document')
        editor_json = data.get('content', {})
        styles_list = data.get('styles', []) # Get styles
        
        print(f"DEBUG: styles_list type: {type(styles_list)}, length: {len(styles_list) if isinstance(styles_list, list) else 'N/A'}")
        
        if not editor_json:
             return jsonify({'error': 'No content provided'}), 400

        doc = Document()
        
        # Apply Custom Styles
        update_doc_styles(doc, styles_list)

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


# ==========================================
# LaTeX Export Logic
# ==========================================

def escape_latex(text):
    """Escape special characters for LaTeX and filter unsupported symbols (Emojis)"""
    if not text:
        return ""
    
    # 1. Filter out Emojis and unsupported symbols
    # Remove characters outside BMP (Basic Multilingual Plane), e.g., 🚧 (U+1F6A7)
    text = "".join(c for c in text if c <= '\uFFFF')
    
    # Remove specific BMP ranges for Symbols/Dingbats (likely to crash standard fonts), e.g., ✅ (U+2705)
    # Range: Dingbats (U+2700-U+27BF), Misc Symbols (U+2600-U+26FF)
    text = re.sub(r'[\u2600-\u27BF]', '', text)
    
    # 2. Escape LaTeX special characters
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    
    escaped = ""
    for char in text:
        escaped += special_chars.get(char, char)
    return escaped

def get_latex_color(hex_color):
    """Convert hex string to LaTeX HTML color syntax"""
    if not hex_color or not hex_color.startswith('#'):
        return None
    return hex_color.lstrip('#').upper()

class LatexExporter:
    def __init__(self, content_json, styles_list):
        self.content = content_json
        self.styles = styles_list
        self.images = [] # List of tuples: (filename, stream)
        self.image_counter = 0
        
        # Parse styles into a usable map: element -> color_hex
        self.global_colors = {}
        self._parse_styles()

    def _parse_styles(self):
        """Extract color colors from global styles"""
        if not self.styles: return
        
        # Map internal IDs or Elements to our processing logic
        # Elements: p, h1, h2, h3, blockquote?
        for item in self.styles:
            element = item.get('element')
            style = item.get('style', {})
            color = style.get('color')
            if element and color and color != '#000000' and color != '#333333': # Ignore near-blacks used as defaults
                self.global_colors[element] = get_latex_color(color)

    def process_inline(self, content):
        """Process inline text nodes to LaTeX string"""
        if not content: return ""
        
        result = []
        for node in content:
            node_type = node.get('type')
            
            if node_type == 'text':
                text = escape_latex(node.get('text', ''))
                marks = node.get('marks', [])
                
                # Apply marks (wrappers)
                # Order matters? LaTeX handles nesting well usually.
                
                prefix = ""
                suffix = ""
                
                for mark in marks:
                    m_type = mark.get('type')
                    attrs = mark.get('attrs', {})
                    
                    if m_type == 'bold':
                        prefix = r"\textbf{" + prefix
                        suffix = suffix + "}"
                    elif m_type == 'italic':
                        prefix = r"\textit{" + prefix
                        suffix = suffix + "}"
                    elif m_type == 'underline':
                        prefix = r"\uline{" + prefix
                        suffix = suffix + "}"
                    elif m_type == 'strike':
                        prefix = r"\sout{" + prefix
                        suffix = suffix + "}"
                    elif m_type == 'code':
                        prefix = r"\texttt{" + prefix
                        suffix = suffix + "}"
                    elif m_type == 'textStyle':
                        color = attrs.get('color')
                        if color:
                            c_hex = get_latex_color(color)
                            if c_hex:
                                prefix = r"\textcolor[HTML]{" + c_hex + "}{" + prefix
                                suffix = suffix + "}"
                                
                    elif m_type == 'link':
                        href = attrs.get('href', '')
                        # \href{url}{text}
                        # We need to wrap the *inner* text, so href goes outside?
                        # Actually link is usually the outer-most mark stylistically.
                        # But TipTap marks can be any order.
                        # Let's wrap current result.
                        prefix = r"\href{" + href + "}{" + prefix
                        suffix = suffix + "}"

                result.append(f"{prefix}{text}{suffix}")
                
            elif node_type == 'hardBreak':
                result.append(r"\\")
                
        return "".join(result)

    def process_node(self, node):
        """Process a block node"""
        node_type = node.get('type')
        content = node.get('content', [])
        attrs = node.get('attrs', {})
        latex_out = ""

        if node_type == 'doc':
            for child in content:
                latex_out += self.process_node(child) + "\n"

        elif node_type == 'heading':
            level = attrs.get('level', 1)
            text = self.process_inline(content)
            
            # Apply global color for heading if exists
            h_tag = f"h{level}"
            if h_tag in self.global_colors:
                text = r"\textcolor[HTML]{" + self.global_colors[h_tag] + "}{" + text + "}"
            
            if level == 1: latex_out = f"\\section{{{text}}}\n"
            elif level == 2: latex_out = f"\\subsection{{{text}}}\n"
            elif level == 3: latex_out = f"\\subsubsection{{{text}}}\n"
            else: latex_out = f"\\paragraph{{{text}}}\n"

        elif node_type == 'paragraph':
            text = self.process_inline(content)
            if not text.strip():
                return "\n" # Empty paragraph
            
            # Global color for paragraph
            if 'p' in self.global_colors:
                 text = r"\textcolor[HTML]{" + self.global_colors['p'] + "}{" + text + "}"
                 
            alignment = attrs.get('textAlign')
            if alignment == 'center':
                latex_out = "\\begin{center}\n" + text + "\n\\end{center}\n"
            elif alignment == 'right':
                latex_out = "\\begin{flushright}\n" + text + "\n\\end{flushright}\n"
            else:
                latex_out = text + "\n\n"

        elif node_type == 'bulletList':
            latex_out = "\\begin{itemize}\n"
            for child in content:
                if child.get('type') == 'listItem':
                    latex_out += "\\item " + self._process_list_item(child) + "\n"
            latex_out += "\\end{itemize}\n"

        elif node_type == 'orderedList':
            latex_out = "\\begin{enumerate}\n"
            for child in content:
                if child.get('type') == 'listItem':
                    latex_out += "\\item " + self._process_list_item(child) + "\n"
            latex_out += "\\end{enumerate}\n"

        elif node_type == 'blockquote':
            text = ""
            for child in content:
                text += self.process_node(child)
            latex_out = "\\begin{quote}\n" + text + "\\end{quote}\n"

        elif node_type == 'codeBlock':
            code = ""
            for child in content:
                if child.get('type') == 'text':
                    code += child.get('text', '')
            # Use listings
            latex_out = "\\begin{lstlisting}\n" + code + "\n\\end{lstlisting}\n"

        elif node_type == 'horizontalRule':
            latex_out = "\n\\hrulefill\n\n"

        elif node_type == 'image':
            src = attrs.get('src')
            if src:
                self.image_counter += 1
                ext = 'png'
                if src.lower().endswith('.jpg') or src.lower().endswith('.jpeg'): ext = 'jpg'
                
                filename = f"image_{self.image_counter}.{ext}"
                stream = get_image_stream(src)
                
                if stream:
                    self.images.append((filename, stream))
                    caption = escape_latex(attrs.get('alt', ''))
                    latex_out = f"""
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{assets/{filename}}}
    \\caption{{{caption}}}
\\end{{figure}}
"""
        
        elif node_type == 'table':
            # Simplified table handling
            rows = content
            if rows:
                latex_out = "\\begin{table}[h]\n\\centering\n"
                
                # Analyze columns
                first_row = rows[0].get('content', [])
                num_cols = len(first_row)
                col_def = "| " + " | ".join(["l"] * num_cols) + " |"
                
                latex_out += f"\\begin{{tabular}}{{{col_def}}}\n\\hline\n"
                
                for row_idx, row in enumerate(rows):
                    cells = row.get('content', [])
                    row_texts = []
                    for cell in cells:
                         cell_content = cell.get('content', [])
                         # Flatten cell content (usually paragraphs)
                         c_text = ""
                         for block in cell_content:
                             c_text += self.process_inline(block.get('content', []))
                         row_texts.append(c_text)
                    
                    latex_out += " & ".join(row_texts) + " \\\\\n\\hline\n"
                
                latex_out += "\\end{tabular}\n\\end{table}\n"

        return latex_out

    def _process_list_item(self, node):
        # List items usually contain paragraphs. We need to strip paragraph breaks for basic items
        # or handle nested blocks properly.
        content = node.get('content', [])
        result = ""
        for child in content:
            # We strip the double newline from paragraph process for list items to look tighter
            result += self.process_node(child).strip() + " "
        return result

    def generate_full_tex(self, title):
        body = self.process_node(self.content if self.content.get('type') == 'doc' else {'type': 'doc', 'content': []})
        
        preamble = r"""% !TeX program = xelatex
\documentclass{article}
\usepackage[UTF8]{ctex}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{listings}
\usepackage[normalem]{ulem}
\usepackage{geometry}
\geometry{a4paper, scale=0.8}
\usepackage{booktabs}
\usepackage{float}

% Code highlighting style
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}
\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegray},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}
\lstset{style=mystyle}

\title{""" + escape_latex(title) + r"""}
\date{\today}

\begin{document}
\maketitle

"""
        return preamble + body + "\n\\end{document}"


@export_bp.route('/latex', methods=['POST'])
def export_latex():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        title = data.get('title', 'Document')
        # Handle both list and dict content input for robustness
        raw_content = data.get('content', {})
        if isinstance(raw_content, list):
             editor_json = {'type': 'doc', 'content': raw_content}
        else:
             editor_json = raw_content

        styles_list = data.get('styles', [])

        exporter = LatexExporter(editor_json, styles_list)
        tex_content = exporter.generate_full_tex(title)
        
        # Create ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Add main.tex
            zf.writestr('main.tex', tex_content)
            
            # Add images
            if exporter.images:
                for filename, stream in exporter.images:
                    # stream is open file or BytesIO
                    if isinstance(stream, io.BytesIO):
                        data = stream.getvalue()
                    else:
                        data = stream.read()
                        stream.close()
                    zf.writestr(f'assets/{filename}', data)
        
        memory_file.seek(0)
        
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
        if not safe_title: safe_title = "document"

        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f"{safe_title}_latex.zip",
            mimetype='application/zip'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


