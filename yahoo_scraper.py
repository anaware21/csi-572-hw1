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
        url = 'http://www.search.yahoo.com/search?p=' + temp_url + '&n=30'
        
        if debug:
            print(f"  URL: {url}")
            
        soup = BeautifulSoup(requests.get(url, headers=USER_AGENT).text, "html.parser") 
        new_results = SearchEngine.scrape_search_result(soup, debug=debug) 
        return new_results 
 
    @staticmethod 
    def scrape_search_result(soup, debug=False): 
        results = [] 
        seen_urls = set()
        
        # Try multiple selector patterns for Yahoo (they change frequently)
        selector_patterns = [
            # Pattern 1: Standard algo class
            ("div", {"class": re.compile(r"algo")}),
            # Pattern 2: Direct link with specific class
            ("a", {"class": re.compile(r"ac-algo")}),
            # Pattern 3: Title divs
            ("div", {"class": re.compile(r"title")}),
            # Pattern 4: Compnent titles
            ("div", {"class": re.compile(r"compTitle")}),
            # Pattern 5: Any div with algo in any class
            ("div", {"class": re.compile(r".*algo.*", re.IGNORECASE)}),
        ]
        
        # Try each selector pattern
        for tag_name, attrs in selector_patterns:
            if len(results) >= 10:
                break
                
            raw_results = soup.find_all(tag_name, attrs=attrs, limit=50)
            
            for result in raw_results: 
                if len(results) >= 10:  # Only get top 10
                    break
                    
                # Find the link within the element
                if tag_name == 'a':
                    link_tag = result
                else:
                    link_tag = result.find('a')
                    
                if not link_tag or not link_tag.get('href'):
                    continue
                    
                link = link_tag.get('href')
                
                # Yahoo uses redirect URLs, extract the actual URL
                # Format: https://r.search.yahoo.com/_ylt=XXX/RU=https%3a%2f%2fwww.example.com/RK=2/RS=XXX
                if 'r.search.yahoo.com' in link or 'search.yahoo.com' in link:
                    # Try to extract the RU= parameter
                    match = re.search(r'/RU=([^/]+)/', link)
                    if match:
                        encoded_url = match.group(1)
                        # Decode the URL
                        try:
                            link = unquote(encoded_url)
                            # Convert remaining encoded characters
                            link = link.replace('%3a', ':').replace('%2f', '/').replace('%3A', ':').replace('%2F', '/')
                        except:
                            continue
                    else:
                        # Try alternative format: ?u= parameter
                        match = re.search(r'[?&]u=([^&]+)', link)
                        if match:
                            try:
                                link = unquote(match.group(1))
                            except:
                                continue
                        else:
                            continue
                
                # Normalize the URL
                link = SearchEngine.normalize_url(link)
                
                # Skip invalid URLs and duplicates
                if not link:
                    continue
                if link in seen_urls:
                    continue
                if not SearchEngine.is_valid_url(link):
                    continue
                    
                seen_urls.add(link)
                results.append(link)
            
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
        
        # Skip internal Yahoo links and other non-organic results
        skip_patterns = [
            'javascript:',
            'mailto:',
            'yahoo.com/search',
            'r.search.yahoo.com',
            'search.yahoo.com'
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
    print(f"Yahoo Search Engine Scraper - HW1")
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
                print(f"  ⚠️  Only {len(results)} results (this is OK - assignment allows <10)")
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
    # For Yahoo (USC ID ending 25-49)
    query_file = 'query_set.txt'  # Your query file
    output_file = 'hw1.json'
    
    # Uncomment to test with a single query first (RECOMMENDED)
    # print(SearchEngine.search("What is machine learning", sleep=False))
    
    # Scrape all queries
    scrape_all_queries(query_file, output_file)
####################################