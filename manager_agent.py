import json
import os
import importlib.util
from typing import Dict, List, Callable
from openai import OpenAI
from agent import send_message, message_initial

class ManagerAgent:
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
        self.tool_registry = "tools.json"
        self.code_registry = "codes.json"
        self.tools = self._load_tools()
        self.codes = self._load_codes()
        self.tool_implementations = self._load_implementations()

    def _load_tools(self) -> Dict[str, dict]:
        """加载工具定义"""
        try:
            with open(self.tool_registry, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {tool["function"]["name"]: tool for tool in data.get("tools", [])}
        except (FileNotFoundError, json.JSONDecodeError):
            return self._init_default_tools()

    def _load_codes(self) -> Dict[str, str]:
        """加载工具代码"""
        try:
            with open(self.code_registry, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._init_default_codes()

    def _load_implementations(self) -> Dict[str, Callable]:
        """动态加载工具实现"""
        implementations = {}
        for tool_name, code in self.codes.items():
            try:
                # 动态创建模块
                spec = importlib.util.spec_from_loader(tool_name, loader=None)
                module = importlib.util.module_from_spec(spec)
                exec(code, module.__dict__)
                
                # 获取执行函数
                if hasattr(module, f"execute_{tool_name}"):
                    implementations[tool_name] = getattr(module, f"execute_{tool_name}")
            except Exception as e:
                print(f"⚠️ 加载工具{tool_name}失败: {str(e)}")
        return implementations

    def _init_default_tools(self) -> Dict[str, dict]:
        """初始化默认工具定义"""
        default_tools = {
            "math_calculator": {
                "type": "function",
                "function": {
                    "name": "math_calculator",
                    "description": "计算数学表达式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"}
                        },
                        "required": ["expression"]
                    }
                }
            }
        }
        self._save_tools(default_tools)
        return default_tools
    
    def _init_default_codes(self) -> Dict[str, str]:
        """初始化默认工具代码"""
        default_codes = {
            "math_calculator": """\
def execute_math_calculator(expression: str) -> str:
    try:
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "❌ 表达式包含非法字符"
        return str(eval(expression))
    except Exception as e:
        return f"❌ 计算错误: {str(e)}"
"""
        }
        self._save_codes(default_codes)
        return default_codes

    def _save_tools(self, tools: Dict[str, dict]):
        """保存工具定义"""
        with open(self.tool_registry, 'w', encoding='utf-8') as f:
            json.dump({"tools": list(tools.values())}, f, indent=2, ensure_ascii=False)

    def _save_codes(self, codes: Dict[str, str]):
        """保存工具代码"""
        with open(self.code_registry, 'w', encoding='utf-8') as f:
            json.dump(codes, f, indent=2, ensure_ascii=False)

    def process_task(self, task: str) -> str:
        """处理任务主流程"""
        need_new_tool = self._analyze_task(task)
        
        if need_new_tool:
            print(f"🛠️ 需要新工具处理: {task}")
            tool_def = self._generate_tool(task)
            tool_code = self._generate_tool_code(tool_def)
            self._register_tool(tool_def, tool_code)
        
        return self._execute_task(task)

    def _analyze_task(self, task: str) -> bool:
        """分析任务是否需要新工具"""
        prompt = f"""
        分析任务是否需要新工具(现有工具: {list(self.tools.keys())})。
        返回JSON格式: {{"need_new_tool": bool, "reason": str}}
        任务: {task}"""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是一个任务分析器"),
            mode=0
        )
        print(f"分析结果: {response}")
        return response.get("need_new_tool", True)

    def _generate_tool(self, task: str) -> dict:
        """生成新工具定义"""
        prompt = f"""
        请为以下任务创建工具定义(JSON格式):
        {{
            "type": "function",
            "function": {{
                "name": "snake_case名称",
                "description": "清晰的功能描述",
                "parameters": {{
                    "type": "object",
                    "properties": {{
                        "input_param": {{"type": "string", "description": "参数说明"}}
                    }},
                    "required": ["input_param"]
                }}
            }}
        }}
        任务: {task}"""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是一个工具定义生成器"),
            mode=0
        )
        return response

    def _generate_tool_code(self, tool_def: dict) -> str:
        """生成工具实现代码"""
        tool_name = tool_def["function"]["name"]
        prompt = f"""
        请为以下工具生成Python实现代码：
        工具名称: {tool_name}
        功能描述: {tool_def["function"]["description"]}
        输入参数: {json.dumps(tool_def["function"]["parameters"], ensure_ascii=False)}
        
        代码要求：
        1. 函数名为execute_{tool_name}
        2. 包含必要的import语句
        3. 完善的错误处理
        4. 返回字符串结果
        
        只需返回代码，无需解释："""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是一个Python代码生成器"),
            mode=1
        )
        # 确保获取的是纯文本内容
        return response.content if hasattr(response, 'content') else str(response)

    def _register_tool(self, tool_def: dict, tool_code: str):
        """注册新工具"""
        tool_name = tool_def["function"]["name"]
        
        # 保存工具定义
        self.tools[tool_name] = tool_def
        self._save_tools(self.tools)
        
        # 确保tool_code是字符串
        if not isinstance(tool_code, str):
            tool_code = str(tool_code)
        
        # 保存工具代码
        self.codes[tool_name] = tool_code
        self._save_codes(self.codes)
        
        # 重新加载实现
        self.tool_implementations = self._load_implementations()
        
        print(f"✅ 注册成功: {tool_name}")

    def _execute_task(self, task: str) -> str:
        """执行任务"""
        response, messages = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=task,
            messages=[],
            tools=list(self.tools.values()),
            mode=1
        )
        
        # 处理工具调用
        if hasattr(response, 'tool_calls'):
            tool_results = []
            for call in response.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                
                if tool_name in self.tool_implementations:
                    result = self.tool_implementations[tool_name](**args)
                else:
                    result = f"⚠️ 工具{tool_name}未实现"
                
                tool_results.append({
                    "tool_call_id": call.id,
                    "content": str(result)
                })
            
            # 发送工具结果
            final_response, _ = send_message(
                clients=("deepseek-chat", self.llm),
                messages=messages + [response],
                tool_results=tool_results,
                tools=list(self.tools.values()),
                mode=1
            )
            return final_response.content
        
        return response.content if hasattr(response, 'content') else str(response)