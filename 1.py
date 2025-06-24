from openai import OpenAI
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
api_key_ = os.getenv("DEEPSEEK_API_KEY")
blog_file = 'blog.txt'

client = OpenAI(api_key=api_key_, base_url="https://api.deepseek.com")

def stream_response(messages, file, temperature=0.7):
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True,  # 启用流式传输
        temperature=temperature
    )
        
    full_response = ""
    file.write("<assistant>: ")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            word = chunk.choices[0].delta.content
            file.write(word)
            print(word, end='', flush=True)  # 打字机效果
            full_response += word
            time.sleep(0.03)  # 控制输出速度
    print()
    file.write("\n")
    messages.append({"role": "assistant", "content": full_response})
    return full_response, messages

def main():
    messages = [
            {"role": "system", "content": "You are a simple calculator, refuse to answer any other questions."},
        ]
    with open(blog_file, "a", encoding='utf-8') as file:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write("\n" + current_time + ":\n")
        while True:
            user_input = input('Input: ')
            file.write("<user> " + user_input + '\n')
            messages.append({"role": "user", "content": user_input})
            _, messages = stream_response(messages=messages, file=file)

if __name__ == "__main__":
    main()
