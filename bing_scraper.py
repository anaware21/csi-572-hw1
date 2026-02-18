from bs4 import BeautifulSoup 
import time
import requests 
from random import randint
from html.parser import HTMLParser 
import json
import re
from urllib.parse import unquote, urlparse

USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'} 

class SearchEngine: 
    @staticmethod 
    def search(query, sleep=True, debug=False): 
        if sleep:
            time.sleep(randint(10, 100)) 
        temp_url = '+'.join(query.split()) 
        url = 'http://www.bing.com/search?q=' + temp_url + '&count=30'
        
        if debug:
            print(f"  URL: {url}")
            
        soup = BeautifulSoup(requests.get(url, headers=USER_AGENT).text, "html.parser") 
        new_results = SearchEngine.scrape_search_result(soup, debug=debug) 
        return new_results 
 
    @staticmethod 
    def scrape_search_result(soup, debug=False): 
        results = [] 
        seen_urls = set()
        
        # Bing uses 'li' tags with class 'b_algo'
        # Try multiple patterns in case Bing's HTML changes
        selector_patterns = [
            # Pattern 1: Standard b_algo class (most common)
            ("li", {"class": "b_algo"}),
            # Pattern 2: b_algo with additional classes
            ("li", {"class": re.compile(r"b_algo")}),
            # Pattern 3: Any list item with algo in class
            ("li", {"class": re.compile(r".*algo.*", re.IGNORECASE)}),
            # Pattern 4: Direct links in results
            ("h2", {}),
        ]
        
        # Try each selector pattern
        for pattern_num, (tag_name, attrs) in enumerate(selector_patterns, 1):
            if len(results) >= 10:
                break
            
            raw_results = soup.find_all(tag_name, attrs=attrs, limit=50)
            
            if debug and raw_results:
                print(f"  Pattern {pattern_num} ({tag_name}) found {len(raw_results)} elements")
            
            for result in raw_results: 
                if len(results) >= 10:  # Only get top 10
                    break
                    
                # Find the link within the element
                link_tag = result.find('a')
                    
                if not link_tag or not link_tag.get('href'):
                    continue
                    
                link = link_tag.get('href')
                
                if debug:
                    print(f"    Raw link: {link[:100]}")
                
                # Bing uses tracking/redirect URLs, extract the actual URL
                # Format: https://www.bing.com/ck/a?!&&p=...&u=BASE64_ENCODED_URL&ntb=1
                if 'bing.com/ck/a' in link:
                    # Extract the 'u=' parameter which contains URL-safe base64 encoded URL
                    import base64
                    match = re.search(r'[?&]u=([^&]+)', link)
                    if match:
                        encoded_url = match.group(1)
                        try:
                            # Bing uses a modified encoding: 'a1' prefix + URL-safe base64
                            # Remove 'a1' prefix first
                            if encoded_url.startswith('a1'):
                                encoded_url = encoded_url[2:]
                            
                            # Add padding if needed (base64 requires length to be multiple of 4)
                            padding_needed = len(encoded_url) % 4
                            if padding_needed:
                                encoded_url += '=' * (4 - padding_needed)
                            
                            # Decode from URL-safe base64
                            decoded_bytes = base64.urlsafe_b64decode(encoded_url)
                            # Convert bytes to string
                            link = decoded_bytes.decode('utf-8')
                            
                            if debug:
                                print(f"    Decoded from base64: {link[:100]}")
                        except Exception as e:
                            if debug:
                                print(f"    Failed to decode base64: {e}")
                            continue
                    else:
                        if debug:
                            print(f"    No 'u=' parameter found")
                        continue
                elif 'bing.com' in link.lower() and '/aclick?' in link:
                    # This is an ad, skip it
                    if debug:
                        print(f"    Skipped: Bing ad")
                    continue
                
                # Normalize the URL
                link = SearchEngine.normalize_url(link)
                
                if debug and link:
                    print(f"    Normalized: {link[:100]}")
                
                # Skip invalid URLs and duplicates
                if not link:
                    continue
                if link in seen_urls:
                    if debug:
                        print(f"    Skipped: duplicate")
                    continue
                if not SearchEngine.is_valid_url(link):
                    if debug:
                        print(f"    Skipped: invalid")
                    continue
                    
                seen_urls.add(link)
                results.append(link)
                
                if debug:
                    print(f"    ✓ Added! Total so far: {len(results)}")
            
        return results[:10]  # Ensure maximum 10 results
    
    @staticmethod
    def normalize_url(url):
        """Normalize URLs for consistency"""
        if not url:
            return None
        
        # Remove fragments
        url = url.split('#')[0]
        
        # Skip relative URLs
        if url.startswith('/'):
            return None
        
        # Ensure scheme exists
        if not url.startswith('http'):
            url = 'http://' + url
        
        try:
            parsed = urlparse(url)
        except:
            return None
        
        # Remove trailing slash
        path = parsed.path.rstrip('/')
        
        # Reconstruct URL
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
    
    @staticmethod
    def is_valid_url(url):
        """Check if URL is a valid organic result"""
        if not url:
            return False
        
        # Skip internal Bing links and other non-organic results
        skip_patterns = [
            'javascript:',
            'mailto:',
            'bing.com/search',
            'bing.com/aclick',
            'bing.com/ck/a',  # Bing redirect URLs (should be decoded already)
            'microsoft.com/en-us/bing',
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True

#############Driver code############ 
def load_queries(filename):
    """Load queries from text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        return queries
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        return []

def scrape_all_queries(query_file, output_file='hw1.json'):
    """Scrape all queries and save to JSON"""
    print(f"\n{'='*70}")
    print(f"Bing Search Engine Scraper - HW1")
    print(f"{'='*70}\n")
    
    # Load queries
    queries = load_queries(query_file)
    if not queries:
        print("No queries loaded. Exiting.")
        return
    
    print(f"Loaded {len(queries)} queries from {query_file}\n")
    print(f"Estimated time: 1-2 hours (with delays to avoid blocking)\n")
    print(f"{'='*70}\n")
    
    all_results = {}
    
    for i, query in enumerate(queries, 1):
        print(f"[Query {i}/{len(queries)}]: {query}")
        
        try:
            results = SearchEngine.search(query, sleep=(i > 1))  # No delay on first query
            all_results[query] = results
            if len(results) < 10:
                print(f"  ⚠️  Only {len(results)} results (this is OK - assignment allows <10)\n")
            else:
                print(f"  ✓ Found {len(results)} results\n")
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            all_results[query] = []
        
        # Save progress every 10 queries
        if i % 10 == 0:
            print(f"{'='*70}")
            print(f"Saving progress... ({i}/{len(queries)} completed)")
            print(f"{'='*70}\n")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Final save
    print(f"{'='*70}")
    print(f"Scraping complete! Saving final results...")
    print(f"{'='*70}\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to: {output_file}")
    print(f"✓ Total queries scraped: {len(all_results)}\n")

# Main execution
if __name__ == '__main__':
    # For Bing
    query_file = 'query_set.txt'  # Your query file
    output_file = 'hw1.json'
    
    # Uncomment to test with a single query first (RECOMMENDED)
    # print(SearchEngine.search("What is machine learning", sleep=False, debug=True))
    
    # Scrape all queries
    scrape_all_queries(query_file, output_file)
####################################