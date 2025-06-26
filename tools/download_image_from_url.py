def execute_download_image_from_url(params):
    import os
    import requests
    from urllib.parse import urlparse
    
    try:
        # 参数验证
        image_url = params.get('image_url')
        save_path = params.get('save_path')
        
        if not image_url or not save_path:
            return "Error: Both 'image_url' and 'save_path' parameters are required."
        
        # 验证URL格式
        parsed_url = urlparse(image_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return "Error: Invalid image URL format."
        
        # 创建保存目录（如果不存在）
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 下载图片
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # 处理可能的编码问题
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            return "Error: The URL does not point to a valid image."
        
        # 写入文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
                
        return f"Success: Image downloaded and saved to {save_path}"
        
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to download image from URL - {str(e)}"
    except IOError as e:
        return f"Error: Failed to save image to {save_path} - {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"