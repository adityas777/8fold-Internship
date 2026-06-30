import re
from typing import List, Tuple, Any, Dict, Optional
from src.models import CanonicalProfile, SkillEntry, Experience, Education, ProvenanceEntry
from src.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill

# Source priority order by field category
FIELD_PRIORITIES = {
    "full_name": ["resume", "ats_json", "recruiter_csv", "recruiter_notes", "github"],
    "location": ["resume", "ats_json", "recruiter_csv", "recruiter_notes", "github"],
    "headline": ["resume", "github", "ats_json", "recruiter_csv", "recruiter_notes"],
    "years_experience": ["resume", "recruiter_notes", "recruiter_csv", "ats_json", "github"],
    "emails": ["resume", "ats_json", "recruiter_csv", "recruiter_notes", "github"],
    "phones": ["resume", "ats_json", "recruiter_csv", "recruiter_notes", "github"],
}

# Base confidence scores by extraction method
METHOD_BASE_CONFIDENCE = {
    "csv_reader": 0.9,
    "json_parser": 0.9,
    "github_api": 0.8,
    "regex_heuristics": 0.6,
    "regex_notes": 0.4
}

def levenshtein_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    dist = dp[m][n]
    max_len = max(m, n)
    return 1.0 - (dist / max_len)

def build_source_candidates(raw_tuples: List[Tuple[str, str, Any, str, str]]) -> Dict[str, Dict[str, List[Tuple[Any, str, str]]]]:
    """
    Groups raw tuples by record_id.
    Returns dictionary mapping record_id -> canonical_field_name -> list of (raw_value, source_name, method)
    """
    grouped: Dict[str, Dict[str, List[Tuple[Any, str, str]]]] = {}
    for record_id, field_path, raw_value, source_name, method in raw_tuples:
        if record_id not in grouped:
            grouped[record_id] = {}
        if field_path not in grouped[record_id]:
            grouped[record_id][field_path] = []
        grouped[record_id][field_path].append((raw_value, source_name, method))
    return grouped

def match_candidates(grouped_sources: Dict[str, Dict[str, List[Tuple[Any, str, str]]]]) -> List[List[str]]:
    """
    Groups source record_ids that belong to the same candidate using entity resolution.
    """
    # Helper to retrieve normalized match keys for a record_id
    def get_match_keys(record_id: str, fields: Dict[str, List[Tuple[Any, str, str]]]) -> Dict[str, set]:
        keys = {"emails": set(), "phones": set(), "names": set()}
        
        # Extract emails
        if "emails" in fields:
            for val, _, _ in fields["emails"]:
                if isinstance(val, list):
                    for email in val:
                        keys["emails"].add(email.strip().lower())
                else:
                    keys["emails"].add(val.strip().lower())
                    
        # Extract phones
        if "phones" in fields:
            for val, _, _ in fields["phones"]:
                if isinstance(val, list):
                    for phone in val:
                        norm_p = normalize_phone(phone)
                        if norm_p:
                            keys["phones"].add(norm_p)
                else:
                    norm_p = normalize_phone(val)
                    if norm_p:
                        keys["phones"].add(norm_p)
                        
        # Extract names
        if "full_name" in fields:
            for val, _, _ in fields["full_name"]:
                if val:
                    keys["names"].add(val.strip().lower())
                    
        return keys

    # Compute match keys for all record IDs
    record_keys = {r_id: get_match_keys(r_id, fields) for r_id, fields in grouped_sources.items()}
    
    # Simple union-find or grouping based on connectivity
    groups: List[set] = []
    
    for r_id in grouped_sources:
        matched_group_idx = -1
        r_keys = record_keys[r_id]
        
        for idx, g in enumerate(groups):
            # Check overlap of emails or phones
            g_emails = set().union(*(record_keys[g_id]["emails"] for g_id in g))
            g_phones = set().union(*(record_keys[g_id]["phones"] for g_id in g))
            g_names = set().union(*(record_keys[g_id]["names"] for g_id in g))
            
            email_match = bool(r_keys["emails"] & g_emails)
            phone_match = bool(r_keys["phones"] & g_phones)
            
            # Fuzzy name match fallback
            name_match = False
            if not email_match and not phone_match and r_keys["names"] and g_names:
                for r_name in r_keys["names"]:
                    for g_name in g_names:
                        if levenshtein_similarity(r_name, g_name) > 0.85:
                            name_match = True
                            break
                    if name_match:
                        break
                        
            if email_match or phone_match or name_match:
                matched_group_idx = idx
                break
                
        if matched_group_idx != -1:
            groups[matched_group_idx].add(r_id)
        else:
            groups.append({r_id})
            
    return [list(g) for g in groups]

def resolve_field(field_name: str, values: List[Tuple[Any, str, str]]) -> Tuple[Any, float, List[ProvenanceEntry]]:
    """
    Resolves the value of a field based on source priority.
    Returns (winning_value, field_confidence, provenance_entries)
    """
    priorities = FIELD_PRIORITIES.get(field_name, ["resume", "ats_json", "recruiter_csv", "recruiter_notes", "github"])
    
    # Filter empty or null values
    valid_values = []
    for val, src, method in values:
        if val is not None:
            if isinstance(val, str) and not val.strip():
                continue
            if isinstance(val, list) and not val:
                continue
            valid_values.append((val, src, method))
            
    if not valid_values:
        return None, 0.0, []

    # Sort values by priority of the source
    def get_priority_index(item):
        src = item[1]
        if src in priorities:
            return priorities.index(src)
        return len(priorities)  # lowest priority

    valid_values.sort(key=get_priority_index)
    winning_val, winning_src, winning_method = valid_values[0]

    # Calculate confidence: base score of winning method + corroboration bonus
    base_conf = METHOD_BASE_CONFIDENCE.get(winning_method, 0.5)
    
    # Count agreeing sources
    agreeing_sources = {winning_src}
    
    # Check if other sources agree on the value
    for val, src, method in valid_values[1:]:
        if val == winning_val:
            agreeing_sources.add(src)
            
    bonus = 0.05 * (len(agreeing_sources) - 1)
    confidence = min(base_conf + bonus, 1.0)

    # For lists/arrays (like emails, phones, links), we actually combine unique values instead of just picking one winner,
    # but we still track provenance of each unique item
    provenance = []
    for val, src, method in valid_values:
        provenance.append(ProvenanceEntry(
            field=field_name,
            source=src,
            method=method,
            value=str(val)
        ))

    return winning_val, confidence, provenance

def merge(raw_tuples: List[Tuple[str, str, Any, str, str]]) -> List[CanonicalProfile]:
    """
    Main entity resolution and merging function.
    Groups raw tuples, merges candidates, resolves conflicts, and returns canonical profiles.
    """
    grouped_sources = build_source_candidates(raw_tuples)
    groups = match_candidates(grouped_sources)
    
    canonical_profiles = []
    
    for cand_idx, group in enumerate(groups):
        # Gather all field values across the record IDs in this group
        combined_fields: Dict[str, List[Tuple[Any, str, str]]] = {}
        for r_id in group:
            for field, vals in grouped_sources[r_id].items():
                if field not in combined_fields:
                    combined_fields[field] = []
                combined_fields[field].extend(vals)
                
        # Resolve identity fields
        full_name, name_conf, name_prov = resolve_field("full_name", combined_fields.get("full_name", []))
        location, loc_conf, loc_prov = resolve_field("location", combined_fields.get("location", []))
        headline, head_conf, head_prov = resolve_field("headline", combined_fields.get("headline", []))
        years_exp, years_conf, years_prov = resolve_field("years_experience", combined_fields.get("years_experience", []))
        
        # Normalize and merge emails list
        emails_list = []
        email_confidences = []
        emails_provenance = []
        if "emails" in combined_fields:
            for raw_val, src, method in combined_fields["emails"]:
                vals = raw_val if isinstance(raw_val, list) else [raw_val]
                for val in vals:
                    clean_v = val.strip().lower()
                    if clean_v and clean_v not in emails_list:
                        emails_list.append(clean_v)
                        # base confidence
                        email_confidences.append(METHOD_BASE_CONFIDENCE.get(method, 0.5))
                        emails_provenance.append(ProvenanceEntry(field="emails", source=src, method=method, value=clean_v))
        emails_conf = sum(email_confidences) / len(email_confidences) if email_confidences else 0.0

        # Normalize and merge phones list
        phones_list = []
        phone_confidences = []
        phones_provenance = []
        
        # Determine default region from location if possible
        default_region = "IN"
        if location and ("usa" in location.lower() or "united states" in location.lower() or "sf" in location.lower() or "seattle" in location.lower() or "us" in location.lower()):
            default_region = "US"

        if "phones" in combined_fields:
            for raw_val, src, method in combined_fields["phones"]:
                vals = raw_val if isinstance(raw_val, list) else [raw_val]
                for val in vals:
                    norm_p = normalize_phone(val, default_region)
                    if norm_p and norm_p not in phones_list:
                        phones_list.append(norm_p)
                        phone_confidences.append(METHOD_BASE_CONFIDENCE.get(method, 0.5))
                        phones_provenance.append(ProvenanceEntry(field="phones", source=src, method=method, value=norm_p))
        phones_conf = sum(phone_confidences) / len(phone_confidences) if phone_confidences else 0.0

        # Normalize and merge links list
        links_list = []
        links_provenance = []
        if "links" in combined_fields:
            for raw_val, src, method in combined_fields["links"]:
                vals = raw_val if isinstance(raw_val, list) else [raw_val]
                for val in vals:
                    clean_l = val.strip()
                    if clean_l and clean_l not in links_list:
                        links_list.append(clean_l)
                        links_provenance.append(ProvenanceEntry(field="links", source=src, method=method, value=clean_l))

        # Normalize and merge skills list
        skills_map: Dict[str, Tuple[float, List[str]]] = {}  # skill_name -> (max_confidence, sources)
        skills_provenance = []
        if "skills" in combined_fields:
            for raw_val, src, method in combined_fields["skills"]:
                vals = raw_val if isinstance(raw_val, list) else [raw_val]
                for val in vals:
                    norm_s = normalize_skill(val)
                    base_conf = METHOD_BASE_CONFIDENCE.get(method, 0.5)
                    if norm_s not in skills_map:
                        skills_map[norm_s] = (base_conf, [src])
                    else:
                        prev_conf, prev_srcs = skills_map[norm_s]
                        new_conf = min(prev_conf + 0.05, 1.0)
                        if src not in prev_srcs:
                            prev_srcs.append(src)
                        skills_map[norm_s] = (new_conf, prev_srcs)
                    skills_provenance.append(ProvenanceEntry(field="skills", source=src, method=method, value=norm_s))
        
        skills_list = [
            SkillEntry(name=name, confidence=conf, sources=srcs)
            for name, (conf, srcs) in skills_map.items()
        ]
        skills_conf = sum(s.confidence for s in skills_list) / len(skills_list) if skills_list else 0.0

        # Merge experience lists
        experience_list: List[Experience] = []
        experience_provenance = []
        if "experience" in combined_fields:
            # Simple group by company to avoid duplicates
            comp_map: Dict[str, Dict[str, Any]] = {}
            for raw_val, src, method in combined_fields["experience"]:
                # raw_val should be list of dicts
                if isinstance(raw_val, list):
                    for job in raw_val:
                        company = job.get("company", "Unknown").strip()
                        norm_company = company.lower()
                        # normalize dates
                        s_date = normalize_date(job.get("start_date") or "")
                        e_date = normalize_date(job.get("end_date") or "")
                        title = job.get("title")
                        desc = job.get("description")
                        
                        if norm_company not in comp_map:
                            comp_map[norm_company] = {
                                "company": company,
                                "title": title,
                                "start_date": s_date,
                                "end_date": e_date,
                                "description": desc,
                                "source": src,
                                "method": method
                            }
                        else:
                            # Merge details, prioritize values that exist
                            existing = comp_map[norm_company]
                            if not existing["title"] and title:
                                existing["title"] = title
                            if not existing["start_date"] and s_date:
                                existing["start_date"] = s_date
                            if not existing["end_date"] and e_date:
                                existing["end_date"] = e_date
                            if desc and (not existing["description"] or len(desc) > len(existing["description"])):
                                existing["description"] = desc
                                
                        experience_provenance.append(ProvenanceEntry(
                            field="experience", source=src, method=method, value=company
                        ))
            
            for key, val in comp_map.items():
                experience_list.append(Experience(
                    company=val["company"],
                    title=val["title"],
                    start_date=val["start_date"],
                    end_date=val["end_date"],
                    description=val["description"]
                ))

        # Merge education lists
        education_list: List[Education] = []
        education_provenance = []
        if "education" in combined_fields:
            inst_map: Dict[str, Dict[str, Any]] = {}
            for raw_val, src, method in combined_fields["education"]:
                if isinstance(raw_val, list):
                    for edu in raw_val:
                        inst = edu.get("institution", "Unknown").strip()
                        norm_inst = inst.lower()
                        s_date = normalize_date(edu.get("start_date") or "")
                        e_date = normalize_date(edu.get("end_date") or "")
                        deg = edu.get("degree")
                        field = edu.get("field_of_study")
                        
                        if norm_inst not in inst_map:
                            inst_map[norm_inst] = {
                                "institution": inst,
                                "degree": deg,
                                "field_of_study": field,
                                "start_date": s_date,
                                "end_date": e_date,
                                "source": src,
                                "method": method
                            }
                        else:
                            existing = inst_map[norm_inst]
                            if not existing["degree"] and deg:
                                existing["degree"] = deg
                            if not existing["field_of_study"] and field:
                                existing["field_of_study"] = field
                            if not existing["start_date"] and s_date:
                                existing["start_date"] = s_date
                            if not existing["end_date"] and e_date:
                                existing["end_date"] = e_date
                                
                        education_provenance.append(ProvenanceEntry(
                            field="education", source=src, method=method, value=inst
                        ))
                        
            for key, val in inst_map.items():
                education_list.append(Education(
                    institution=val["institution"],
                    degree=val["degree"],
                    field_of_study=val["field_of_study"],
                    start_date=val["start_date"],
                    end_date=val["end_date"]
                ))

        # Overall Confidence calculation (weighted average of filled fields)
        weights = {
            "full_name": (name_conf, 2.0),
            "emails": (emails_conf, 2.0),
            "phones": (phones_conf, 1.5),
            "location": (loc_conf, 1.0),
            "headline": (head_conf, 1.0),
            "years_experience": (years_conf, 1.0),
            "skills": (skills_conf, 1.5)
        }
        
        weighted_sum = 0.0
        weight_sum = 0.0
        for conf, w in weights.values():
            if conf > 0:
                weighted_sum += conf * w
                weight_sum += w
                
        overall_confidence = round(weighted_sum / weight_sum, 2) if weight_sum > 0 else 0.5

        # Consolidate all provenance entries
        all_provenance = []
        if name_prov: all_provenance.extend(name_prov)
        if loc_prov: all_provenance.extend(loc_prov)
        if head_prov: all_provenance.extend(head_prov)
        if years_prov: all_provenance.extend(years_prov)
        all_provenance.extend(emails_provenance)
        all_provenance.extend(phones_provenance)
        all_provenance.extend(links_provenance)
        all_provenance.extend(skills_provenance)
        all_provenance.extend(experience_provenance)
        all_provenance.extend(education_provenance)

        # Unique Candidate ID
        email_str = emails_list[0] if emails_list else "unknown"
        candidate_id = f"cand_{cand_idx}_{email_str.split('@')[0]}"

        canonical_profiles.append(CanonicalProfile(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails_list,
            phones=phones_list,
            location=location,
            links=links_list,
            headline=headline,
            years_experience=years_exp,
            skills=skills_list,
            experience=experience_list,
            education=education_list,
            provenance=all_provenance,
            overall_confidence=overall_confidence
        ))

    return canonical_profiles
