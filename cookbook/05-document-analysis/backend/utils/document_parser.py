# backend/utils/document_parser.py
import io
import re
import fitz  # PyMuPDF

def parse_pdf_to_sentences(file_bytes: bytes) -> list:
    # PyMuPDF requires a stream to read from memory
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    document_structure = []
    sentence_id_counter = 0
    
    for page in doc:
        # Extract the page as a structured dictionary to access font metadata
        blocks = page.get_text("dict")["blocks"]
        
        for b in blocks:
            # We only care about text blocks (type 0)
            if b.get("type") != 0 or "lines" not in b:
                continue
            
            para_html = ""
            for line in b["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span["text"]
                    
                    # Detect bold text either by font name or the internal bold flag
                    is_bold = "bold" in span["font"].lower() or "black" in span["font"].lower()
                    
                    if is_bold:
                        line_text += f"<b>{text}</b>"
                    else:
                        line_text += text
                        
                # Preserve the physical line break from the PDF layout
                para_html += line_text + "<br>"
            
            # Clean up multiple consecutive spaces
            para_html = re.sub(r' +', ' ', para_html).strip()
            
            # Split paragraph into manageable sentences while maintaining the injected HTML tags
            # We split safely by standard punctuation that is followed by a space or a line break
            raw_sentences = re.split(r'(?<=[.!?])(?:\s+|<br>)', para_html)
            
            para_obj = {"paragraph_id": len(document_structure), "sentences": []}
            for text in raw_sentences:
                clean_text = text.strip()
                
                # Check length ignoring the HTML tags we just added
                if len(re.sub(r'<[^>]+>', '', clean_text)) > 5:
                    para_obj["sentences"].append({
                        "sentence_id": sentence_id_counter,
                        "sentence": clean_text
                    })
                    sentence_id_counter += 1
                    
            if para_obj["sentences"]:
                document_structure.append(para_obj)
                
    return document_structure