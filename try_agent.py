from openai import OpenAI
from manager_agent import ManagerAgent
import os
from dotenv import load_dotenv
from agent import message_initial

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

agent = ManagerAgent(client)

# 处理任务（会自动选择或生成工具）
tasks = ['计算12-9-10-9*7的结果', '给出 https://pku.instructure.com/login/canvas 的标题', '在当前目录下创建2.txt文件']
for task in tasks:
    response, _ = agent.process_task(task)
    print(response)