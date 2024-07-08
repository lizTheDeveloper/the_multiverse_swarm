import csv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# OpenAI client setup for local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def load_queue(filename):
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        return list(reader)

def update_queue(queue, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Link Text'])
        writer.writerows(queue)

def save_result(url, topic_and_summary, filename):
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([url, topic_and_summary])

def get_web_content(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

def categorize_and_summarize(text):
    try:
        completion = client.chat.completions.create(
            model="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
            messages=[
                {"role": "system", "content": "Please categorize this resource into a topic, and give a short description, separated by a | character"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    queue = load_queue('./agents/curriculum/resources/good_resources.csv')

    while queue:
        url, text = queue.pop(0)
        web_content = get_web_content(url)

        if web_content:
            topic_and_summary = categorize_and_summarize(web_content)
            save_result(url, topic_and_summary, './agents/curriculum/resources/categorized_resources.csv')
        else:
            save_result(url, "Failed to retrieve content", 'categorized_resources.csv')

        update_queue(queue, './agents/curriculum/resources/good_resources.csv')

if __name__ == "__main__":
    main()