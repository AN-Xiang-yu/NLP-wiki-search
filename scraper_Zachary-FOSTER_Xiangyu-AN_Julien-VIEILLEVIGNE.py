import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import time

# List of themes to scrape
themes = [
    "World War II"
    "Chinese history",
]


base_url = "https://en.wikipedia.org/wiki/"

# Initialize list to store the data and a set to track visited URLs
visited_urls = set()


def scrape_page(url, theme, depth=0, max_depth=2, header_levels={}, max_urls=100, number_of_links_to_follow=10):
    print(url)
    time.sleep(0.2)

    print(len(visited_urls) % max_urls)
    if len(visited_urls) % max_urls >= max_urls-1:
        visited_urls.add(url)
        return []

    if url in visited_urls or depth > max_depth:
        return []

    visited_urls.add(url)

    local_data = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract page title dynamically
    page_title = soup.title.string if soup.title else 'No Title Found'

    content = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    current_headers = header_levels.copy()

    for element in content:
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Update the headers based on the current header level
            level = int(element.name[1])
            current_headers[element.name] = element.get_text().strip()
            # Clear all lower header levels
            for i in range(level+1, 6):
                current_headers[f'h{i}'] = ''
        elif element.name == 'p':
            paragraph = element.get_text().strip()
            if paragraph:
                bold_words = [b.get_text().strip()
                              for b in element.find_all(['b', 'strong'])]
                local_data.append({
                    "theme": theme,
                    "page_title": page_title,
                    **{f'h{i}': current_headers.get(f'h{i}', '') for i in range(1, 6)},
                    "paragraph": paragraph,
                    "bold_words": bold_words,
                    "source": url
                })

            if depth < max_depth:
                for index, link in enumerate(element.find_all('a', href=True)):
                    href = link['href']
                    # Following themed links, so not the about etc...
                    if href.startswith('/wiki/') and not ':' in href and index < number_of_links_to_follow and len(visited_urls) < max_urls:
                        full_url = urljoin(base_url, href)
                        if urlparse(full_url).netloc == 'en.wikipedia.org':
                            local_data.extend(scrape_page(
                                full_url, theme, depth + 1, max_depth, current_headers, max_urls, number_of_links_to_follow))

    return local_data


# Scrape each theme
all_data = []
for theme in themes:
    print("Scraping theme:", theme)
    page_url = base_url + theme.replace(" ", "_")
    all_data.extend(scrape_page(page_url, theme, max_depth=2,
                    max_urls=1500, number_of_links_to_follow=20))

df = pd.DataFrame(all_data)

df.to_csv('wikipedia_dataset.csv', index=False)

print("Scraping completed and data saved.")
