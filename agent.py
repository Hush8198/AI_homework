from openai import OpenAI
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def client_maker(model_name="deepseek-chat"):
    load_dotenv()
    client = None
    if model_name == "deepseek-chat":
        api_key_ = os.getenv("DEEPSEEK_API_KEY")
        client = OpenAI(api_key=api_key_, base_url="https://api.deepseek.com")
    return (model_name, client)

def stream_response(clients, messages, blog_file, temperature):
    model_name, client = clients
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,  # 启用流式传输
        temperature=temperature
    )
        
    full_response = ""
    blog_file.write(f"<assistant>({model_name}): ")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            word = chunk.choices[0].delta.content
            blog_file.write(word)
            print(word, end='', flush=True)
            full_response += word
            time.sleep(0.03)
    print()
    blog_file.write("\n")
    messages.append({"role": "assistant", "content": full_response})
    return full_response, messages

def send_message(clients, user_input, messages, blog_file, temperature=0.7):
    """
    发送讯息
    clients: 模型，结构为(model_name, client)
    user_input: 发送的信息
    messages: 历史信息
    blog_file: 日志
    temperature=0.7: 温度
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    blog_file.write("\n" + current_time + ":\n")
    blog_file.write("<user> " + user_input + '\n')
    messages.append({"role": "user", "content": user_input})
    response, messages = stream_response(clients, messages, blog_file, temperature)
    return response, messages

def message_initial(prompt):
    """
    初始化信息
    """
    messages = [
            {"role": "system", "content": prompt},
        ]
    
    return messages