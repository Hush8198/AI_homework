def execute_validate_image_integrity(params):
    import os
    from PIL import Image
    import json
    
    try:
        # 验证输入参数
        if not isinstance(params, dict):
            return json.dumps({"status": "error", "message": "Input parameters must be a dictionary"})
        
        image_path = params.get("image_path")
        if not image_path:
            return json.dumps({"status": "error", "message": "Missing required parameter: image_path"})
        
        # 检查路径是否存在
        if not os.path.exists(image_path):
            return json.dumps({"status": "error", "message": f"Path does not exist: {image_path}"})
        
        # 收集所有图像文件
        image_files = []
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        
        for root, _, files in os.walk(image_path):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            return json.dumps({"status": "warning", "message": "No image files found in the specified path"})
        
        # 验证图像完整性
        results = {
            "total_images": len(image_files),
            "valid_images": 0,
            "invalid_images": [],
            "status": "success"
        }
        
        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    img.verify()  # 验证图像完整性
                results["valid_images"] += 1
            except Exception as e:
                results["invalid_images"].append({
                    "path": img_path,
                    "error": str(e)
                })
        
        # 处理中文路径编码问题
        results["invalid_images"] = [
            {k: v.encode('utf-8').decode('utf-8') if isinstance(v, str) else v 
             for k, v in item.items()}
            for item in results["invalid_images"]
        ]
        
        return json.dumps(results, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"})