def execute_check_path_access(params):
    import os
    import sys
    
    try:
        path = params.get('path', '')
        if not path:
            return "错误：未提供路径参数"
        
        # 标准化路径，处理斜杠和反斜杠问题
        normalized_path = os.path.normpath(path)
        
        # 检查路径是否存在
        if not os.path.exists(normalized_path):
            return f"错误：路径 '{normalized_path}' 不存在"
        
        # 检查是否是目录
        if not os.path.isdir(normalized_path):
            return f"错误：'{normalized_path}' 不是目录"
        
        # 检查写入权限
        if os.access(normalized_path, os.W_OK):
            return f"成功：路径 '{normalized_path}' 存在且可写入"
        else:
            return f"警告：路径 '{normalized_path}' 存在但无写入权限"
            
    except Exception as e:
        return f"发生意外错误：{str(e)}"