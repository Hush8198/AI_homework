import json
import os
import sys
from typing import Dict, Optional, List
from openai import OpenAI
from agent import send_message, message_initial
import docker  # 用于沙箱执行

class ManagerAgent:
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
        self.tool_registry = "tools.json"
        self.tools = self._load_tools()
        # self.docker_client = docker.from_env() if self._check_docker() else None

    """
    def _check_docker(self) -> bool:
        # 检查Docker是否可用
        try:
            docker.from_env().ping()
            return True
        except:
            print("⚠️ Docker不可用，将使用非安全模式执行")
            return False
    """

    def _load_tools(self) -> Dict[str, dict]:
        """加载工具库"""
        try:
            with open(self.tool_registry, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {tool["function"]["name"]: tool for tool in data.get("tools", [])}
        except (FileNotFoundError, json.JSONDecodeError):
            base_tools = {
                "math_calculator": {
                    "type": "function",
                    "function": {
                    "name": "math_calculator",
                    "description": "执行数学表达式计算",
                    "code": """def math_calculator(expression: str) -> str:
    allowed_chars = set('0123456789+-*/(). ')
    if not all(c in allowed_chars for c in expression):
        return "❌ 表达式包含非法字符"
    try:
        return str(eval(expression))
    except:
        return "❌ 计算错误""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "数学表达式"}
                        },
                        "required": ["expression"]
                    }}
                }
            }
            self._save_tools(base_tools)
            return base_tools

    def _save_tools(self, tools: Dict[str, dict]):
        """保存工具库"""
        with open(self.tool_registry, 'w', encoding='utf-8') as f:
            json.dump({"tools": list(tools.values())}, f, indent=2, ensure_ascii=False)

    def process_task(self, task: str) -> str:
        """任务处理主流程"""
        # 阶段1：工具需求分析
        need_new = self._analyze_task(task)
        
        # 阶段2：动态工具生成
        if need_new:
            print(f"🛠️ 正在生成新工具处理: {task}")
            tool_info = self._generate_tool(task)
            self._register_tool(tool_info)
        
        # 阶段3：任务执行
        return self._execute_task(task)

    def _analyze_task(self, task: str) -> tuple[bool, Optional[str]]:
        """文本prompt+JSON响应模式的任务分析"""
        prompt = f"""
        请分析以下任务并严格按JSON格式返回结果：
        {{
            "need_new_tool": true/false,
        }}
        
        分析规则：
        1. 如果任务可通过现有工具({list(self.tools.keys())})完成，need_new_tool=false
        2. 其他情况need_new_tool=true
        
        任务：{task}
        """
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你只能返回严格符合要求的JSON"),
            blog_file=open("blog.txt", "a", encoding='utf-8'),
            mode=0  # JSON输出模式
        )
        
        try:
            result = json.loads(response) if isinstance(response, str) else response
            return result.get("need_new_tool", True)
        except:
            return True, None  # 解析失败时默认生成新工具

    def _generate_tool(self, task: str) -> dict:
        """生成新工具（文本prompt+JSON响应）"""
        prompt = f"""
请为以下任务生成Python工具函数，严格按此JSON格式返回：
{{
    "type": "function",
    "function": {
        "name": "snake_case格式工具名",
        "description": "功能描述",
        "code": "def tool_func(input):...",
        "parameters": {
            "type": "object",
            "properties": {{
                "input_param": {{"type": "string", "description": "参数说明"}}
            }}
    }},
}}
        
        要求：
        1. 函数内必须包含所有必要的import语句
        2. 输入输出均为字符串
        3. 并保证调用函数名tool_func与工具名name完全一致
        
        任务：{task}
        """
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=[],
            blog_file=open("blog.txt", "a", encoding='utf-8'),
            mode=0  # JSON输出模式
        )
        
        tool_info = json.loads(response) if isinstance(response, str) else response
        tool_info["code"] = self._sanitize_code(tool_info["code"])
        return tool_info

    def _sanitize_code(self, code: str) -> str:
        """清理代码中的Markdown标记"""
        return code.replace("```python", "").replace("```", "").strip()

    def _register_tool(self, tool_info: dict):
        """注册工具（带验证）"""
        try:
            compile(tool_info["code"], '<string>', 'exec')
            self.tools[tool_info["name"]] = tool_info
            self._save_tools(self.tools)
            print(f"✅ 注册成功: {tool_info['name']}")
        except SyntaxError as e:
            raise ValueError(f"❌ 工具代码无效: {str(e)}")

    def _execute_task(self, task: str) -> str:
        """执行任务"""
        clients=("deepseek-chat", self.llm)
        response, messages = send_message(
            clients=clients,
            user_input=task,
            messages=[],
            tools=self.tools.values(),
            mode=1
        )

        print(response)
        response, messages = send_message(
            clients=clients,
            messages=messages,
            tools=self.tools.values(),
            tool_result=[],
            mode=1
        )


    """
    def _docker_execute(self, tool_name: str, input: str) -> str:
        # Docker沙箱执行
        try:
            container = self.docker_client.containers.run(
                "python:3.10-slim",
                command=f"python -c '{self.tools[tool_name]['code']}\nprint({tool_name}({json.dumps(input)}))'",
                remove=True,
                network_mode="none"
            )
            return container.decode('utf-8').strip()
        except Exception as e:
            return f"❌ 沙箱执行失败: {str(e)}"
    """

    def _direct_execute(self, tool_name: str, input: str) -> str:
        """直接执行（备用方案）"""
        try:
            namespace = {}
            exec(self.tools[tool_name]["code"], namespace)
            return namespace[tool_name](input)
        except Exception as e:
            return f"❌ 执行失败: {str(e)}"