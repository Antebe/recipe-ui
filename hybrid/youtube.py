# hybrid/youtube.py

"""
Simple helper to build a YouTube search URL for a given query.
"""


def youtube_search(query: str) -> str:
    """
    Return a YouTube search URL for a given query string.

    Example:
        query = "how to preheat an oven"
        -> "https://www.youtube.com/results?search_query=how+to+preheat+an+oven"
    """
    base_url = "https://www.youtube.com/results?search_query="
    formatted = query.strip().replace(" ", "+")
    return base_url + formatted
