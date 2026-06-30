import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_folders():
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/resumes', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('tests/gold', exist_ok=True)

def generate_csv():
    # We will generate a recruiter export CSV.
    # We want 2-3 rows. Let's make:
    # Row 1: Jane Doe (overlap with resume and GitHub jane_doe)
    # Row 2: Bob Smith (one phone blank, test robustness)
    # Row 3: Malformed row (we can simulate this, or write normal data but make it slightly irregular)
    csv_path = 'data/recruiter_export.csv'
    rows = [
        ['name', 'email', 'phone', 'current_company', 'title', 'location'],
        ['Jane Doe', 'jane.doe@example.com', '+91 98765 43210', 'Google', 'Senior Software Engineer', 'Mumbai, India'],
        ['Bob Smith', 'bob.smith@example.com', '', 'Microsoft', 'Software Engineer', 'Seattle, USA'],
        ['Alice Johnson', 'alice.j@example.com', '+1 415 555 2671', 'Meta', 'Product Manager', 'San Francisco']
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Generated sample CSV at {csv_path}")

def generate_resume_pdf():
    # Generate data/resumes/jane_doe.pdf
    pdf_path = 'data/resumes/jane_doe.pdf'
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    # Simple clean styling for a resume
    name_style = ParagraphStyle(
        'ResumeName',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        spaceAfter=4
    )
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'ResumeSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        spaceAfter=6
    )
    
    story.append(Paragraph("JANE DOE", name_style))
    story.append(Paragraph("Email: jane.doe@example.com | Phone: +91 98765 43210 | Location: Mumbai, India | GitHub: github.com/janedoe", contact_style))
    
    story.append(Paragraph("Professional Summary", h2_style))
    story.append(Paragraph("Experienced Software Engineer specializing in backend systems, distributed architectures, and web technologies.", body_style))
    
    story.append(Paragraph("Skills", h2_style))
    story.append(Paragraph("Python, Django, FastAPI, ReactJS, SQL, Git, Docker, Kubernetes", body_style))
    
    story.append(Paragraph("Experience", h2_style))
    story.append(Paragraph("<b>Senior Software Engineer</b><br/>Google, Mumbai, India<br/>March 2022 to Present<br/>Leading development of core distributed service features. Restructured API services to improve latency by 20%. mentored junior developers.", body_style))
    story.append(Paragraph("<b>Software Engineer</b><br/>Amazon, Bangalore, India<br/>January 2020 to February 2022<br/>Built scalable data pipelines and backend web applications using Python and Django. Worked closely with product teams to design robust API services.", body_style))
    
    story.append(Paragraph("Education", h2_style))
    story.append(Paragraph("<b>Bachelor of Technology in Computer Science</b><br/>Indian Institute of Technology Bombay, Mumbai, India<br/>July 2016 to May 2020", body_style))
    
    doc.build(story)
    print(f"Generated sample PDF resume at {pdf_path}")

def generate_notes():
    # Recruiter notes: free text with a couple of mentions
    notes_path = 'data/recruiter_notes.txt'
    content = """Recruiter Notes:
Candidate Jane Doe (jane.doe@example.com) seemed very strong during the call.
She has about 6.5 years of experience in total, mostly at Google and Amazon.
Her skills include Python, React, and SQL. Currently located in Mumbai.
Would be a great fit for the senior backend developer position.
"""
    with open(notes_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated sample recruiter notes at {notes_path}")

def generate_example_config():
    # We will write the example config to config/example_config.json
    import json
    config_path = 'config/example_config.json'
    config = {
        "fields": [
            { "path": "candidate_id", "from": "candidate_id", "type": "string", "required": True, "on_missing": "error" },
            { "path": "full_name", "from": "full_name", "type": "string", "required": True, "on_missing": "error" },
            { "path": "emails", "from": "emails", "type": "array", "required": False, "on_missing": "omit" },
            { "path": "phones", "from": "phones", "type": "array", "required": False, "on_missing": "omit" },
            { "path": "location", "from": "location", "type": "string", "required": False, "on_missing": "null" },
            { "path": "years_experience", "from": "years_experience", "type": "number", "required": False, "on_missing": "null" },
            { "path": "skills", "from": "skills", "type": "array", "required": False, "on_missing": "omit" },
            { "path": "experience", "from": "experience", "type": "array", "required": False, "on_missing": "omit" }
        ],
        "include_confidence": True,
        "include_provenance": True
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    print(f"Generated example config at {config_path}")

if __name__ == '__main__':
    create_folders()
    generate_csv()
    # Resume PDF relies on reportlab, we will run this script once reportlab is installed
    try:
        generate_resume_pdf()
    except ImportError:
        print("reportlab not installed yet. Skipping resume PDF generation for now.")
    generate_notes()
    generate_example_config()
