import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(output_path, name, email):
    # Set page margins to fit exactly on one page (0.5 inch margins)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles to look premium and fit on a single page
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=2
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=8
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8,
        leading=9.5,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=3
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-8,
        spaceAfter=2
    )
    
    # Header
    story.append(Paragraph("Eightfold Candidate Profile Pipeline — Design Document", title_style))
    story.append(Paragraph(f"Candidate Name: {name} &nbsp;|&nbsp; Email: {email} &nbsp;|&nbsp; Target: Eightfold Candidate Pipeline", meta_style))
    
    # 2.1 Pipeline Breakdown
    story.append(Paragraph("1. Pipeline Breakdown", h2_style))
    pipeline_text = (
        "The system processes multiple recruitment sources end-to-end through a modular sequence: "
        "<b>detect</b> (identifies source type from file extensions/URLs) &rarr; "
        "<b>extract</b> (extracts raw key-value pairs into intermediate dicts) &rarr; "
        "<b>normalize</b> (standardizes E.164 phones, YYYY-MM dates, ISO-3166 countries, and skills) &rarr; "
        "<b>merge</b> (groups candidates via match-key blocking, resolves conflicts, and generates provenance) &rarr; "
        "<b>confidence</b> (assigns scores using source weight + consensus bonus) &rarr; "
        "<b>project</b> (filters/remaps fields via runtime config) &rarr; "
        "<b>validate</b> (validates output against custom JSON Schema)."
    )
    story.append(Paragraph(pipeline_text, body_style))
    
    # 2.2 Canonical Schema & Normalized Formats
    story.append(Paragraph("2. Canonical Schema & Normalized Formats", h2_style))
    schema_intro = "The internal record uses a strict Pydantic model representation with normalized fields:"
    story.append(Paragraph(schema_intro, body_style))
    story.append(Paragraph("&bull; <b>Phones:</b> Standardized to E.164 (e.g. +91 99999 99999) using the <i>phonenumbers</i> library, falling back to IN (+91) region.", bullet_style))
    story.append(Paragraph("&bull; <b>Dates:</b> Standardized to YYYY-MM format; free-text (e.g., 'Jan 2021-Present') parsed using <i>python-dateutil</i> and regex; 'Present' maps to null end date.", bullet_style))
    story.append(Paragraph("&bull; <b>Country:</b> Normalized to ISO-3166 alpha-2 (e.g., 'US', 'IN') via dictionary lookup of common names and country aliases.", bullet_style))
    story.append(Paragraph("&bull; <b>Skills:</b> Case-insensitive matching against a canonical skills list with alias expansion (e.g. 'ReactJS' &rarr; 'React').", bullet_style))
    
    # 2.3 Merge & Conflict-Resolution Policy
    story.append(Paragraph("3. Merge & Conflict-Resolution Policy", h2_style))
    merge_text = (
        "<b>Match Keys:</b> Identity grouping uses a blocking key chain: exact match on normalized email, exact match on normalized phone, or fuzzy match on full name (Levenshtein distance > 0.85). "
        "<b>Conflict Resolution:</b> Field-level winners are determined by configurable source priority order: for identity and contact details, <i>resume > ATS JSON > recruiter CSV > notes > GitHub</i>; for skills and links, <i>GitHub > resume > ATS JSON > CSV</i>; for experience/education, <i>resume > ATS JSON > CSV</i>. "
        "<b>Confidence Formula:</b> Each field confidence is computed as: <i>base_score(extraction_method) + corroboration_bonus - recency_decay</i>. Base scores are: structured = 0.9, GitHub API = 0.8, resume regex = 0.6, notes = 0.4. Corroboration adds +0.05 per agreeing source, capped at 1.0."
    )
    story.append(Paragraph(merge_text, body_style))
    
    # 2.4 Runtime Config Handling
    story.append(Paragraph("4. Runtime Config Handling", h2_style))
    config_text = (
        "The projection layer maps the canonical record to custom output shapes at runtime. Config defines: "
        "<b>path</b> (output path, supporting dot-notation), <b>from</b> (canonical source path), <b>type</b> (expected type), and <b>on_missing</b> policy (<i>null</i> keeps key as null; <i>omit</i> drops key; <i>error</i> collects field-level error and raises exception). "
        "The system generates a dynamic JSON Schema matching the config shape and validates the projected output using <i>jsonschema</i>. Errors are aggregated per-candidate."
    )
    story.append(Paragraph(config_text, body_style))
    
    # 2.5 Edge Cases Handled
    story.append(Paragraph("5. Edge Cases Handled", h2_style))
    story.append(Paragraph("&bull; <b>1. Multiple Emails:</b> If same candidate has different emails, they remain separate candidates unless name/phone matches; noted as a known limitation.", bullet_style))
    story.append(Paragraph("&bull; <b>2. Missing Country Code:</b> Assumes regional fallback (IN) but scales field confidence down by a factor of 0.5.", bullet_style))
    story.append(Paragraph("&bull; <b>3. Source Failure:</b> Malformed CSV lines or GitHub API rate-limits/404s are logged as warnings and skipped; the pipeline continues processing other rows.", bullet_style))
    story.append(Paragraph("&bull; <b>4. Conflicting Experience:</b> Takes highest-confidence source for years_experience (e.g. resume = 3, notes = 5 &rarr; output 3) and stores the other in provenance for audit.", bullet_style))
    
    # 2.6 Deliberately Left Out
    story.append(Paragraph("6. Deliberately Left Out (Future Enhancements)", h2_style))
    story.append(Paragraph("&bull; <b>LinkedIn Scraping:</b> Omitted due to TOS restrictions/auth requirements; mock ATS JSON acts as a placeholder for manual data uploads.", bullet_style))
    story.append(Paragraph("&bull; <b>Fuzzy Name Clustering:</b> Advanced cross-source clustering (e.g. Jaro-Winkler/double-metaphone) omitted for a simple Levenshtein implementation.", bullet_style))
    story.append(Paragraph("&bull; <b>User Interface:</b> UI polish skipped in favor of a robust, deterministic, testable CLI tool outputs JSON to standard output and files.", bullet_style))
    
    doc.build(story)
    print(f"Successfully generated design document PDF at: {output_path}")

if __name__ == '__main__':
    # Default values or arguments
    name = "Candidate"
    email = "candidate@example.com"
    if len(sys.argv) > 2:
        name = sys.argv[1]
        email = sys.argv[2]
    
    # Save the file to the parent folder c:\Users\pglap\OneDrive\Desktop\8fold\
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_parent = os.path.dirname(output_dir)
    pdf_filename = f"{name.replace(' ', '')}_{email.replace('@', '_at_')}_Eightfold.pdf"
    output_path = os.path.join(output_parent, pdf_filename)
    
    generate_pdf(output_path, name, email)
