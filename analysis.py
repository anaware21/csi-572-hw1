"""
Analysis Script for Bing Search Results - HW1
Calculates percent overlap and Spearman correlation coefficient
Compares Bing results (hw1.json) with Google results (google_results.json)
"""

import json
import csv
from urllib.parse import urlparse


def normalize_url(url):
    """Normalize URLs for comparison"""
    if not url:
        return None
    
    # Remove fragments
    url = url.split('#')[0]
    
    # Ensure scheme exists
    if not url.startswith('http'):
        url = 'http://' + url
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except:
        return None
    
    # Remove trailing slash
    path = parsed.path.rstrip('/')
    
    # Reconstruct URL (keeping original scheme)
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


def urls_match(url1, url2):
    """Check if two URLs are equivalent"""
    norm1 = normalize_url(url1)
    norm2 = normalize_url(url2)
    
    if not norm1 or not norm2:
        return False
    
    if norm1 == norm2:
        return True
    
    # Handle http vs https as same
    if norm1.replace('https://', 'http://') == norm2.replace('https://', 'http://'):
        return True
    
    # Handle www vs non-www
    norm1_no_www = norm1.replace('://www.', '://')
    norm2_no_www = norm2.replace('://www.', '://')
    
    if norm1_no_www == norm2_no_www:
        return True
    
    return False


def find_matches(google_results, bing_results):
    """
    Find matching URLs and their positions
    Returns: list of tuples (google_rank, bing_rank)
    """
    matches = []
    
    for g_idx, g_url in enumerate(google_results, 1):
        for b_idx, b_url in enumerate(bing_results, 1):
            if urls_match(g_url, b_url):
                matches.append((g_idx, b_idx))
                break  # Found match, move to next Google URL
    
    return matches


def calculate_percent_overlap(google_results, bing_results):
    """Calculate percentage of overlapping results"""
    matches = find_matches(google_results, bing_results)
    
    # Overlap is based on Google's result count (always 10)
    google_count = len(google_results)
    overlap_count = len(matches)
    
    if google_count == 0:
        return 0.0
    
    percent = (overlap_count / google_count) * 100
    return percent


def calculate_spearman_correlation(google_results, bing_results):
    """
    Calculate Spearman's rank correlation coefficient
    
    Special cases:
    - If no overlap: rho = 0
    - If only 1 match with same rank: rho = 1
    - If only 1 match with different rank: rho = 0
    """
    matches = find_matches(google_results, bing_results)
    
    n = len(matches)
    
    # No overlap
    if n == 0:
        return 0.0
    
    # Only one match
    if n == 1:
        g_rank, b_rank = matches[0]
        if g_rank == b_rank:
            return 1.0
        else:
            return 0.0
    
    # Multiple matches - use Spearman formula
    sum_d_squared = 0
    
    for g_rank, b_rank in matches:
        d = g_rank - b_rank
        sum_d_squared += d * d
    
    # Spearman formula: rho = 1 - (6 * sum(d^2)) / (n * (n^2 - 1))
    denominator = n * (n * n - 1)
    
    if denominator == 0:
        return 0.0
    
    rho = 1 - (6 * sum_d_squared) / denominator
    
    return rho


def analyze_results(google_json_file='google_results.json', 
                    bing_json_file='hw1.json', 
                    output_csv='hw1.csv'):
    """
    Analyze Bing search results against Google reference
    """
    print(f"\n{'='*70}")
    print(f"{'BING vs GOOGLE ANALYSIS':^70}")
    print(f"{'='*70}\n")
    
    # Load JSON files
    print(f"📂 Loading Google reference results from: {google_json_file}")
    try:
        with open(google_json_file, 'r', encoding='utf-8') as f:
            google_data = json.load(f)
        print(f"   ✓ Loaded {len(google_data)} Google results")
    except FileNotFoundError:
        print(f"   ❌ Error: File '{google_json_file}' not found!")
        print(f"   Make sure the file is in the same directory")
        return None
    except json.JSONDecodeError:
        print(f"   ❌ Error: Invalid JSON format in {google_json_file}")
        return None
    
    print(f"\n📂 Loading Bing search results from: {bing_json_file}")
    try:
        with open(bing_json_file, 'r', encoding='utf-8') as f:
            bing_data = json.load(f)
        print(f"   ✓ Loaded {len(bing_data)} Bing results")
    except FileNotFoundError:
        print(f"   ❌ Error: File '{bing_json_file}' not found!")
        print(f"   Run bing_scraper.py first to generate {bing_json_file}")
        return None
    except json.JSONDecodeError:
        print(f"   ❌ Error: Invalid JSON format in {bing_json_file}")
        return None
    
    print(f"\n{'='*70}")
    print(f"🔍 Analyzing {len(google_data)} queries...")
    print(f"{'='*70}\n")
    
    # Prepare results
    results = []
    total_overlap_count = 0
    total_percent_overlap = 0.0
    total_spearman = 0.0
    queries_analyzed = 0
    queries_with_no_bing_results = 0
    
    # Analyze each query
    for query_num, (query, google_results) in enumerate(google_data.items(), 1):
        # Get corresponding Bing results
        bing_results = bing_data.get(query, [])
        
        if not bing_results:
            queries_with_no_bing_results += 1
            # Still record the query with 0 results
            results.append({
                'query_id': f'Query {query_num}',
                'query_text': query,
                'overlap_count': 0,
                'percent_overlap': 0.0,
                'spearman': 0.0
            })
            continue
        
        # Find matches
        matches = find_matches(google_results, bing_results)
        overlap_count = len(matches)
        
        # Calculate metrics
        percent_overlap = calculate_percent_overlap(google_results, bing_results)
        spearman = calculate_spearman_correlation(google_results, bing_results)
        
        # Store result
        results.append({
            'query_id': f'Query {query_num}',
            'query_text': query,
            'overlap_count': overlap_count,
            'percent_overlap': percent_overlap,
            'spearman': spearman
        })
        
        # Accumulate totals
        total_overlap_count += overlap_count
        total_percent_overlap += percent_overlap
        total_spearman += spearman
        queries_analyzed += 1
        
        # Print progress
        if query_num % 20 == 0:
            print(f"   Processed {query_num}/{len(google_data)} queries...")
    
    # Calculate averages
    if queries_analyzed > 0:
        avg_overlap_count = total_overlap_count / queries_analyzed
        avg_percent_overlap = total_percent_overlap / queries_analyzed
        avg_spearman = total_spearman / queries_analyzed
    else:
        avg_overlap_count = 0
        avg_percent_overlap = 0
        avg_spearman = 0
    
    print(f"\n{'='*70}")
    print(f"💾 Writing results to: {output_csv}")
    print(f"{'='*70}\n")
    
    # Write to CSV
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Queries', 'Number of Overlapping Results', 
                           'Percent Overlap', 'Spearman Coefficient'])
            
            # Data rows
            for result in results:
                writer.writerow([
                    result['query_id'],
                    result['overlap_count'],
                    f"{result['percent_overlap']:.1f}",
                    f"{result['spearman']:.2f}"
                ])
            
            # Averages row
            writer.writerow([
                'Averages',
                f"{avg_overlap_count:.1f}",
                f"{avg_percent_overlap:.1f}",
                f"{avg_spearman:.2f}"
            ])
        
        print(f"✓ CSV file created successfully!\n")
    except Exception as e:
        print(f"❌ Error writing CSV: {e}\n")
        return None
    
    # Print summary
    print(f"{'='*70}")
    print(f"{'ANALYSIS RESULTS':^70}")
    print(f"{'='*70}")
    print(f"\n📊 Summary Statistics:")
    print(f"   Total queries analyzed: {queries_analyzed}")
    print(f"   Queries with no Bing results: {queries_with_no_bing_results}")
    print(f"\n📈 Average Metrics:")
    print(f"   Average overlapping results: {avg_overlap_count:.2f} out of 10")
    print(f"   Average percent overlap: {avg_percent_overlap:.2f}%")
    print(f"   Average Spearman coefficient: {avg_spearman:.2f}")
    print(f"\n{'='*70}\n")
    
    return {
        'avg_overlap_count': avg_overlap_count,
        'avg_percent_overlap': avg_percent_overlap,
        'avg_spearman': avg_spearman,
        'queries_analyzed': queries_analyzed,
        'queries_no_results': queries_with_no_bing_results
    }


def generate_hw1_txt(stats, output_file='hw1.txt'):
    """Generate the hw1.txt summary file for Bing"""
    
    if not stats:
        print("❌ No statistics available to generate hw1.txt")
        return
    
    avg_overlap = stats['avg_percent_overlap']
    avg_spearman = stats['avg_spearman']
    queries = stats['queries_analyzed']
    no_results = stats['queries_no_results']
    
    # Determine performance assessment
    if avg_overlap >= 70:
        overlap_assessment = "very similar"
    elif avg_overlap >= 50:
        overlap_assessment = "moderately similar"
    elif avg_overlap >= 30:
        overlap_assessment = "somewhat similar"
    else:
        overlap_assessment = "quite different"
    
    if avg_spearman >= 0.7:
        rank_assessment = "highly correlated"
    elif avg_spearman >= 0.4:
        rank_assessment = "moderately correlated"
    elif avg_spearman >= 0:
        rank_assessment = "weakly correlated"
    else:
        rank_assessment = "negatively correlated"
    
    # Generate comprehensive summary
    summary = f"""Search Engine Comparison Analysis: Bing vs Google

Based on the analysis of {queries} queries, Bing performed as follows compared to Google:

Average Percent Overlap: {avg_overlap:.1f}%
Average Spearman Coefficient: {avg_spearman:.2f}

The results indicate that Bing is {overlap_assessment} to Google in terms of the URLs returned. With an average overlap of {avg_overlap:.1f}%, approximately {avg_overlap/10:.1f} out of every 10 results from Bing match those returned by Google for the same query.

The average Spearman coefficient of {avg_spearman:.2f} suggests that the ranking of results is {rank_assessment} between the two search engines. """

    if avg_spearman > 0:
        summary += f"""A positive coefficient indicates that when both engines return the same URLs, they tend to rank them in a similar order. This suggests that Bing and Google may be using similar ranking signals or algorithms, at least for the overlapping results."""
    else:
        summary += f"""A negative coefficient indicates that even when both engines return the same URLs, they rank them quite differently. This suggests that Bing and Google employ different ranking algorithms or weight ranking factors differently, leading to divergent result orderings."""

    summary += f"""

Overall, Bing {'performs comparably to Google' if avg_overlap >= 60 and avg_spearman >= 0.5 else 'shows significant differences from Google'} in both result selection and ranking for these queries."""

    if no_results > 0:
        summary += f""" It should be noted that {no_results} queries returned no results from Bing, which may indicate issues with query handling or scraping limitations."""

    summary += """

This comparison provides insights into how different search engines may serve different results to users, even for identical queries, which has implications for information access and search engine optimization strategies.
"""
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"{'='*70}")
        print(f"📝 Summary paragraph saved to: {output_file}")
        print(f"{'='*70}\n")
    except Exception as e:
        print(f"❌ Error writing summary file: {e}\n")


def main():
    """Main function for Bing analysis"""
    
    print("\n" + "="*70)
    print("BING SEARCH RESULTS ANALYSIS - HW1")
    print("="*70)
    
    # Configuration - using your actual file names
    google_json = 'google_results.json'
    bing_json = 'hw1.json'
    output_csv = 'hw1.csv'
    output_txt = 'hw1.txt'
    
    print("\n📋 Configuration:")
    print(f"   Google reference: {google_json}")
    print(f"   Bing results: {bing_json}")
    print(f"   Output CSV: {output_csv}")
    print(f"   Output TXT: {output_txt}")
    
    input("\n▶ Press Enter to start analysis...")
    
    # Run analysis
    stats = analyze_results(google_json, bing_json, output_csv)
    
    if stats:
        # Generate summary text file
        generate_hw1_txt(stats, output_txt)
        
        print(f"{'='*70}")
        print(f"{'✅ ALL FILES GENERATED SUCCESSFULLY':^70}")
        print(f"{'='*70}")
        print(f"\n📦 Deliverables ready for submission:")
        print(f"   1. {bing_json} - Your scraped Bing results")
        print(f"   2. {output_csv} - Overlap and correlation analysis")
        print(f"   3. {output_txt} - Summary paragraph")
        print(f"\n📤 Upload these 3 files to your Google Drive CSCI572/hw1 folder")
        print(f"{'='*70}\n")
    else:
        print("\n❌ Analysis failed. Please check error messages above.\n")


if __name__ == '__main__':
    main()