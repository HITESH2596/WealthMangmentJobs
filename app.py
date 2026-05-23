from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

class UAEWealthJobAggregator:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.locations = ["Dubai", "Abu Dhabi"]
        self.search_queries = ["Private Banker", "Wealth Relationship Manager", "HNWI Wealth"]
        
        # Zero-tolerance real estate firewall
        self.banned_keywords = ["real estate", "property", "broker", "developer", "off-plan", "leasing", "villa"]
        self.finance_keywords = ["aum", "portfolio", "banking", "private bank", "hnw", "hnwi", "difc", "adgm"]

    def _clean_and_filter(self, title, company, summary):
        combined = f"{title} {company} {summary}".lower()
        if any(banned in combined for banned in self.banned_keywords):
            return False
        if any(fin in combined for fin in self.finance_keywords):
            return True
        return False

    def get_jobs(self):
        jobs = []
        # For a quick real-time dashboard load, we scan top queries
        for loc in self.locations:
            for query in self.search_queries[:2]: 
                encoded_query = urllib.parse.quote(query)
                encoded_loc = urllib.parse.quote(f"{loc}, United Arab Emirates")
                url = f"https://ae.indeed.com/jobs?q={encoded_query}&l={encoded_loc}"
                
                try:
                    res = requests.get(url, headers=self.headers, timeout=5)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, 'html.parser')
                        cards = soup.find_all('div', class_='job_seen_beacon')
                        for card in cards:
                            t = card.find('h2', class_='jobTitle').text.strip() if card.find('h2', class_='jobTitle') else "N/A"
                            c = card.find('span', data_testid='company-name').text.strip() if card.find('span', data_testid='company-name') else "Financial Institution"
                            s = card.find('div', class_='job-snippet').text.strip() if card.find('div', class_='job-snippet') else ""
                            jk = card.find('a', data_jk=True)
                            lnk = f"https://ae.indeed.com/viewjob?jk={jk['data_jk']}" if jk else url
                            
                            if self._clean_and_filter(t, c, s):
                                jobs.append({"title": t, "company": c, "location": loc, "summary": s, "link": lnk})
                except Exception:
                    pass
        
        # Deduplicate
        seen = set()
        deduped = []
        for j in jobs:
            id_str = f"{j['title']}-{j['company']}".lower()
            if id_str not in seen:
                seen.add(id_str)
                deduped.append(j)
        return deduped

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/jobs')
def api_jobs():
    scraper = UAEWealthJobAggregator()
    listings = scraper.get_jobs()
    return jsonify(listings)

if __name__ == '__main__':
    app.run(debug=True, port=5000)