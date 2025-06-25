def execute_get_bilibili_title(params):
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    
    try:
        url = params.get('url', 'https://www.bilibili.com')
        
        # 验证URL格式
        parsed_url = urllib.parse.urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return "错误：提供的URL格式不正确"
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 处理可能的编码问题
        if response.encoding.lower() != 'utf-8':
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else "未找到标题"
        
        return title
    
    except requests.exceptions.RequestException as e:
        return f"网络请求错误: {str(e)}"
    except Exception as e:
        return f"发生错误: {str(e)}"