from openai import OpenAI
import time
from datetime import datetime
import json
import os
from dotenv import load_dotenv

def client_maker(model_name="deepseek-chat"):
    load_dotenv()
    client = None
    if model_name == "deepseek-chat":
        api_key_ = os.getenv("DEEPSEEK_API_KEY")
        client = OpenAI(api_key=api_key_, base_url="https://api.deepseek.com")
    return (model_name, client)

def direct_response(clients, messages, blog_file, tools, temperature):
    model_name, client = clients
    if tools:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )
    else:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
    full_response = response.choices[0].message
    # blog_file.write(f'<assistant><direct mode>({model_name}): ' + full_response + '\n')
    print(full_response)
    return full_response

def stream_response(clients, messages, blog_file, temperature):
    model_name, client = clients
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,  # 启用流式传输
        temperature=temperature
    )
        
    full_response = ""
    blog_file.write(f"<assistant><stream mode>({model_name}): ")
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

def json_response(clients, messages, blog_file):
    model_name, client = clients
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"}
    )
    full_response = response.choices[0].message.content
    try:
        json_data = json.loads(full_response)  # 修正：使用json.loads解析字符串
        blog_file.write(f'<assistant>({model_name}): {json.dumps(json_data, ensure_ascii=False)}\n')
        return json_data
    except json.JSONDecodeError:
        blog_file.write(f'<assistant>({model_name}): [INVALID JSON] {full_response}\n')
        return {"error": "Invalid JSON response"}

def send_message(clients, messages, blog_file=open("blog.txt", "a", encoding='utf-8'), user_input="", tools=[], tool_result=[], temperature=0.3, mode=0):
    """
    发送讯息
    clients: 模型，结构为(model_name, client)
    messages: 历史信息
    blog_file: 日志
    user_input: 发送的信息
    tools: 工具合集
    tool_result: 工具返回的结果
    temperature=0.7: 温度
    mode=0,1,2: mode=0 json输出, mode=1 直接输出, mode=2 流式输出
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    blog_file.write("\n" + current_time + ":\n")
    if not tool_result:
        blog_file.write("<user> " + user_input + '\n')
        messages.append({"role": "user", "content": user_input})
    else:
        blog_file.write("<tool> " + tool_result + '\n')
        for tool_r in tool_result:
            messages.append({"role": "tool", "tool_call_id": tool_r[0], "content": tool_r[1]})
        
    if mode == 0:
        response = json_response(clients, messages, blog_file)
    elif mode == 1:
        response, messages = direct_response(clients, messages, blog_file, tools, temperature)
    else:
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