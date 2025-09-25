import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_financial_news(query="finance"):
    """
    Fetches top financial news articles from the News API.

    Args:
        query (str): The search term for news articles.

    Returns:
        list: A list of dictionaries, where each dictionary is a news article.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return {"error": "NEWS_API_KEY not found in .env file."}

    url = f"https://newsapi.org/v2/top-headlines?q={query}&category=business&language=en&apiKey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        articles = response.json().get("articles", [])
        
        # Limit to top 5 articles and extract relevant info
        top_articles = []
        for article in articles[:5]:
            top_articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url")
            })
        return top_articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return {"error": f"Could not fetch news. Please check your connection and API key. Error: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred in get_financial_news: {e}")
        return {"error": f"An unexpected error occurred: {e}"}

def summarize_news_for_llm(articles):
    """
    Creates a concise summary of news articles for the LLM.
    """
    if not articles or "error" in articles:
        return "No financial news could be retrieved at this time."

    summary = "Here are the latest top financial news headlines:\n"
    for i, article in enumerate(articles, 1):
        summary += f"{i}. {article['title']}: {article['description']}\n"
    return summary
