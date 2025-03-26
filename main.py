import requests
from bs4 import BeautifulSoup
from dateutil import parser
import json
import os
import re


def load_existing_articles(filename="news.json"):
    """Load existing articles from JSON to avoid duplicates."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def scrape_amnesty_article(article_url):
    """Fetch the first few sentences from the actual article page."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(article_url, headers=headers)

    if response.status_code != 200:
        return "Excerpt not available"

    soup = BeautifulSoup(response.text, "html.parser")
    paragraph_tags = soup.article.find_all("p")  # Adjust if needed

    if paragraph_tags:
        full_text = " ".join([p.text.strip() for p in paragraph_tags])  # Merge paragraphs
        sentences = re.split(r'(?<=[.!?]) +', full_text)  # Split into sentences
        return " ".join(sentences[:3])  # Return first 3 sentences

    return "Excerpt not available"


def scrape_amnesty_news(max_pages=2, filename="news.json"):
    base_url = "https://www.amnesty.org/en/latest/"
    headers = {"User-Agent": "Mozilla/5.0"}
    existing_articles = load_existing_articles(filename)
    existing_links = {article["url"] for article in existing_articles}
    new_articles = []
    page_count = 0

    while base_url and page_count < max_pages:
        response = requests.get(base_url, headers=headers)

        if response.status_code != 200:
            print("Failed to retrieve the webpage")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        for article in soup.find_all("article", class_="wp-block-group"):  # Adjust class as needed
            title_tag = article.h2.find("a")
            link_tag = article.h2.find("a", href=True)
            date_tag = article.div.time['datetime']

            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = link_tag["href"].strip()
                date = str(parser.parse(date_tag).strftime('%Y-%m-%d'))

                if not link.startswith("http"):
                    link = "https://www.amnesty.org" + link



                if link not in existing_links:
                    article = scrape_amnesty_article(link)
                    new_articles.append({"url": link, "title": title, "release_date": date, "article": article})
                    print(title + '--' + link + '--' + date + '--' + article)
                    existing_links.add(link)

        next_page_tag = soup.select_one("a.wp-block-query-pagination-next")
        base_url = next_page_tag["href"] if next_page_tag else None
        page_count += 1

    return existing_articles+new_articles


def update_news_json(articles, filename="news.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4)


def main():
    articles = scrape_amnesty_news()
    if articles:
        update_news_json(articles)
        print("News updated and pushed to GitHub")
    else:
        print("No new articles found")


if __name__ == "__main__":
    main()
