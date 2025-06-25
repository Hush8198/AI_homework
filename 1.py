def execute_create_file(input_param):
    import os
    
    try:
        if not isinstance(input_param, str):
            return "Error: Input parameter must be a string"
            
        if input_param != "2.txt":
            return "Error: This function only creates '2.txt' file"
            
        file_path = os.path.join(os.getcwd(), input_param)
        
        if os.path.exists(file_path):
            return f"Error: File '{input_param}' already exists"
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')
            
        return f"Successfully created file: {input_param}"
        
    except PermissionError:
        return "Error: Permission denied when trying to create file"
    except OSError as e:
        return f"Error: OS error occurred - {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"
    
execute_create_file("2.txt")