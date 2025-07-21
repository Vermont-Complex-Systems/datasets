import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_publication_gaps(papers_df, faculty_df):
    """
    Analyze publication gaps to identify false positive early publications
    
    Args:
        papers_df: DataFrame with all papers (your format)
        faculty_df: DataFrame with faculty info including current first_pub_year
    
    Returns:
        DataFrame with gap analysis and cleaning recommendations
    """
    
    results = []
    
    for _, faculty in faculty_df.iterrows():
        ego_aid = faculty['oa_uid']
        name = faculty['payroll_name']
        current_first_year = faculty.get('first_pub_year')
        
        # Get all papers for this faculty member
        faculty_papers = papers_df[papers_df['ego_aid'] == ego_aid].copy()
        
        if len(faculty_papers) == 0:
            results.append({
                'ego_aid': ego_aid,
                'name': name,
                'current_first_year': current_first_year,
                'paper_count': 0,
                'recommendation': 'no_papers_found',
                'confidence': 0.0,
                'suggested_first_year': None,
                'max_gap': None,
                'gap_location': None
            })
            continue
        
        # Sort papers by year
        faculty_papers = faculty_papers.sort_values('pub_year')
        pub_years = faculty_papers['pub_year'].dropna().astype(int)
        
        if len(pub_years) < 2:
            results.append({
                'ego_aid': ego_aid,
                'name': name,
                'current_first_year': current_first_year,
                'paper_count': len(faculty_papers),
                'recommendation': 'insufficient_data',
                'confidence': 0.0,
                'suggested_first_year': pub_years.iloc[0] if len(pub_years) > 0 else None,
                'max_gap': None,
                'gap_location': None
            })
            continue
        
        # Calculate gaps between consecutive publication years
        gaps = []
        for i in range(len(pub_years) - 1):
            gap = pub_years.iloc[i+1] - pub_years.iloc[i]
            gaps.append({
                'start_year': pub_years.iloc[i],
                'end_year': pub_years.iloc[i+1],
                'gap_size': gap,
                'gap_index': i
            })
        
        max_gap = max(gaps, key=lambda x: x['gap_size']) if gaps else None
        
        # Analysis logic
        analysis = analyze_faculty_timeline(pub_years, gaps, faculty)
        
        results.append({
            'ego_aid': ego_aid,
            'name': name,
            'current_first_year': current_first_year,
            'paper_count': len(faculty_papers),
            'actual_first_year': pub_years.iloc[0],
            'actual_last_year': pub_years.iloc[-1],
            'span_years': pub_years.iloc[-1] - pub_years.iloc[0],
            'max_gap': max_gap['gap_size'] if max_gap else 0,
            'gap_location': f"{max_gap['start_year']}-{max_gap['end_year']}" if max_gap else None,
            **analysis
        })
    
    return pd.DataFrame(results)

def analyze_faculty_timeline(pub_years, gaps, faculty_info):
    """
    Analyze a single faculty member's publication timeline
    """
    
    max_gap = max(gaps, key=lambda x: x['gap_size']) if gaps else None
    current_year = datetime.now().year
    payroll_year = faculty_info.get('payroll_year', current_year)
    
    # Rule 1: Large gap at the beginning suggests false positive early papers
    if max_gap and max_gap['gap_size'] >= 15:
        gap_position = max_gap['gap_index'] / (len(pub_years) - 1)  # Position as fraction
        
        if gap_position < 0.3:  # Gap in first 30% of career
            return {
                'recommendation': 'likely_false_positive_early',
                'confidence': 0.8,
                'suggested_first_year': max_gap['end_year'],
                'reasoning': f"Large {max_gap['gap_size']}-year gap early in career"
            }
    
    # Rule 2: Multiple large gaps suggest data quality issues
    large_gaps = [g for g in gaps if g['gap_size'] >= 10]
    if len(large_gaps) >= 2:
        return {
            'recommendation': 'multiple_large_gaps',
            'confidence': 0.6,
            'suggested_first_year': None,
            'reasoning': f"Multiple gaps ≥10 years: {len(large_gaps)} gaps"
        }
    
    # Rule 3: Very early publication compared to career stage
    if len(pub_years) > 0:
        career_span = payroll_year - pub_years.iloc[0]
        if career_span > 40:  # More than 40 years since first publication
            return {
                'recommendation': 'suspiciously_long_career',
                'confidence': 0.7,
                'suggested_first_year': None,
                'reasoning': f"Career span of {career_span} years seems excessive"
            }
    
    # Rule 4: Single very early outlier
    if len(pub_years) >= 3:
        early_gap = pub_years.iloc[1] - pub_years.iloc[0]
        later_gaps = [pub_years.iloc[i+1] - pub_years.iloc[i] for i in range(1, len(pub_years)-1)]
        median_gap = np.median(later_gaps) if later_gaps else 1
        
        if early_gap >= 15 and early_gap > 5 * median_gap:
            return {
                'recommendation': 'isolated_early_outlier',
                'confidence': 0.9,
                'suggested_first_year': pub_years.iloc[1],
                'reasoning': f"First paper {early_gap} years before rest, {early_gap/median_gap:.1f}x median gap"
            }
    
    # Rule 5: Papers appear reasonable
    return {
        'recommendation': 'appears_reasonable',
        'confidence': 0.8,
        'suggested_first_year': pub_years.iloc[0],
        'reasoning': "No suspicious gaps detected"
    }

def create_cleaning_recommendations(analysis_df, min_confidence=0.6):
    """
    Create final cleaning recommendations based on analysis
    """
    
    df = analysis_df.copy()
    
    # Create cleaning decision
    def make_cleaning_decision(row):
        if row['confidence'] >= min_confidence:
            if row['recommendation'] in ['likely_false_positive_early', 'isolated_early_outlier']:
                return 'clean_to_suggested', row['suggested_first_year']
            elif row['recommendation'] in ['suspiciously_long_career', 'multiple_large_gaps']:
                return 'flag_for_manual_review', None
            else:
                return 'keep_original', row['current_first_year']
        else:
            return 'keep_original', row['current_first_year']
    
    cleaning_decisions = df.apply(make_cleaning_decision, axis=1)
    df['cleaning_action'] = [d[0] for d in cleaning_decisions]
    df['final_suggested_year'] = [d[1] for d in cleaning_decisions]
    
    return df

def visualize_cleaning_results(analysis_df, papers_df, sample_faculty=None):
    """
    Create visualizations to help understand the cleaning results
    """
    
    if sample_faculty:
        # Plot timeline for specific faculty members
        fig, axes = plt.subplots(len(sample_faculty), 1, figsize=(12, 3*len(sample_faculty)))
        if len(sample_faculty) == 1:
            axes = [axes]
        
        for i, ego_aid in enumerate(sample_faculty):
            faculty_papers = papers_df[papers_df['ego_aid'] == ego_aid]
            faculty_info = analysis_df[analysis_df['ego_aid'] == ego_aid].iloc[0]
            
            if len(faculty_papers) > 0:
                pub_years = faculty_papers['pub_year'].dropna().astype(int)
                paper_counts = pub_years.value_counts().sort_index()
                
                axes[i].bar(paper_counts.index, paper_counts.values, alpha=0.7)
                axes[i].axvline(faculty_info['current_first_year'], color='red', linestyle='--', 
                              label=f"Current first year: {faculty_info['current_first_year']}")
                if faculty_info['final_suggested_year']:
                    axes[i].axvline(faculty_info['final_suggested_year'], color='green', linestyle='--', 
                                  label=f"Suggested first year: {faculty_info['final_suggested_year']}")
                
                axes[i].set_title(f"{faculty_info['name']} - {faculty_info['recommendation']}")
                axes[i].set_xlabel('Publication Year')
                axes[i].set_ylabel('Number of Papers')
                axes[i].legend()
        
        plt.tight_layout()
        plt.show()
    
    # Summary statistics
    print("=== CLEANING ANALYSIS SUMMARY ===")
    print(f"Total faculty analyzed: {len(analysis_df)}")
    print(f"Recommendations distribution:")
    print(analysis_df['recommendation'].value_counts())
    print(f"\nCleaning actions:")
    print(analysis_df['cleaning_action'].value_counts())
    
    # Show high-confidence cases for review
    high_confidence = analysis_df[analysis_df['confidence'] >= 0.8]
    print(f"\nHigh-confidence recommendations ({len(high_confidence)} cases):")
    for _, row in high_confidence.iterrows():
        print(f"  {row['name']}: {row['recommendation']} (confidence: {row['confidence']:.2f})")
        if row['max_gap']:
            print(f"    Max gap: {row['max_gap']} years at {row['gap_location']}")

def apply_cleaning_to_faculty_data(faculty_df, analysis_df):
    """
    Apply the cleaning recommendations to the original faculty dataframe
    """
    
    df_clean = faculty_df.copy()
    
    # Add analysis results
    df_clean = df_clean.merge(
        analysis_df[['ego_aid', 'recommendation', 'confidence', 'final_suggested_year', 
                    'cleaning_action', 'max_gap', 'reasoning']], 
        left_on='oa_uid', 
        right_on='ego_aid', 
        how='left'
    )
    
    # Create cleaned first_pub_year column
    df_clean['first_pub_year_original'] = df_clean['first_pub_year']
    df_clean['first_pub_year_cleaned'] = df_clean.apply(
        lambda row: row['final_suggested_year'] if row['cleaning_action'] == 'clean_to_suggested' 
                   else row['first_pub_year'], axis=1
    )
    
    return df_clean

# Example usage
def run_complete_cleaning_pipeline(papers_df, faculty_df):
    """
    Run the complete cleaning pipeline
    """
    
    print("Step 1: Analyzing publication gaps...")
    analysis_df = analyze_publication_gaps(papers_df, faculty_df)
    
    print("Step 2: Creating cleaning recommendations...")
    analysis_df = create_cleaning_recommendations(analysis_df, min_confidence=0.6)
    
    print("Step 3: Visualizing results...")
    visualize_cleaning_results(analysis_df, papers_df)
    
    print("Step 4: Applying cleaning to faculty data...")
    faculty_cleaned = apply_cleaning_to_faculty_data(faculty_df, analysis_df)
    
    return faculty_cleaned, analysis_df

# Example usage:
faculty_df = pd.read_csv("../static/data/academic-research-groups.csv")

paper_file = "../../complex-stories/src/lib/stories/open-academic-analytics/data/raw/paper.parquet"
papers_df = pd.read_parquet(paper_file)

oa_uid2first_year={row.oa_uid:row.first_pub_year for (i,row) in faculty_df[['oa_uid', 'first_pub_year']].iterrows()}

out = []
# for all papers, check if we have faculty_first_year. 
for i, row in papers_df.iterrows():
    faculty_first_year = oa_uid2first_year.get(row.ego_aid)

    # If we do, filter out any paper before that.
    if faculty_first_year is not None:
        if row.pub_year < faculty_first_year:
            continue

    out.append(row)

papers_df = pd.DataFrame(out) 

# papers_df.to_parquet("../../complex-stories/static/data/open-academic-analytics/paper.parquet")

faculty_cleaned, analysis_results = run_complete_cleaning_pipeline(papers_df, faculty_df)

# Review cases flagged for manual review
manual_review = analysis_results[analysis_results['cleaning_action'] == 'flag_for_manual_review']

print("Cases requiring manual review:")
print(manual_review[['name', 'recommendation', 'reasoning', 'max_gap']])


# =============================================================================
# STEP 2: INTERACTIVE REVIEW
# =============================================================================



def interactive_review_pub_years(analysis_df, papers_df, faculty_df):
    """
    Interactive review of flagged publication years
    
    Args:
        analysis_df: Results from gap analysis with recommendations
        papers_df: All papers data
        faculty_df: Original faculty data
        
    Returns:
        dict: Manual corrections {ego_aid: corrected_first_pub_year}
    """
    
    # Get cases that need review
    review_needed = analysis_df[
        (analysis_df['recommendation'] != 'appears_reasonable') & 
        (analysis_df['confidence'] >= 0.5)
    ].copy()
    
    print(f"\nReviewing {len(review_needed)} flagged publication years...")
    print("Commands: (k)eep current, (s)uggested, (c)ustom year, (skip), (q)uit")
    
    corrections = {}
    
    for i, (idx, row) in enumerate(review_needed.iterrows()):
        ego_aid = row['ego_aid']
        name = row['name']
        
        # Get faculty papers for context
        faculty_papers = papers_df[papers_df['ego_aid'] == ego_aid].copy()
        
        print(f"\n--- Review {i+1}/{len(review_needed)} ---")
        print(f"Faculty: {name}")
        print(f"Current first pub year: {row['current_first_year']}")
        print(f"Issue: {row['recommendation']} (confidence: {row['confidence']:.2f})")
        print(f"Reasoning: {row['reasoning']}")
        
        if row['suggested_first_year']:
            print(f"Suggested correction: {row['suggested_first_year']}")
        
        if row['max_gap']:
            print(f"Max gap: {row['max_gap']} years at {row['gap_location']}")
        
        # Show publication timeline
        if len(faculty_papers) > 0:
            pub_years = faculty_papers['pub_year'].dropna().astype(int).sort_values()
            year_counts = pub_years.value_counts().sort_index()
            
            print(f"\nPublication timeline ({len(faculty_papers)} total papers):")
            
            # Show year-by-year breakdown for first 10 years
            first_years = year_counts.head(10)
            for year, count in first_years.items():
                marker = "★" if year == row['current_first_year'] else " "
                suggested_marker = "→" if year == row['suggested_first_year'] else " "
                print(f"  {marker}{suggested_marker} {year}: {count} papers")
            
            if len(year_counts) > 10:
                print(f"  ... and {len(year_counts) - 10} more years")
                print(f"  Last year: {year_counts.index[-1]} ({year_counts.iloc[-1]} papers)")
            
            # Show sample paper titles from different periods
            early_papers = faculty_papers[faculty_papers['pub_year'] == row['current_first_year']]
            if len(early_papers) > 0:
                print(f"\nSample early papers ({row['current_first_year']}):")
                for _, paper in early_papers.head(2).iterrows():
                    title = paper['title'][:80] + "..." if len(str(paper['title'])) > 80 else paper['title']
                    print(f"  • {title}")
                    print(f"    Authors: {paper['authors'][:100]}...")
            
            if row['suggested_first_year'] and row['suggested_first_year'] != row['current_first_year']:
                suggested_papers = faculty_papers[faculty_papers['pub_year'] == row['suggested_first_year']]
                if len(suggested_papers) > 0:
                    print(f"\nSample papers from suggested year ({row['suggested_first_year']}):")
                    for _, paper in suggested_papers.head(2).iterrows():
                        title = paper['title'][:80] + "..." if len(str(paper['title'])) > 80 else paper['title']
                        print(f"  • {title}")
                        print(f"    Authors: {paper['authors'][:100]}...")
        
        # Get user choice
        while True:
            choice = input("\nChoice: (k)eep/(s)uggested/(c)ustom year/(skip)/(q)uit: ").lower().strip()
            
            if choice in ['k', 'keep']:
                corrections[ego_aid] = row['current_first_year']
                print(f"✓ Keeping current year: {row['current_first_year']}")
                break
                
            elif choice in ['s', 'suggested'] and row['suggested_first_year']:
                corrections[ego_aid] = row['suggested_first_year']
                print(f"✓ Using suggested year: {row['suggested_first_year']}")
                break
                
            elif choice in ['c', 'custom']:
                try:
                    custom_year = int(input("Enter custom year: "))
                    if 1900 <= custom_year <= datetime.now().year:
                        corrections[ego_aid] = custom_year
                        print(f"✓ Using custom year: {custom_year}")
                        break
                    else:
                        print("Please enter a reasonable year (1900-2025)")
                except ValueError:
                    print("Please enter a valid year")
                    
            elif choice in ['skip', '']:
                print("⏭ Skipping for now")
                break
                
            elif choice in ['q', 'quit']:
                print("Exiting review...")
                return corrections
                
            else:
                print("Invalid choice. Use: k/s/c/skip/q")
    
    return corrections

def apply_manual_corrections(faculty_df, corrections):
    """
    Apply manual corrections to the faculty dataframe
    
    Args:
        faculty_df: Original faculty dataframe
        corrections: Dict of {ego_aid: corrected_first_pub_year}
    
    Returns:
        DataFrame with corrections applied
    """
    
    df_corrected = faculty_df.copy()
    
    # Add correction tracking columns
    df_corrected['first_pub_year_original'] = df_corrected['first_pub_year']
    df_corrected['manually_corrected'] = False
    df_corrected['correction_date'] = None
    
    # Apply corrections
    for ego_aid, corrected_year in corrections.items():
        mask = df_corrected['oa_uid'] == ego_aid
        if mask.any():
            df_corrected.loc[mask, 'first_pub_year'] = corrected_year
            df_corrected.loc[mask, 'manually_corrected'] = True
            df_corrected.loc[mask, 'correction_date'] = datetime.now().strftime('%Y-%m-%d')
    
    return df_corrected

def save_corrections_log(corrections, filename='pub_year_corrections.csv'):
    """
    Save corrections to a log file for reproducibility
    """
    
    corrections_df = pd.DataFrame([
        {'ego_aid': ego_aid, 'corrected_first_pub_year': year, 
         'correction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        for ego_aid, year in corrections.items()
    ])
    
    corrections_df.to_csv(filename, index=False)
    print(f"Corrections saved to {filename}")

def run_interactive_cleaning(analysis_df, papers_df, faculty_df):
    """
    Complete interactive cleaning workflow
    """
    
    print("=== Interactive Publication Year Cleaning ===")
    print(f"Total cases flagged for review: {len(analysis_df[analysis_df['recommendation'] != 'appears_reasonable'])}")
    
    # Run interactive review
    corrections = interactive_review_pub_years(analysis_df, papers_df, faculty_df)
    
    if corrections:
        print(f"\n=== Summary ===")
        print(f"Manual corrections made: {len(corrections)}")
        
        # Apply corrections
        faculty_corrected = apply_manual_corrections(faculty_df, corrections)
        
        # Save corrections log
        save_corrections_log(corrections)
        
        print(f"✓ Corrections applied to faculty data")
        print(f"✓ Correction log saved")
        
        return faculty_corrected, corrections
    else:
        print("No corrections made")
        return faculty_df, {}

# Quick review function for specific cases
def quick_review_faculty(ego_aid, papers_df, faculty_df):
    """
    Quick review of a specific faculty member's publication timeline
    """
    
    # Get faculty info
    faculty_info = faculty_df[faculty_df['oa_uid'] == ego_aid].iloc[0]
    faculty_papers = papers_df[papers_df['ego_aid'] == ego_aid]
    
    print(f"Faculty: {faculty_info['payroll_name']}")
    print(f"Current first pub year: {faculty_info['first_pub_year']}")
    print(f"Total papers: {len(faculty_papers)}")
    
    if len(faculty_papers) > 0:
        pub_years = faculty_papers['pub_year'].dropna().astype(int).sort_values()
        year_counts = pub_years.value_counts().sort_index()
        
        print("\nPublication timeline:")
        for year, count in year_counts.head(15).items():
            print(f"  {year}: {count} papers")
        
        if len(year_counts) > 15:
            print(f"  ... and {len(year_counts) - 15} more years")
    
    return faculty_papers
 
# First, run the gap analysis
analysis_df = analyze_publication_gaps(papers_df, faculty_df)
analysis_df = create_cleaning_recommendations(analysis_df)

analysis_df[analysis_df.ego_aid == 'A5072094717']

# Then run interactive review
faculty_cleaned, corrections = run_interactive_cleaning(analysis_df, papers_df, faculty_df)

faculty_cleaned = faculty_cleaned[faculty_df.columns]

faculty_cleaned.to_csv("../static/data/academic-research-groups.csv", index=False)
faculty_cleaned.to_parquet("../static/data/academic-research-groups.parquet")
