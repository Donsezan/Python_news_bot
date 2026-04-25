import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

class FetchingData:
    def __init__(self, news_url, headers):
        self.news_url = news_url
        self.headers = headers

    def fetch_latest_articles(self):
        print("Fetching latest articles from:", self.news_url)
        try:
            resp = requests.get(self.news_url, headers=self.headers)
            resp.raise_for_status()  # ensure successful response
            print("Response status code:", resp.status_code)
            soup = BeautifulSoup(resp.text, "html.parser")
            # Example: find all article links in the main list (may need to adjust selector)
            articles = []
            for link in soup.select("a[href*='/malaga/']"):  # find anchors in Málaga section
                href = link.get('href')
                title = link.get_text(strip=True)
                if href and title:
                    articles.append((title, href))
            articles.reverse()  # Reverse to get the latest articles first
            print(f"Found {len(articles)} articles.")
            return articles
        except requests.RequestException as e:
            print(f"Error fetching articles: {e}")
            return []

    def fetch_and_summarize(self, title, href):
        print(f"Fetching and summarizing article: {title}")
        if(title == "Málaga"):
                return
            # Suppose we detect this is new (not seen before)
        resp = requests.get(href, headers=self.headers)
        print(f"Response status code for {href}: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract the title of the article
        title = soup.find('h1').get_text(strip=True)  # Assuming the title is in an <h1> tag
        print(f"Article title: {title}")
        # Extract the date of the article
        date_time_obj =  soup.find('p', class_='timestamp-atom') # Assuming the title is in an <h1> tag    
        # Convert to datetime object

        month_mapping = {
        'enero': '01',
        'febrero': '02',
        'marzo': '03',
        'abril': '04',
        'mayo': '05',
        'junio': '06',
        'julio': '07',
        'agosto': '08',
        'septiembre': '09',
        'octubre': '10',
        'noviembre': '11',
        'diciembre': '12'
    }
        date_string = date_time_obj.text.strip().split('\n')
        if date_string.__len__() > 1:
            date_string = date_string[1]
        else:
            date_string = date_string[0]
        # Replace the Spanish month name with its corresponding number
        for month_name, month_number in month_mapping.items():
            if month_name in date_string:
                date_string = date_string.replace(month_name, month_number)
                break  # Exit the loop once the month is found and replaced
        date_string = date_string.replace(" ", "")
        date_time = datetime.strptime(date_string, '%dde%m%Y-%H:%M')
        print(f"Article date: {date_time}")
        if date_time < datetime.now() - timedelta(days=7):
            print("Article is older than current time for the last 7 days, skipping.")
            return None
        # Extract the main content of the article
        content = []
        for paragraph in soup.find_all('p'):
            content.append(paragraph.get_text(strip=True))
        print("Extracted content.")

        # Extract image URLs from <source> tags
        main_colleft= soup.find('main', id ='content-body')
        source_images = [
            source['srcset'] for source in main_colleft.find_all('source')
            if not source.find_parent(class_='media-atom') 
            ]
        print(f"Found {len(source_images)} source images.")

        # Extract image URL from <img> tag
        img_tag = soup.find('img')
        img_url = img_tag['src'] if img_tag else None
        print(f"Found img tag: {img_url is not None}")

        # Combine all image URLs
        all_images = source_images + [img_url] if img_url else source_images

        max_resolution = 0

        for url in all_images:
            match = re.search(r'_(\d+)w_', url) # type: ignore
            if match:
                resolution = int(match.group(1))
                if resolution > max_resolution:
                    max_resolution = resolution
        print(f"Max image resolution: {max_resolution}")

        # Step 2: Filter URLs with the maximum resolution and .jpg extension
        unique_urls = set(all_images) 
        filtered_urls = [url for url in unique_urls if url.endswith('.jpg') and f'_{max_resolution}w_' in url] # type: ignore
        print(f"Found {len(filtered_urls)} filtered images.")
        # Join the content paragraphs into a single string
        return '\n'.join(content), filtered_urls, date_time
