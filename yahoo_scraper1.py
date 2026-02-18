from bs4 import BeautifulSoup 
import time
import requests 
import re
from random import randint
from html.parser import HTMLParser 
 
USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'} 
 
class SearchEngine: 
    @staticmethod 
    def search(query, sleep=True): 
        if sleep:
            # time.sleep(randint(10, 100)) 
            pass
        temp_url = '+'.join(query.split()) 
        url = 'http://www.search.yahoo.com/search?p=' + temp_url + '&n=30'
        print(url)
        soup = BeautifulSoup(requests.get(url, headers=USER_AGENT).text, "html.parser") 
        new_results = SearchEngine.scrape_search_result(soup) 
        return new_results 
 
    @staticmethod 
    def scrape_search_result(soup): 
        raw_results = soup.find_all("div", attrs={"class": re.compile(r"algo")})
        results = [] 

        for result in raw_results: 
            link = result.get('href') 
            results.append(link) 
        return results
 
#############Driver code############ 
print(SearchEngine.search("QUERY"))
####################################