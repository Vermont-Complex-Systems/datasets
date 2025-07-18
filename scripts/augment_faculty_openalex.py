import pandas as pd
from pyalex import Authors, Institutions
from pathlib import Path
from time import sleep
import json

faculty_file = Path("../static/data/academic-research-groups.csv")
d = pd.read_csv(faculty_file)
uvm_id = 'i111236770'
d['name'] = d.payroll_name.str.split(",").map(lambda x: x[1] + ' ' + x[0])

faculty_raw_oa = {} # {'payroll_name: [hits]}
for faculty_name in d.name:
    try:
        authors = Authors().search(faculty_name).filter(
            affiliations={"institution": {"id": uvm_id}}
        ).get()
        faculty_raw_oa[faculty_name] = authors

    except Exception as e:
        print(f"Error for {faculty_name}: {e}")
        faculty_raw_oa[faculty_name] = None

    sleep(0.1)  # 100ms between requests

with open('./tmp.json', 'w') as f:
    json.dump(faculty_raw_oa, f)

##############################
#                            #
#      CHECKING MATCHES      #
#                            #
##############################

import re
from difflib import SequenceMatcher
from datetime import datetime

def normalize_name(name):
    """Clean and normalize a name for comparison"""
    # Remove common titles and suffixes
    name = re.sub(r'\b(Dr|Prof|Professor|PhD|MD|Jr|Sr|II|III|IV)\b\.?', '', name, flags=re.IGNORECASE)
    # Clean up whitespace and punctuation
    name = re.sub(r'[^\w\s]', '', name)
    return ' '.join(name.split()).strip().lower()

def extract_name_parts(name):
    """Extract first, middle, and last name parts"""
    parts = normalize_name(name).split()
    if len(parts) == 1:
        return parts[0], [], ""
    elif len(parts) == 2:
        return parts[0], [], parts[1]
    else:
        return parts[0], parts[1:-1], parts[-1]

def calculate_name_similarity(payroll_name, openalex_name):
    """Calculate similarity accounting for middle names"""
    # Basic full name similarity
    full_sim = SequenceMatcher(None, normalize_name(payroll_name), normalize_name(openalex_name)).ratio()
    
    # Parse names
    p_first, p_middle, p_last = extract_name_parts(payroll_name)
    o_first, o_middle, o_last = extract_name_parts(openalex_name)
    
    # First name similarity (most important)
    first_sim = SequenceMatcher(None, p_first, o_first).ratio()
    
    # Last name similarity (very important)
    last_sim = SequenceMatcher(None, p_last, o_last).ratio()
    
    # Middle name handling
    middle_bonus = 0
    if p_middle and o_middle:
        # Both have middle names - they should match
        middle_sim = max([SequenceMatcher(None, pm, om).ratio() for pm in p_middle for om in o_middle])
        middle_bonus = middle_sim * 0.1
    elif not p_middle and o_middle:
        # Payroll has no middle, OpenAlex does - this is expected, small bonus
        middle_bonus = 0.1
    elif p_middle and not o_middle:
        # Payroll has middle, OpenAlex doesn't - slight penalty
        middle_bonus = -0.05
    
    # Weighted combination
    combined_score = (first_sim * 0.4 + last_sim * 0.4 + full_sim * 0.2 + middle_bonus)
    
    return min(combined_score, 1.0)  # Cap at 1.0

def score_author_match(faculty_name, author_data):
    score = 0
    flags = []
    
    # 1. Improved name similarity
    author_name = author_data.get('display_name', '')
    name_sim = calculate_name_similarity(faculty_name, author_name)
    score += name_sim * 60  # 0-60 points
    
    # Lower the threshold since we're handling middle names better
    if name_sim < 0.6:  # Was 0.7
        flags.append(f'low_name_similarity_{name_sim:.2f}')
    
    # 2. Check if UVM is current/recent affiliation
    current_year = datetime.now().year
    uvm_affiliation_years = []
    
    for affiliation in author_data.get('affiliations', []):
        if affiliation.get('institution', {}).get('id') == f"https://openalex.org/{uvm_id}":
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
    
    # 3. Publication activity (basic check)
    works_count = author_data.get('works_count', 0)
    if works_count == 0:
        flags.append('no_publications')
        score -= 10
    elif works_count < 5:
        flags.append('few_publications')
    
    return score, flags

def process_matches(faculty_name, authors_list):
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
    
    # Sort by score
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    best_match, best_score, best_flags = scored_matches[0]
    
    # If top two scores are close, flag for manual review
    if len(scored_matches) > 1 and scored_matches[0][1] - scored_matches[1][1] < 10:
        best_flags.append('close_competitors')
    
    confidence = 'high' if best_score > 70 else 'medium' if best_score > 50 else 'low'
    return best_match, confidence, best_flags

processed_results = []

for faculty_name, authors in faculty_raw_oa.items():
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

# Save for manual review

df = pd.DataFrame(processed_results)
df.to_csv('faculty_openalex_matches.csv', index=False)

# Show items that need manual review
review_needed = df[df['needs_review'] == True]
print(f"{len(review_needed)} matches need manual review")


def interactive_review_with_competitors():
    review_needed = df[df['needs_review'] == True].copy()
    approved = {}
    
    for idx, row in review_needed.iterrows():
        print(f"\n--- Match {idx+1}/{len(review_needed)} ---")
        print(f"Faculty name: {row['faculty_name']}")
        
        # Get the original search results for this faculty member
        faculty_name = row['faculty_name']
        original_results = faculty_raw_oa.get(faculty_name, [])
        
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
                    recent_affs = [aff for aff in affiliations if aff.get('years') and max(aff['years']) >= 2020]
                    if recent_affs:
                        print(f"     Recent affiliations: {[aff['institution']['display_name'] for aff in recent_affs[:2]]}")
                print()
            
            print(f"★ = Current top pick: {row['openalex_name']}")
        else:
            print(f"OpenAlex name: {row['openalex_name']}")
            print(f"OpenAlex ID: {row['openalex_id']}")
        
        print(f"Confidence: {row['confidence']}")
        print(f"Flags: {row['flags']}")
        
        while True:
            if len(original_results) > 1:
                choice = input("Approve top pick? (y/n/1-9 to pick different number/s to skip/q to quit): ").lower()
                if choice in ['y', 'n', 's', 'q'] or (choice.isdigit() and 1 <= int(choice) <= len(original_results)):
                    break
            else:
                choice = input("Approve? (y/n/s for skip/q to quit): ").lower()
                if choice in ['y', 'n', 's', 'q']:
                    break
        
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

# Run the improved review
approved_matches = interactive_review_with_competitors()

##############################
#                            #
#      FINAL MATCHES      #
#                            #
##############################


# Start with high-confidence matches (auto-approved)
final_matches = {}

# Add high-confidence matches
high_confidence = df[df['confidence'] == 'high']
for _, row in high_confidence.iterrows():
    final_matches[row['faculty_name']] = row['openalex_id']

# Add your manually approved matches
final_matches.update(approved_matches)

# Add medium confidence matches that weren't flagged for review
medium_confidence = df[(df['confidence'] == 'medium') & (df['needs_review'] == False)]
for _, row in medium_confidence.iterrows():
    final_matches[row['faculty_name']] = row['openalex_id']

print(f"Total matches: {len(final_matches)}")
print(f"With OpenAlex IDs: {len([v for v in final_matches.values() if v is not None])}")

# MERRRRGEEE

# Assuming your original dataset is in 'd' DataFrame
d_with_openalex = d.copy()

# Add OpenAlex ID column
d_with_openalex['openalex_id'] = d_with_openalex['name'].map(final_matches)

# Clean up the IDs (remove the URL part if present)
# Clean up the IDs using pandas string methods (handles NaN automatically)
d_with_openalex['openalex_id'] = d_with_openalex['openalex_id'].str.replace('https://openalex.org/', '', regex=False)

# Check results
print(f"Faculty with OpenAlex IDs: {d_with_openalex['openalex_id'].notna().sum()}/{len(d_with_openalex)}")

# cleaning
d_with_openalex = d_with_openalex.drop(['name_split', 'name', 'nb_tokens'], axis=1)

# SAVING
# Save to your static/data directory
d_with_openalex.to_csv('../static/data/academic-department-with-openalex.csv', index=False)

# Also save as parquet if you were using that
d_with_openalex.to_parquet('../static/data/academic-department-with-openalex.parquet', index=False)

print("Saved augmented dataset!")

# d_with_openalex = pd.read_csv('../static/data/academic-department-with-openalex.csv')
d_with_openalex['oa_uid'] = d_with_openalex.oa_uid.str.capitalize()

def compare_existing_vs_new_openalex():
    approved = {}
    
    # Find cases where we have both existing oa_ui and new openalex_id
    conflicts = d_with_openalex[
        d_with_openalex['oa_uid'].notna() & 
        d_with_openalex['openalex_id'].notna() & 
        (d_with_openalex['oa_uid'] != d_with_openalex['openalex_id'])
    ].copy()
    
    # Auto-resolve: pick non-null values when only one exists
    auto_resolved = d_with_openalex[
        (d_with_openalex['oa_uid'].isna() & d_with_openalex['openalex_id'].notna()) |
        (d_with_openalex['oa_uid'].notna() & d_with_openalex['openalex_id'].isna())
    ].copy()
    
    for _, row in auto_resolved.iterrows():
        final_id = row['oa_uid'] if pd.notna(row['oa_uid']) else row['openalex_id']
        approved[row['payroll_name']] = final_id
        print(f"✅ Auto-picked for {row['payroll_name']}: {final_id}")
    
    # Handle conflicts manually
    if len(conflicts) > 0:
        print(f"\n🔄 Found {len(conflicts)} conflicts to resolve:")
        
        for idx, row in conflicts.iterrows():
            faculty_name = row['payroll_name']
            existing_id = row['oa_uid']
            new_id = row['openalex_id']
            
            print(f"\n--- {faculty_name} ---")
            print(f"Existing oa_uid:     https://openalex.org/authors/{existing_id}")
            print(f"New openalex_id:     https://openalex.org/authors/{new_id}")
            
            while True:
                choice = input("Choose: (o/n/s for none): ").lower()
                if choice in ['o', 'n', 's']:
                    break
            
            if choice == 'o':
                approved[faculty_name] = existing_id
            elif choice == 'n':
                approved[faculty_name] = new_id
            elif choice == 's':
                approved[faculty_name] = None
            # 's' = skip
    else:
        print("✅ No conflicts found!")
    
    print(f"\nProcessed {len(approved)} faculty members")
    return approved

# Run it
final_openalex_ids = compare_existing_vs_new_openalex()

d_final = d_with_openalex.copy()

# Apply the final decisions
for faculty_name, final_id in final_openalex_ids.items():
    mask = d_final['payroll_name'] == faculty_name
    d_final.loc[mask, 'oa_uid'] = final_id

# For any faculty not in final_openalex_ids, keep existing oa_uid or use new openalex_id
remaining_mask = ~d_final['payroll_name'].isin(final_openalex_ids.keys())
d_final.loc[remaining_mask, 'oa_uid'] = d_final.loc[remaining_mask, 'oa_uid'].fillna(
    d_final.loc[remaining_mask, 'openalex_id']
)

# Clean up - remove the temporary openalex_id column and other review columns
columns_to_drop = ['openalex_id', 'openalex_name', 'confidence', 'flags', 'needs_review']
existing_cols_to_drop = [col for col in columns_to_drop if col in d_final.columns]
d_final = d_final.drop(columns=existing_cols_to_drop)

# Check results
print(f"Faculty with OpenAlex IDs: {d_final['oa_uid'].notna().sum()}/{len(d_final)}")
print(f"Match rate: {(d_final['oa_uid'].notna().sum() / len(d_final) * 100):.1f}%")

#################################
#
# STILL a few more to be done!
#
##################################

def manual_openalex_lookup():
    # Find faculty with missing OpenAlex IDs
    missing_oa = d_final[d_final['oa_uid'].isna()].copy()
    manual_matches = {}
    
    print(f"Found {len(missing_oa)} faculty members without OpenAlex IDs")
    print("You can search for them manually at: https://openalex.org/")
    print("Enter the OpenAlex ID (just the part after openalex.org/) or 'n' for no match\n")
    
    for idx, (_, row) in enumerate(missing_oa.iterrows()):
        faculty_name = row['payroll_name']
        
        print(f"\n--- {idx+1}/{len(missing_oa)} ---")
        print(f"Faculty: {faculty_name}")
        
        # Show any other info that might help with search
        if 'department' in row and pd.notna(row['department']):
            print(f"Department: {row['department']}")
        if 'title' in row and pd.notna(row['title']):
            print(f"Title: {row['title']}")
        
        print(f"Search URL: https://openalex.org/authors?search={faculty_name.replace(' ', '%20')}")
        
        while True:
            user_input = input("OpenAlex ID (A1234567890/n for none/s to skip/q to quit): ").strip()
            
            if user_input.lower() == 'q':
                print("Quitting...")
                return manual_matches
            elif user_input.lower() == 's':
                break  # Skip this one
            elif user_input.lower() == 'n':
                manual_matches[faculty_name] = None
                print(f"Marked {faculty_name} as no match")
                break
            elif user_input.startswith('A') and len(user_input) == 11:
                manual_matches[faculty_name] = user_input
                print(f"Added {faculty_name} -> {user_input}")
                break
            elif user_input.startswith('https://openalex.org/'):
                # Extract ID from full URL
                oa_id = user_input.split('/')[-1]
                if oa_id.startswith('A') and len(oa_id) == 11:
                    manual_matches[faculty_name] = oa_id
                    print(f"Added {faculty_name} -> {oa_id}")
                    break
                else:
                    print("Invalid OpenAlex ID format")
            else:
                print("Please enter a valid OpenAlex ID (A1234567890) or 'n' for no match")
    
    print(f"\nManually processed {len(manual_matches)} faculty members")
    return manual_matches

# Do, Hung: A5030492411
# Jan fook : A5030492411
# Alex Garlick: A5045120152
# Steven Gove: A5030492411

# Run manual lookup
manual_openalex_ids = manual_openalex_lookup()

# Apply the manual matches
d_final_manual = d_final.copy()
for faculty_name, oa_id in manual_openalex_ids.items():
    mask = d_final_manual['payroll_name'] == faculty_name
    d_final_manual.loc[mask, 'oa_uid'] = oa_id

# Check final results
total_with_ids = d_final_manual['oa_uid'].notna().sum()
print(f"\nFinal results: {total_with_ids}/{len(d_final_manual)} faculty have OpenAlex IDs")
print(f"Final match rate: {(total_with_ids / len(d_final_manual) * 100):.1f}%")

# Save final dataset
d_final_manual.to_csv('../static/data/academic-research-groups.csv', index=False)
d_final_manual.to_parquet('../static/data/academic-research-groups.parquet', index=False)
