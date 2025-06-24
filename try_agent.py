from manager_agent import ManagerAgent
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

agent = ManagerAgent(client)

# 测试用例
print(agent.process_task("计算3+5*2"))          # 使用预装计算器
print(agent.process_task("提取https://example.com的标题"))  # 触发工具生成
print(agent.process_task("统计PDF页数"))        # 触发工具生成