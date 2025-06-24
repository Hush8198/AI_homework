import json
from typing import Dict, Optional
from openai import OpenAI
from agent import send_message, message_initial
from datetime import datetime

class ManagerAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.tool_registry = "tools.json"
        self.tools = self._load_tools()  # 加载工具库
    
    def _load_tools(self) -> Dict[str, str]:
        """加载工具库（新增注释说明）"""
        try:
            with open(self.tool_registry, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"math_calculator": "def calculate(expr): return str(eval(expr))"}
    
    def process_task(self, task: str) -> str:
        """处理用户任务的主入口"""
        if self._need_new_tool(task):
            print("检测到需要新工具...")
            tool_name, tool_code = self._generate_tool(task)
            self._register_tool(tool_name, tool_code)
        
        return self._execute_task(task)
    
    def _need_new_tool(self, task: str) -> bool:
        """改进版工具需求判断"""
        prompt = f"""
        [工具需求分析规则]
        1. 如果任务可通过现有工具（{list(self.tools.keys())}）完成，回答N
        2. 如需以下操作，回答Y：
           - 网络请求（如网页抓取）
           - 文件处理（如PDF/Excel）
           - 复杂计算（如统计建模）
        任务：{task}
        回答（Y/N）:"""
        
        system_prompt = f"""
        你是一个单字符回答机，只能根据用户需求回复一个单字符如Y或N
        """
        messages = message_initial(system_prompt)
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=messages,
            blog_file=open("blog.txt", "a", encoding='utf-8'),
            temperature=0  # 确保确定性
        )
        return "Y" in response.strip().upper()

    def _generate_tool(self, task: str) -> tuple[str, str]:
        """生成新工具（极简版）"""
        prompt = f"""
        请生成一个Python函数来处理以下任务：
        - 函数名：snake_case格式，体现功能
        - 输入：单个字符串参数
        - 输出：字符串结果
        - 必须包含异常处理
        
        任务描述：{task}
        只需返回函数代码，不要解释："""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=[],
            blog_file=open("blog.txt", "a", encoding='utf-8'),
            temperature=0.3  # 适度创造性
        )
        
        # 提取函数名（如：def extract_title(url) → "extract_title"）
        tool_name = response.split("def ")[1].split("(")[0].strip()
        return tool_name, response
    
    def _register_tool(self, name: str, code: str):
        """注册工具到本地JSON文件"""
        self.tools[name] = code
        with open(self.tool_registry, 'w') as f:
            json.dump(self.tools, f, indent=2)
        print(f"✅ 工具注册成功: {name}")
    
    def _execute_task(self, task: str) -> str:
        """安全执行任务（暂用eval，后续需改沙箱）"""
        # 让LLM选择最合适的工具
        prompt = f"""
        现有工具：{list(self.tools.keys())}
        请选择最适合处理该任务的工具名：
        任务：{task}
        只需返回工具名："""
        
        tool_name, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=[],
            blog_file=open("blog.txt", "a", encoding='utf-8'),
            temperature=0
        )
        tool_name = tool_name.strip()
        
        # 动态执行工具代码（实际项目应用沙箱！）
        try:
            namespace = {}
            exec(self.tools[tool_name], namespace)
            return namespace[tool_name](task)
        except Exception as e:
            return f"❌ 工具执行失败: {str(e)}"