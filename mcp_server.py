"""MCP server for web research and Markdown blog writing.

This file is the single source of truth for the two tools used by CrewAI.
"""

import json
import os
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("blog-tools")

@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web with Tavily and return source-backed results."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is missing from the environment.")
    response = requests.post(
        "https://api.tavily.com/search",
        json = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max(1, min(max_results, 10)),
            "include_answer": True,
        },
        timeout = 30
    )
    response.raise_for_status()
    payload = response.json()
    results = [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
        }
        for item in payload.get("results", [])
    ]
    return json.dumps(
        {"answer": payload.get("answer", ""), "results": results},
    )

@mcp.tool()
def write_blog_markdown(content: str, file_path: str = "blog.md") -> str:
    """Write blog content to a Markdown file and return its absolute path."""
    destination = Path(file_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return f"Blog written to {destination}"

if __name__ == "__main__":
    mcp.run()