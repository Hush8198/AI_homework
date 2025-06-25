import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class WebAgent:
    """Web Agent实现：支持搜索、GitHub检索和网页内容提取"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def google_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Google搜索（通过SerpAPI，需注册免费API Key）"""
        api_key = os.getenv("SERPAPI_KEY")  # 从.env获取
        if not api_key:
            raise ValueError("请先在.env中设置SERPAPI_KEY")
        
        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results
        }
        response = self.session.get("https://serpapi.com/search", params=params)
        return response.json().get("organic_results", [])

    def github_search(self, query: str, max_repos: int = 3) -> List[Dict]:
        """GitHub代码库搜索"""
        url = f"https://api.github.com/search/repositories?q={query}"
        response = self.session.get(url)
        if response.status_code != 200:
            return []
        return [
            {"name": repo["full_name"], "url": repo["html_url"]} 
            for repo in response.json().get("items", [])[:max_repos]
        ]

    def browse_web(self, url: str, extract_hyperlinks: bool = False) -> str:
        """简易网页浏览器（支持纯文本/链接提取）"""
        try:
            html = self.session.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            
            if extract_hyperlinks:
                return "\n".join([
                    f"{link.text.strip()}: {link['href']}" 
                    for link in soup.find_all("a", href=True)
                ])
            else:
                # 返回正文文本（去除脚本和样式）
                for element in soup(["script", "style"]):
                    element.decompose()
                return soup.get_text(separator="\n", strip=True)[:5000]  # 限制长度
        except Exception as e:
            return f"浏览失败: {str(e)}"

# 示例工具类（供ManagerAgent调用）
class WebTools:
    @staticmethod
    def get_tool_definitions() -> List[Dict]:
        """返回Web Agent的工具定义（JSON Schema格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "执行Google搜索并返回结果",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"},
                            "max_results": {"type": "integer", "description": "最大结果数"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "github_search",
                    "description": "搜索GitHub上的代码库",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"},
                            "max_repos": {"type": "integer", "description": "最大仓库数"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "browse_web",
                    "description": "浏览网页并提取文本或超链接",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "目标URL"},
                            "extract_hyperlinks": {"type": "boolean", "description": "是否只提取链接"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]