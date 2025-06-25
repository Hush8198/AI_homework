def execute_generate_math_questions(params):
    import random
    import os
    
    try:
        # Get output file name from params or use default
        output_file = params.get('output_file', 'questions.txt')
        
        # Generate 10 math questions (5 addition, 5 subtraction)
        questions = []
        for i in range(5):
            # Addition questions
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            questions.append(f"{a} + {b} = {a + b}")
            
            # Subtraction questions (ensure result is positive)
            a = random.randint(1, 100)
            b = random.randint(1, a)
            questions.append(f"{a} - {b} = {a - b}")
        
        # Shuffle the questions
        random.shuffle(questions)
        
        # Write to file with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, question in enumerate(questions, 1):
                f.write(f"Question {i}: {question.split('=')[0]}= ?\n")
                f.write(f"Answer {i}: {question.split('=')[1]}\n\n")
        
        return f"Successfully generated math questions to {output_file}"
    
    except PermissionError:
        return f"Error: Permission denied when trying to write to {output_file}"
    except OSError as e:
        return f"Error: Failed to write to file - {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"