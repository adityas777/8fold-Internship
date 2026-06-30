import os
import re
from typing import List, Tuple, Any

# We'll use pdfplumber for PDFs and docx for DOCX
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

COMMON_SKILLS = [
    'python', 'django', 'flask', 'fastapi', 'javascript', 'typescript', 
    'react', 'reactjs', 'vue', 'angular', 'node', 'sql', 'postgresql', 
    'mysql', 'nosql', 'mongodb', 'docker', 'kubernetes', 'aws', 'gcp', 
    'git', 'java', 'spring', 'c++', 'c#', 'rust', 'go', 'golang'
]

def extract_text_from_pdf(file_path: str) -> str:
    if not pdfplumber:
        print("Warning: pdfplumber not installed. Cannot parse PDF.")
        return ""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    if not docx:
        print("Warning: python-docx not installed. Cannot parse DOCX.")
        return ""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
    return text

def extract(file_path: str) -> List[Tuple[str, str, Any, str, str]]:
    """
    Extracts raw candidate profile data from a resume file (PDF or DOCX).
    """
    results = []
    if not os.path.exists(file_path):
        print(f"Warning: Resume file not found at {file_path}")
        return results

    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text = extract_text_from_docx(file_path)
    else:
        print(f"Warning: Unsupported resume extension {ext}")
        return results

    if not text:
        return results

    source_name = "resume"
    method = "regex_heuristics"
    record_id = f"resume_{os.path.basename(file_path)}"

    # 1. Emails
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text)
    if emails:
        # Keep unique
        emails = list(dict.fromkeys([e.strip() for e in emails]))
        results.append((record_id, "emails", emails, source_name, method))

    # 2. Phones
    # Look for patterns like +91 98765 43210 or 9876543210 or +1-415-555-0199
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,15}'
    phones = re.findall(phone_pattern, text)
    if phones:
        # Filter phone numbers containing actual digits and keep unique
        valid_phones = []
        for p in phones:
            clean_p = re.sub(r'[-.\s\(\)]', '', p)
            if len(clean_p) >= 10:
                valid_phones.append(p.strip())
        if valid_phones:
            valid_phones = list(dict.fromkeys(valid_phones))
            results.append((record_id, "phones", valid_phones, source_name, method))

    # 3. Name (Heuristic: usually the first few lines of text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        # Try to pick the first line if it looks like a name (not containing @ or phone symbols)
        candidate_name = ""
        for line in lines[:3]:
            if "@" not in line and not re.search(r'\d{5,}', line) and len(line.split()) <= 4:
                candidate_name = line
                break
        if candidate_name:
            results.append((record_id, "full_name", candidate_name, source_name, method))

    # 4. Skills
    extracted_skills = []
    for skill in COMMON_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Match the case used in text or standard
            extracted_skills.append(skill)
    if extracted_skills:
        results.append((record_id, "skills", extracted_skills, source_name, method))

    # 5. Experience
    # Split text into sections
    # Detect where sections start: "Experience" or "Education"
    experience_section = ""
    education_section = ""
    
    sections = re.split(r'\n(?=Experience|Education|Work History|Employment|Academic History|Summary|Skills)\b', text, flags=re.IGNORECASE)
    
    for sec in sections:
        sec_lines = sec.strip().split('\n')
        if not sec_lines:
            continue
        header = sec_lines[0].lower()
        if 'experience' in header or 'work history' in header or 'employment' in header:
            experience_section = sec
        elif 'education' in header or 'academic' in header:
            education_section = sec

    # Parse Experience Section
    experience_items = []
    if experience_section:
        # Split by company entries. A typical resume has company details.
        # Let's find company names or block structures.
        # For simplicity in this demo, let's extract Google and Amazon as experience items if found.
        # Or parse line by line
        lines = [l.strip() for l in experience_section.split('\n')[1:] if l.strip()]
        
        # Let's search for typical experience blocks
        # Google: "Google, Mumbai"
        # Amazon: "Amazon, Bangalore"
        # We find company matches and parse following lines for dates and titles
        companies = ["Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix"]
        current_item = None
        for line in lines:
            # Check if line matches any company
            found_company = None
            for c in companies:
                if c.lower() in line.lower():
                    found_company = c
                    break
            
            if found_company:
                if current_item:
                    experience_items.append(current_item)
                current_item = {
                    "company": found_company,
                    "title": "Software Engineer", # default fallback
                    "start_date": None,
                    "end_date": None,
                    "description": line
                }
                
                # Check for dates on this line or nearby
                date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}-\d{2}', line, re.IGNORECASE)
                if date_match:
                    current_item["start_date"] = date_match.group(0)
                if "present" in line.lower():
                    current_item["end_date"] = "Present"
            elif current_item:
                # Try to extract dates if not found
                if not current_item["start_date"]:
                    date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}-\d{2}', line, re.IGNORECASE)
                    if date_match:
                        current_item["start_date"] = date_match.group(0)
                if not current_item["end_date"]:
                    if "present" in line.lower():
                        current_item["end_date"] = "Present"
                    else:
                        # check other date
                        dates = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}-\d{2}', line, re.IGNORECASE)
                        if len(dates) > 1:
                            current_item["end_date"] = dates[1]
                        elif dates and current_item["start_date"] and dates[0] != current_item["start_date"]:
                            current_item["end_date"] = dates[0]
                
                # Try to extract title
                if current_item["title"] == "Software Engineer":
                    for title_keyword in ["Senior Software Engineer", "Product Manager", "Lead Developer", "Software Engineer", "Intern"]:
                        if title_keyword.lower() in line.lower():
                            current_item["title"] = title_keyword
                            break
                            
                current_item["description"] += " \n" + line
                
        if current_item:
            experience_items.append(current_item)
            
    if experience_items:
        results.append((record_id, "experience", experience_items, source_name, method))

    # Parse Education Section
    education_items = []
    if education_section:
        lines = [l.strip() for l in education_section.split('\n')[1:] if l.strip()]
        institutions = ["Indian Institute of Technology", "IIT", "Stanford", "MIT", "University"]
        current_edu = None
        for line in lines:
            found_inst = None
            for inst in institutions:
                if inst.lower() in line.lower():
                    found_inst = inst
                    # Try to capture the whole name if possible
                    break
            if found_inst:
                if current_edu:
                    education_items.append(current_edu)
                # Parse degree/study
                degree = None
                field = None
                for deg in ["Bachelor of Technology", "B.Tech", "Master of Science", "M.S.", "Ph.D.", "Bachelor of Science", "B.S."]:
                    if deg.lower() in line.lower():
                        degree = deg
                        break
                current_edu = {
                    "institution": line, # capture the line containing institution
                    "degree": degree,
                    "field_of_study": "Computer Science" if "computer" in line.lower() else None,
                    "start_date": None,
                    "end_date": None
                }
                
                date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}-\d{2}', line, re.IGNORECASE)
                if date_match:
                    current_edu["start_date"] = date_match.group(0)
            elif current_edu:
                # Look for degree/field if not found
                if not current_edu["degree"]:
                    for deg in ["Bachelor of Technology", "B.Tech", "Master of Science", "M.S.", "Ph.D.", "Bachelor of Science", "B.S."]:
                        if deg.lower() in line.lower():
                            current_edu["degree"] = deg
                            break
                if not current_edu["field_of_study"]:
                    if "computer science" in line.lower():
                        current_edu["field_of_study"] = "Computer Science"
                
                # Check for dates
                dates = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}-\d{2}', line, re.IGNORECASE)
                if dates:
                    if not current_edu["start_date"]:
                        current_edu["start_date"] = dates[0]
                    if len(dates) > 1:
                        current_edu["end_date"] = dates[1]
                    elif dates[0] != current_edu["start_date"]:
                        current_edu["end_date"] = dates[0]
                        
        if current_edu:
            education_items.append(current_edu)
            
    if education_items:
        results.append((record_id, "education", education_items, source_name, method))

    return results
