def execute_calculate_division(params):
    import re
    
    try:
        # 获取输入参数
        division_expression = params.get('division_expression', '').strip()
        
        if not division_expression:
            return "错误：请输入除法算式"
        
        # 使用正则表达式验证并提取数字
        match = re.match(r'^\s*([+-]?\d*\.?\d+)\s*/\s*([+-]?\d*\.?\d+)\s*$', division_expression)
        if not match:
            return "错误：无效的除法算式格式，请使用'数字/数字'的格式"
        
        numerator = float(match.group(1))
        denominator = float(match.group(2))
        
        if denominator == 0:
            return "错误：除数不能为零"
        
        result = numerator / denominator
        
        # 如果结果是整数则返回整数形式，否则保留小数
        if result.is_integer():
            return str(int(result))
        else:
            return str(result)
            
    except ValueError:
        return "错误：无效的数字格式"
    except Exception as e:
        return f"错误：计算过程中发生意外错误 - {str(e)}"