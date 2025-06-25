from openai import OpenAI
from core.manager_agent import ManagerAgent
import os
from dotenv import load_dotenv
from core.agent import message_initial

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
agent = ManagerAgent(client)

# 示例：动态生成工具并执行
task = "输出 https://xiaoce.fun 最新测试的名称"
response, _ = agent.process_task(task)
print(response)