from openai import OpenAI
from manager_agent import ManagerAgent
import os
from dotenv import load_dotenv
from agent import message_initial

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

agent = ManagerAgent(client)
messages = message_initial("""你是一个智能助手，能够通过工具调用获取信息。当用户请求需要工具完成的任务时严格遵守：
1. 你已经调用了合适工具获取信息，messages中ChatCompletionMessage就是使用工具的记录
2. 你已经借助了工具返回的结果完成任务，messages中'role' = 'tool'的'content'内容就是工具返回的结果
3. 不要声明自己无法完成任务，应当结合工具返回的结果做答
4. 利用工具返回的信息，此外若无需推断不得自行推断
""")
# 处理任务（会自动选择或生成工具）
tasks = ['计算12-9-10-9*7的结果', '给出 https://pku.instructure.com/login/canvas 的标题', '在当前目录下创建2.txt文件']
for task in tasks:
    response, messages = agent.process_task(task, messages)
    print(response)