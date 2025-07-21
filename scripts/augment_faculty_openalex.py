"""
OpenAlex Faculty ID Matching Script

This script matches faculty members from a CSV file with their OpenAlex author IDs.
It performs automated matching, manual review of uncertain matches, and handles
conflicts between existing and new IDs.

Author: Your Name
Date: 2025
"""

import pandas as pd
import json
import re
from pathlib import Path
from time import sleep
from difflib import SequenceMatcher
from datetime import datetime
from pyalex import Authors, Institutions

# =============================================================================
# CONFIGURATION
# =============================================================================

FACULTY_FILE = Path("../static/data/academic-research-groups.csv")
UVM_INSTITUTION_ID = 'i111236770'  # University of Vermont OpenAlex ID
OUTPUT_DIR = Path("../static/data/")
CACHE_FILE = Path("./faculty_openalex_cache.json")

# =============================================================================
# STEP 1: LOAD DATA AND SEARCH OPENALEX
# =============================================================================

def load_and_prepare_faculty_data():
    """Load faculty data and prepare names for matching."""
    print("Loading faculty data...")
    d = pd.read_csv(FACULTY_FILE)
    
    # Convert "Last, First" format to "First Last"
    d['search_name'] = d.payroll_name.str.split(",").map(
        lambda x: f"{x[1].strip()} {x[0].strip()}" if len(x) == 2 else x[0]
    )
    
    print(f"Loaded {len(d)} faculty members")
    return d

def search_openalex_for_faculty(faculty_df, use_cache=True):
    """Search OpenAlex for each faculty member."""
    
    # Try to load from cache first
    if use_cache and CACHE_FILE.exists():
        print(f"Loading cached results from {CACHE_FILE}")
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    
    print("Searching OpenAlex API for faculty matches...")
    faculty_raw_oa = {}
    
    for i, faculty_name in enumerate(faculty_df.search_name):
        print(f"Searching {i+1}/{len(faculty_df)}: {faculty_name}")
        
        try:
            authors = Authors().search(faculty_name).filter(
                affiliations={"institution": {"id": UVM_INSTITUTION_ID}}
            ).get()
            faculty_raw_oa[faculty_name] = authors
            
        except Exception as e:
            print(f"Error for {faculty_name}: {e}")
            faculty_raw_oa[faculty_name] = None
        
        sleep(0.1)  # Be nice to the API
    
    # Cache the results
    print(f"Saving results to cache: {CACHE_FILE}")
    with open(CACHE_FILE, 'w') as f:
        json.dump(faculty_raw_oa, f, indent=2)
    
    return faculty_raw_oa

# =============================================================================
# STEP 2: NAME MATCHING AND SCORING
# =============================================================================

def normalize_name(name):
    """Clean and normalize a name for comparison."""
    # Remove common titles and suffixes
    name = re.sub(r'\b(Dr|Prof|Professor|PhD|MD|Jr|Sr|II|III|IV)\b\.?', '', name, flags=re.IGNORECASE)
    # Clean up whitespace and punctuation
    name = re.sub(r'[^\w\s]', '', name)
    return ' '.join(name.split()).strip().lower()

def extract_name_parts(name):
    """Extract first, middle, and last name parts."""
    parts = normalize_name(name).split()
    if len(parts) == 1:
        return parts[0], [], ""
    elif len(parts) == 2:
        return parts[0], [], parts[1]
    else:
        return parts[0], parts[1:-1], parts[-1]

def calculate_name_similarity(payroll_name, openalex_name):
    """Calculate name similarity accounting for middle names."""
    # Basic full name similarity
    full_sim = SequenceMatcher(None, normalize_name(payroll_name), normalize_name(openalex_name)).ratio()
    
    # Parse names
    p_first, p_middle, p_last = extract_name_parts(payroll_name)
    o_first, o_middle, o_last = extract_name_parts(openalex_name)
    
    # Calculate component similarities
    first_sim = SequenceMatcher(None, p_first, o_first).ratio()
    last_sim = SequenceMatcher(None, p_last, o_last).ratio()
    
    # Handle middle names
    middle_bonus = 0
    if p_middle and o_middle:
        # Both have middle names - they should match
        middle_sim = max([SequenceMatcher(None, pm, om).ratio() for pm in p_middle for om in o_middle])
        middle_bonus = middle_sim * 0.1
    elif not p_middle and o_middle:
        # Payroll has no middle, OpenAlex does - this is expected
        middle_bonus = 0.1
    elif p_middle and not o_middle:
        # Payroll has middle, OpenAlex doesn't - slight penalty
        middle_bonus = -0.05
    
    # Weighted combination: first and last names are most important
    combined_score = (first_sim * 0.4 + last_sim * 0.4 + full_sim * 0.2 + middle_bonus)
    return min(combined_score, 1.0)  # Cap at 1.0

def score_author_match(faculty_name, author_data):
    """Score how well an OpenAlex author matches a faculty member."""
    score = 0
    flags = []
    
    # 1. Name similarity (0-60 points)
    author_name = author_data.get('display_name', '')
    name_sim = calculate_name_similarity(faculty_name, author_name)
    score += name_sim * 60
    
    if name_sim < 0.6:
        flags.append(f'low_name_similarity_{name_sim:.2f}')
    
    # 2. Affiliation recency (0-30 points)
    current_year = datetime.now().year
    uvm_affiliation_years = []
    
    for affiliation in author_data.get('affiliations', []):
        if affiliation.get('institution', {}).get('id') == f"https://openalex.org/{UVM_INSTITUTION_ID}":
            years = affiliation.get('years', [])
            uvm_affiliation_years.extend(years)
    
    if uvm_affiliation_years:
        most_recent = max(uvm_affiliation_years)
        if current_year - most_recent <= 2:
            score += 30  # Current/recent affiliation
        elif current_year - most_recent <= 5:
            score += 20  # Recent affiliation
        else:
            score += 10  # Older affiliation
            flags.append('old_affiliation')
    
    # 3. Publication activity
    works_count = author_data.get('works_count', 0)
    if works_count == 0:
        flags.append('no_publications')
        score -= 10
    elif works_count < 5:
        flags.append('few_publications')
    
    return score, flags

def process_matches(faculty_name, authors_list):
    """Process all potential matches for a faculty member."""
    if not authors_list:
        return None, 'no_matches', []
    
    if len(authors_list) == 1:
        score, flags = score_author_match(faculty_name, authors_list[0])
        confidence = 'high' if score > 70 else 'medium' if score > 50 else 'low'
        return authors_list[0], confidence, flags
    
    # Multiple matches - score them all
    scored_matches = []
    for author in authors_list:
        score, flags = score_author_match(faculty_name, author)
        scored_matches.append((author, score, flags))
    
    # Sort by score (best first)
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    best_match, best_score, best_flags = scored_matches[0]
    
    # Flag if top two scores are close
    if len(scored_matches) > 1 and scored_matches[0][1] - scored_matches[1][1] < 10:
        best_flags.append('close_competitors')
    
    confidence = 'high' if best_score > 70 else 'medium' if best_score > 50 else 'low'
    return best_match, confidence, best_flags

# =============================================================================
# STEP 3: INTERACTIVE REVIEW
# =============================================================================

def interactive_review_uncertain_matches(matches_df, raw_search_results):
    """Manually review uncertain matches."""
    review_needed = matches_df[matches_df['needs_review'] == True].copy()
    approved = {}
    
    print(f"\nReviewing {len(review_needed)} uncertain matches...")
    
    for idx, row in review_needed.iterrows():
        faculty_name = row['faculty_name']
        original_results = raw_search_results.get(faculty_name, [])
        
        print(f"\n--- Match {idx+1}/{len(review_needed)} ---")
        print(f"Faculty name: {faculty_name}")
        
        if original_results and len(original_results) > 1:
            print(f"\nFound {len(original_results)} candidates:")
            for i, candidate in enumerate(original_results):
                marker = "★" if candidate['id'] == row['openalex_id'] else " "
                print(f"  {marker} {i+1}. {candidate.get('display_name', 'N/A')}")
                print(f"     ID: {candidate['id']}")
                print(f"     Works: {candidate.get('works_count', 0)}")
                
                # Show recent affiliations
                affiliations = candidate.get('affiliations', [])
                if affiliations:
                    recent_affs = [aff for aff in affiliations 
                                 if aff.get('years') and max(aff['years']) >= 2020]
                    if recent_affs:
                        inst_names = [aff['institution']['display_name'] for aff in recent_affs[:2]]
                        print(f"     Recent affiliations: {inst_names}")
                print()
            
            print(f"★ = Current top pick: {row['openalex_name']}")
        else:
            print(f"OpenAlex name: {row['openalex_name']}")
            print(f"OpenAlex ID: {row['openalex_id']}")
        
        print(f"Confidence: {row['confidence']}")
        print(f"Flags: {row['flags']}")
        
        # Get user choice
        while True:
            if len(original_results) > 1:
                choice = input("Choice: (y)es/(n)o/(1-9) pick number/(s)kip/(q)uit: ").lower()
                valid_nums = [str(i) for i in range(1, len(original_results) + 1)]
                if choice in ['y', 'n', 's', 'q'] + valid_nums:
                    break
            else:
                choice = input("Choice: (y)es/(n)o/(s)kip/(q)uit: ").lower()
                if choice in ['y', 'n', 's', 'q']:
                    break
        
        # Process choice
        if choice == 'q':
            break
        elif choice == 'y':
            approved[faculty_name] = row['openalex_id']
        elif choice == 'n':
            approved[faculty_name] = None
        elif choice.isdigit():
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(original_results):
                approved[faculty_name] = original_results[selected_idx]['id']
        # 's' = skip for now
    
    return approved

def resolve_id_conflicts(df_with_ids):
    """Handle conflicts between existing oa_uid and new openalex_id."""
    approved = {}
    
    # Auto-resolve: pick non-null values when only one exists
    auto_resolved = df_with_ids[
        (df_with_ids['oa_uid'].isna() & df_with_ids['openalex_id'].notna()) |
        (df_with_ids['oa_uid'].notna() & df_with_ids['openalex_id'].isna())
    ].copy()
    
    for _, row in auto_resolved.iterrows():
        final_id = row['oa_uid'] if pd.notna(row['oa_uid']) else row['openalex_id']
        approved[row['payroll_name']] = final_id
        print(f"✅ Auto-resolved {row['payroll_name']}: {final_id}")
    
    # Handle conflicts manually
    conflicts = df_with_ids[
        df_with_ids['oa_uid'].notna() & 
        df_with_ids['openalex_id'].notna() & 
        (df_with_ids['oa_uid'] != df_with_ids['openalex_id'])
    ].copy()
    
    if len(conflicts) > 0:
        print(f"\n🔄 Found {len(conflicts)} conflicts to resolve:")
        
        for _, row in conflicts.iterrows():
            faculty_name = row['payroll_name']
            existing_id = row['oa_uid']
            new_id = row['openalex_id']
            
            print(f"\n--- {faculty_name} ---")
            print(f"Existing: https://openalex.org/authors/{existing_id}")
            print(f"New:      https://openalex.org/authors/{new_id}")
            
            while True:
                choice = input("Choose: (o)ld/(n)ew/(s)kip: ").lower()
                if choice in ['o', 'n', 's']:
                    break
            
            if choice == 'o':
                approved[faculty_name] = existing_id
            elif choice == 'n':
                approved[faculty_name] = new_id
            # 's' = skip
    else:
        print("✅ No conflicts found!")
    
    return approved

def manual_openalex_lookup(df_final):
    """Manual lookup for remaining unmatched faculty."""
    missing_oa = df_final[df_final['oa_uid'].isna()].copy()
    manual_matches = {}
    
    if len(missing_oa) == 0:
        print("✅ All faculty have OpenAlex IDs!")
        return manual_matches
    
    print(f"\nManual lookup for {len(missing_oa)} remaining faculty")
    print("Search at: https://openalex.org/authors")
    
    for idx, (_, row) in enumerate(missing_oa.iterrows()):
        faculty_name = row['payroll_name']
        
        print(f"\n--- {idx+1}/{len(missing_oa)} ---")
        print(f"Faculty: {faculty_name}")
        
        # Show helpful context
        if 'department' in row and pd.notna(row['department']):
            print(f"Department: {row['department']}")
        
        search_name = faculty_name.replace(' ', '%20')
        print(f"Search URL: https://openalex.org/authors?search={search_name}")
        
        while True:
            user_input = input("OpenAlex ID (A1234567890) or (n)one/(s)kip/(q)uit: ").strip()
            
            if user_input.lower() == 'q':
                return manual_matches
            elif user_input.lower() == 's':
                break
            elif user_input.lower() == 'n':
                manual_matches[faculty_name] = None
                print(f"Marked {faculty_name} as no match")
                break
            elif user_input.startswith('A') and len(user_input) == 11:
                manual_matches[faculty_name] = user_input
                print(f"Added {faculty_name} -> {user_input}")
                break
            elif user_input.startswith('https://openalex.org/'):
                oa_id = user_input.split('/')[-1]
                if oa_id.startswith('A') and len(oa_id) == 11:
                    manual_matches[faculty_name] = oa_id
                    print(f"Added {faculty_name} -> {oa_id}")
                    break
                else:
                    print("Invalid ID format")
            else:
                print("Enter valid OpenAlex ID (A1234567890) or n/s/q")
    
    return manual_matches

# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def main():
    """Main workflow for OpenAlex ID matching."""
    
    print("🔍 OpenAlex Faculty ID Matching Script")
    print("=" * 50)
    
    # Step 1: Load data and search OpenAlex
    faculty_df = load_and_prepare_faculty_data()
    raw_search_results = search_openalex_for_faculty(faculty_df, use_cache=True)
    
    # Step 2: Process and score matches
    print("\n📊 Processing matches...")
    processed_results = []
    
    for faculty_name, authors in raw_search_results.items():
        best_match, confidence, flags = process_matches(faculty_name, authors)
        
        result = {
            'faculty_name': faculty_name,
            'openalex_id': best_match['id'] if best_match else None,
            'openalex_name': best_match['display_name'] if best_match else None,
            'confidence': confidence,
            'flags': flags,
            'needs_review': confidence == 'low' or 'close_competitors' in flags
        }
        processed_results.append(result)
    
    matches_df = pd.DataFrame(processed_results)
    review_count = matches_df['needs_review'].sum()
    print(f"Found {len(matches_df)} total matches, {review_count} need manual review")
    
    # Step 3: Interactive review of uncertain matches
    if review_count > 0:
        approved_matches = interactive_review_uncertain_matches(matches_df, raw_search_results)
    else:
        approved_matches = {}
    
    # Step 4: Combine all matches
    print("\n🔗 Combining matches...")
    final_matches = {}
    
    # Add high-confidence auto-approved matches
    high_confidence = matches_df[matches_df['confidence'] == 'high']
    for _, row in high_confidence.iterrows():
        final_matches[row['faculty_name']] = row['openalex_id']
    
    # Add manually approved matches
    final_matches.update(approved_matches)
    
    # Add medium confidence matches that weren't flagged
    medium_confidence = matches_df[
        (matches_df['confidence'] == 'medium') & 
        (matches_df['needs_review'] == False)
    ]
    for _, row in medium_confidence.iterrows():
        final_matches[row['faculty_name']] = row['openalex_id']
    
    # Step 5: Merge with original data
    df_with_openalex = faculty_df.copy()
    df_with_openalex['openalex_id'] = df_with_openalex['search_name'].map(final_matches)
    
    # Clean up OpenAlex IDs (remove URL prefix)
    df_with_openalex['openalex_id'] = df_with_openalex['openalex_id'].str.replace(
        'https://openalex.org/', '', regex=False
    )
    
    # Step 6: Handle conflicts with existing oa_uid
    if 'oa_uid' in df_with_openalex.columns:
        df_with_openalex['oa_uid'] = df_with_openalex['oa_uid'].str.capitalize()
        conflict_resolutions = resolve_id_conflicts(df_with_openalex)
        
        # Apply conflict resolutions
        for faculty_name, final_id in conflict_resolutions.items():
            mask = df_with_openalex['payroll_name'] == faculty_name
            df_with_openalex.loc[mask, 'oa_uid'] = final_id
        
        # Fill remaining gaps
        remaining_mask = ~df_with_openalex['payroll_name'].isin(conflict_resolutions.keys())
        df_with_openalex.loc[remaining_mask, 'oa_uid'] = df_with_openalex.loc[remaining_mask, 'oa_uid'].fillna(
            df_with_openalex.loc[remaining_mask, 'openalex_id']
        )
    else:
        # No existing oa_uid column, create it
        df_with_openalex['oa_uid'] = df_with_openalex['openalex_id']
    
    # Step 7: Manual lookup for remaining unmatched
    df_final = df_with_openalex.copy()
    manual_matches = manual_openalex_lookup(df_final)
    
    # Apply manual matches
    for faculty_name, oa_id in manual_matches.items():
        mask = df_final['payroll_name'] == faculty_name
        df_final.loc[mask, 'oa_uid'] = oa_id
    
    # Step 8: Clean up and save
    print("\n💾 Saving results...")
    
    # Remove temporary columns
    temp_columns = ['search_name', 'openalex_id']
    df_final = df_final.drop(columns=[col for col in temp_columns if col in df_final.columns])
    
    # Save final dataset
    output_csv = OUTPUT_DIR / "academic-research-groups.csv"
    output_parquet = OUTPUT_DIR / "academic-research-groups.parquet"
    
    df_final.to_csv(output_csv, index=False)
    df_final.to_parquet(output_parquet, index=False)
    
    # Final statistics
    total_with_ids = df_final['oa_uid'].notna().sum()
    match_rate = (total_with_ids / len(df_final)) * 100
    
    print(f"\n✅ Final Results:")
    print(f"   Total faculty: {len(df_final)}")
    print(f"   With OpenAlex IDs: {total_with_ids}")
    print(f"   Match rate: {match_rate:.1f}%")
    print(f"   Saved to: {output_csv}")
    
    return df_final

if __name__ == "__main__":
    result_df = main()