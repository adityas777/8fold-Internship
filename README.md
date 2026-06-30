# Eightfold Candidate Profile Pipeline

## What this is
This project is an end-to-end recruitment candidate profile processing engine. It ingests candidate data from both structured and unstructured sources, normalizes contact/location/skill fields, resolves duplicate identities across sources using fuzzy string comparison, and projects the final unified profiles into custom schema formats defined by dynamic runtime configuration files.

## Architecture
The processing pipeline follows a deterministic and traceable sequence:
1. **detect**: Identifies the source type from file extensions, URL patterns, or content structures.
2. **extract**: Parses raw values from the files/APIs into untyped intermediate representations.
3. **normalize**: Converts values into canonical shapes (E.164 phones, YYYY-MM dates, ISO country codes, and standardized skills).
4. **merge**: Groups matching profiles together (via email/phone/name edit distance), resolves field conflicts by source priority, and records detailed provenance tracking.
5. **confidence**: Computes confidence scores for each field and candidate based on extraction reliability and multi-source consensus.
6. **project**: Dynamically maps and structures the canonical fields according to runtime config files.
7. **validate**: Verifies projected outputs against dynamically generated JSON Schemas.

## Sources Implemented
- **Structured**: Recruiter CSV export parser mapping standard spreadsheet headers.
- **Unstructured**: 
  - **Resume PDF/DOCX**: Extracts text using `pdfplumber`/`python-docx` and scans content for contact info and key skills.
  - **GitHub Profile API**: Retrieves candidate names, locations, bios, and repository languages as skills via the public GitHub REST API.
  - **Recruiter Notes**: Extracts years of experience and names from free-text notes.
- **Descoped**:
  - **LinkedIn Scraping**: Left out because of Terms of Service (TOS) restrictions, login walling, and lack of a public API.
  - **ATS JSON**: Added template code but descoped from active source files in the demo run as Recruiter CSV is sufficient for structured representation.

## How to Run

### Setup:
1. Ensure Python 3.8+ is installed.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Execution:
To run the pipeline on the sample files with the custom projection configuration:
```powershell
python cli.py --sources data/recruiter_export.csv data/resumes/jane_doe.pdf data/recruiter_notes.txt --config config/example_config.json --out outputs/result.json
```

To run with the default schema projection (all fields, no configuration):
```powershell
python cli.py --sources data/recruiter_export.csv data/resumes/jane_doe.pdf data/recruiter_notes.txt --out outputs/default_result.json
```

## Config Format
The projection mapping configuration (e.g. `config/example_config.json`) looks like this:
```json
{
  "fields": [
    { "path": "candidate_id", "from": "candidate_id", "type": "string", "required": true, "on_missing": "error" },
    { "path": "full_name", "from": "full_name", "type": "string", "required": true, "on_missing": "error" },
    { "path": "emails", "from": "emails", "type": "array", "required": false, "on_missing": "omit" },
    { "path": "phones", "from": "phones", "type": "array", "required": false, "on_missing": "omit" },
    { "path": "location", "from": "location", "type": "string", "required": false, "on_missing": "null" },
    { "path": "years_experience", "from": "years_experience", "type": "number", "required": false, "on_missing": "null" },
    { "path": "skills", "from": "skills", "type": "array", "required": false, "on_missing": "omit" }
  ],
  "include_confidence": true,
  "include_provenance": true
}
```
### Configuration Keys:
- **`fields`**: List of projection mappings from canonical fields to output targets.
  - `path`: Target output property path (supports dot notation like `contact.email`).
  - `from`: Source canonical field path.
  - `type`: Target JSON data type (`string`, `number`, `integer`, `boolean`, `array`).
  - `required`: Boolean specifying if the field is mandatory.
  - `on_missing`: Action on missing values: `null` (keeps key with null value), `omit` (drops key), or `error` (raises exception).
- **`include_confidence`**: Boolean. If `true`, includes the computed `overall_confidence` score.
- **`include_provenance`**: Boolean. If `true`, attaches execution provenance metadata listing the source, extraction method, and raw values.

## Tests
Run the test suite to verify normalizers, entity resolution, merging policies, and runtime projection:
```powershell
pytest tests/ -v
```

## Known Limitations & Future Enhancements
- **Fuzzy Name Clustering**: Uses simple Levenshtein edit distance for deduplication; Jaro-Winkler or double-metaphone block keys would reduce false matches on longer text lists.
- **Email Conflict Limit**: If a candidate has completely different email addresses across sources with no shared name or phone number, they will be processed as separate identities.
- **Deep Resume Parsing**: Heuristics are optimized for clean text blocks. Complex column-based multi-page layouts may need a dedicated transformer-based layout parser.
