import json
import os
import importlib.util
from typing import Dict, List, Callable
from openai import OpenAI
from core.agent import send_message, message_initial
import re
import copy
from web_agent.web_agent import WebAgent, WebTools

class ManagerAgent:
    def __init__(self, llm_client: OpenAI, progress_panel=None):
        self.llm = llm_client
        self.web_agent = WebAgent()  # 新增Web Agent实例
        self.tool_registry = "tools.json"  # 仍然保留工具定义的JSON文件
        self.tools_dir = "tools"  # 工具代码存放目录
        self.tools = self._load_tools()
        self.tool_implementations = self._load_implementations()
        self.progress_panel = progress_panel
        
        # 确保工具目录存在
        os.makedirs(self.tools_dir, exist_ok=True)
    
    def _clean_code(self, code: str) -> str:
        """清理代码中的Markdown标记、多余空格和转义字符"""
        # 移除代码块标记
        code = re.sub(r'```(python)?', '', code)
        # 移除前后空白
        code = code.strip()
        # 确保函数定义正确
        if not code.startswith('def '):
            # 尝试提取第一个函数定义
            match = re.search(r'def\s+\w+\(.*?\)\s*:', code)
            if match:
                code = code[match.start():]
        return code

    def _load_tools(self) -> Dict[str, dict]:
        """加载工具定义"""
        try:
            with open(self.tool_registry, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {tool["function"]["name"]: tool for tool in data.get("tools", [])}
        except (FileNotFoundError, json.JSONDecodeError):
            return self._init_default_tools()

    def _load_implementations(self) -> Dict[str, Callable]:
        """动态加载工具实现"""
        implementations = {}
        for tool_name in self.tools.keys():
            try:
                # 从单独的Python文件加载工具
                module_path = os.path.join(self.tools_dir, f"{tool_name}.py")
                if not os.path.exists(module_path):
                    continue
                
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(tool_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 获取执行函数
                func_name = f"execute_{tool_name}"
                if hasattr(module, func_name):
                    implementations[tool_name] = getattr(module, func_name)
                else:
                    print(f"工具{tool_name}缺少执行函数{func_name}")
            except Exception as e:
                print(f"加载工具{tool_name}失败: {str(e)}")
        return implementations

    def _init_default_tools(self) -> Dict[str, dict]:
        """初始化默认工具定义"""
        default_tools = {}
        self._save_tools(default_tools)
        return default_tools
    
    def _save_tools(self, tools: Dict[str, dict]):
        """保存工具定义"""
        with open(self.tool_registry, 'w', encoding='utf-8') as f:
            json.dump({"tools": list(tools.values())}, f, indent=2, ensure_ascii=False)

    def _save_tool_code(self, tool_name: str, code: str):
        """保存工具代码到单独的Python文件"""
        file_path = os.path.join(self.tools_dir, f"{tool_name}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

    def process_task(self, task: str, init_messages=None) -> str:
        """处理任务主流程"""
        if init_messages is None:
            init_messages = message_initial("""你是一个智能助手，能够通过工具调用获取信息。当用户请求需要工具完成的任务时严格遵守：
1. 你已经调用了合适工具获取信息，messages中ChatCompletionMessage就是使用工具的记录
2. 你已经借助了工具返回的结果完成任务，messages中'role' = 'tool'的'content'内容就是工具返回的结果
3. 不要声明自己无法完成任务，应当结合工具返回的结果做答
4. 直接返回工具返回的信息，如无必要不得自行推断
""")
        else:
            init_messages = copy.deepcopy(init_messages)
            
        need_new_tool = self._analyze_task(task)
        
        if need_new_tool == "Yes":
            if self.progress_panel:
                self.progress_panel.add_log_message(f"该任务需要新工具")
            tool_def = self._generate_tool(task)
            tool_code = self._generate_tool_code(tool_def)
            self._register_tool(tool_def, tool_code)
        else:
            if self.progress_panel:
                self.progress_panel.add_log_message(f"该任务无需新工具")
        
        return self._execute_task(task, init_messages, need_new_tool=='self')

    def _analyze_task(self, task: str) -> bool:
        """分析任务是否需要新工具"""
        prompt = f"""
        分析任务是否需要新工具(现有工具: {self.tools})。
        如果你自己可以完成任务或回答问题，无需任何工具或用户操作，need_new_tool字段返回"self"
        如果需要新工具或代码完成，need_new_tool字段返回"Yes"
        如果自己无法完成任务但现有工具或函数可以完成，need_new_tool字段返回"No"
        返回JSON格式: {{"need_new_tool": str, "reason": str}}
        任务: {task}"""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是一个任务分析器"),
            mode=0
        )
        return response["need_new_tool"]

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
        
        严格遵守以下代码要求：
        1. 函数名为execute_{tool_name}
        2. 在函数def的内部使用import语句而非外部
        3. 完善的错误处理，同时保证泛化性和当前任务的可完成性
        4. 输入参数应为字典，表示某个参数key输入的字符串为value，并返回字符串结果
        5. 在涉及非英文内容时谨慎地处理字符编码问题
        
        只需返回代码，无需解释："""
        
        response = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是一个Python代码生成器"),
            mode=1
        )[0]
        
        # 确保获取的是纯文本内容并清理
        code = response.content if hasattr(response, 'content') else str(response)
        return self._clean_code(code)

    def _register_tool(self, tool_def: dict, tool_code: str):
        """注册新工具"""
        tool_name = tool_def["function"]["name"]
        
        # 保存工具定义
        self.tools[tool_name] = tool_def
        self._save_tools(self.tools)
        
        # 保存工具代码到单独的文件
        self._save_tool_code(tool_name, tool_code)
        
        # 重新加载实现
        self.tool_implementations = self._load_implementations()
        
        print(f"注册成功: {tool_name}")

    def _execute_task(self, task: str, init_messages, self_solve) -> str:
        """执行任务"""
        if self_solve:
            response, messages = send_message(
                clients=("deepseek-chat", self.llm),
                user_input=task,
                messages=message_initial("你是一个智能助手，完成用户给的任务或回答用户问题"),
                mode=2
            )
        else:
            response, messages = send_message(
                clients=("deepseek-chat", self.llm),
                user_input=task,
                messages=init_messages,
                tools=list(self.tools.values()),
                mode=1
            )
        
        # 处理工具调用
        if response and hasattr(response, 'tool_calls'):
            tool_results = []
            for call in response.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                
                if tool_name in self.tool_implementations:
                    try:
                        # 执行工具并确保结果为字符串
                        result = self.tool_implementations[tool_name](args)
                        if not isinstance(result, str):
                            result = str(result)
                        # 显式编码为UTF-8，再解码为字符串，确保中文等字符正确处理
                        result = result.encode('utf-8').decode('utf-8')
                    except Exception as e:
                        result = f"工具执行错误: {str(e)}"
                else:
                    result = f"工具{tool_name}未实现"
                
                tool_results.append({
                    "tool_call_id": call.id,
                    "content": result  # 已经是正确处理编码后的字符串
                })
            
            # 发送工具结果
            final_response, messages = send_message(
                clients=("deepseek-chat", self.llm),
                messages=messages + [response],
                tool_results=tool_results,
                mode=2
            )
            return final_response, messages
        
        return response.content if hasattr(response, 'content') else str(response), messages