def execute_save_math_problems(params):
    try:
        # 检查输入参数
        if not isinstance(params, dict):
            return "Error: Input must be a dictionary."
        
        file_path = params.get('file_path')
        if not file_path:
            return "Error: 'file_path' is required."
        
        # 生成10道加减法题目
        problems = []
        for _ in range(10):
            a = random.randint(0, 100)
            b = random.randint(0, 100)
            operator = random.choice(['+', '-'])
            
            if operator == '+':
                answer = a + b
                problem = f"{a} + {b} = "
            else:
                # 确保减法结果为正数
                a, b = max(a, b), min(a, b)
                answer = a - b
                problem = f"{a} - {b} = "
            
            problems.append((problem, answer))
        
        # 写入文件
        try:
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, (problem, answer) in enumerate(problems, 1):
                    f.write(f"问题{i}: {problem}\n")
                    f.write(f"答案{i}: {answer}\n\n")
            
            return f"Math problems saved successfully to: {file_path}"
        except IOError as e:
            return f"Error writing to file: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
        
    except Exception as e:
        return f"Error: {str(e)}"