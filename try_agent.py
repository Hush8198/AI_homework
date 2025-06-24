from openai import OpenAI
from manager_agent import ManagerAgent
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

agent = ManagerAgent(client)

# 处理任务（会自动选择或生成工具）
print(agent.process_task("计算3+5*2")) 
print(agent.process_task("输出 https://xiaoce.fun 的标题")) 