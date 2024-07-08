import csv
import requests
from bs4 import BeautifulSoup

def load_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')
    return [(link.get('href'), link.text.strip()) for link in links if link.get('href')]

def save_to_csv(links, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Link Text'])
        writer.writerows(links)

def load_queue(filename):
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        return list(reader)

def save_result(url, text, filename):
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([url, text])

    save_to_csv(queue, filename)

def check_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def main():
    # Load and parse HTML
    html_content = load_html('./agents/curriculum/resources/bookmarks_6_24_24.html')
    urls = extract_urls(html_content)

    # Initially save all URLs to queue.csv
    save_to_csv(urls, './agents/curriculum/resources/queue.csv')

    # Load the queue
    queue = load_queue('./agents/curriculum/resources/queue.csv')

    # Process each URL
    while queue:
        url, text = queue.pop(0)
        status = check_url(url)

        # Save to appropriate file based on status
        if status is None or status >= 400:
            save_result(url, text, './agents/curriculum/resources/bad_resources.csv')
        else:
            save_result(url, text, './agents/curriculum/resources/good_resources.csv')

        # Update the queue file after processing each URL
        update_queue(queue, './agents/curriculum/resources/queue.csv')

if __name__ == "__main__":
    main()