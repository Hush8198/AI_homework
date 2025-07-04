from typing import List, Dict, Tuple
import json
from openai import OpenAI
from core.agent import send_message, message_initial
from datetime import datetime
from core.manager_agent import ManagerAgent
from core.safe import task_checker

class TaskAnalyzer:
    def __init__(self, llm_client: OpenAI, log_callback=None, stream_handler=None):
        """初始化分析器，复用agent.py的日志系统"""
        self.llm = llm_client
        self.blog_file = open("blogs/blog.txt", "a", encoding="utf-8")
        self.task_history = []  # 新增：记录任务执行历史
        self.log_callback = log_callback
        self.trail = 2
        self.stream_handler = stream_handler

    def _log_step(self, message: str):
        """复用agent.py的日志格式"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.blog_file.write(f"\n{timestamp}:\n<system> {message}\n")

    def analyze_and_execute(self, complex_task: str, log_callback=None, stream_handler=None):
        """分步执行：动态规划下一步 -> 执行子任务 -> 汇总结果"""
        def log(message):
            if log_callback:
                log_callback(message)
            self._log_step(message)
        
        # 初始化任务
        log(f"[CHECK] 开始进行任务安全检查")
        safe, err = self.safe_check(complex_task)
        if not safe:
            log(err)
            return err
        else:
            log(f"[TASK] 开始处理复杂任务: {complex_task}")
            results = []
            manager = ManagerAgent(self.llm, log, self.stream_handler or stream_handler)
            messages = message_initial("系统正在处理复杂任务")
        
        # 动态规划执行流程
        while True:
            log(f"开始规划下一步任务")
            # 步骤1：规划下一步任务

            trail = self.trail
            next_task = self._plan_next_step(complex_task, messages)
            if next_task:
                log(f"[NEXT STEP] 预测步骤为：{next_task['description'][:100]}...")
                log(f"[CHECK] 开始进行子任务安全检查")
                safe, err = self.safe_check(f"{next_task['description'][:100]}")
            while (next_task is None or not safe) and trail:
                next_task = self._plan_next_step(complex_task, messages)
                if next_task:
                    log(f"[NEXT STEP] 预测步骤为：{next_task['description'][:100]}...")
                    log(f"[CHECK] 开始进行子任务安全检查")
                    safe, err = self.safe_check(f"{next_task['description'][:100]}")
                trail -= 1
            if next_task is None or not safe:
                err = f"连续预测下一步骤{self.trail+1}次返回空或不安全，终止该任务"
                log(err)
                return err
                
            if next_task["step_num"] == "-1":  # 终止条件
                log(f"准备结束")
                break
                    
            # 步骤2：执行子任务
            log(f"执行步骤 {next_task['step_num']}: {next_task['description'][:50]}...")
            result, new_messages = self._execute_subtask(next_task["description"], complex_task, manager, messages)
            
            # 更新上下文
            messages += new_messages
            results.append({
                "step": next_task["step_num"],
                "description": next_task["description"],
                "result": result.content if hasattr(result, 'content') else str(result)
            })
            self.task_history.append(next_task["description"])  # 记录历史

        # 步骤3：汇总结果
        log("[CONC] 开始汇总最终结果")
        final_result = self._summarize_results(complex_task, results)
        
        # 正确处理final_result的长度检查
        result_content = final_result.content if hasattr(final_result, 'content') else str(final_result)
        self.blog_file.write(f"<system> 任务完成，结果长度: {len(result_content)}\n")
        return result_content

    def _plan_next_step(self, task: str, messages: List[Dict]) -> Dict:
        """智能规划下一步任务，考虑历史记录和当前上下文"""
        prompt = f"""作为任务规划专家，你需要根据以下信息决定下一步：
        
        当前状态:
        - 主任务: {task}
        - 已下达步骤: {json.dumps(self.task_history, ensure_ascii=False) if self.task_history else "无"}
        - 最新上下文: {str(messages[-3:-1]) + '...' if messages else "无"}
        
        请分析并返回JSON格式的下一步计划，你需要仔细观察历史消息确保没有遗漏步骤和已完成步骤:
        {{
            "step_num": "步骤编号（新步骤从1开始，后续递增，-1表示任务结束）",
            "description": "具体任务描述",
            "rationale": "选择此步骤的理由"
        }}
        
        要求:
        1. 你的下一步任务将直接交给LLM工作，请确保它足够明确且能够使用Python工具执行，避免不必要或无意义的步骤
        2. 强调未完成的行动，已完成的行动需弱化避免误判，例如获得的信息记为已获得的或直接将信息给出提供给LLM
        2. 尽量理解用户需求，如果需求不明确可以直接将step_num设置为-1
        3. 如果一些子任务无法完成，应当选择其他方式。如果过于复杂如Python不可能实现，也可直接将step_num设置为-1
        4. 如果你发现代码有问题，请显式写出“重新生成一份代码，...”
        5. 需要获取信息时，请明确需要用户端信息、网络信息或生成内容
        6. 只有所有必要步骤完成后返回step_num=-1，你必须仔细检查最新上下文观察是否真的完成了所有已下达步骤
        
        示例（数据收集任务）:
        输入: 主任务"收集A公司竞品分析报告"
        已完成: ["在网页搜索A公司主页", "根据A公司主页识别A公司主要竞品"]
        应返回: {{
            "step_num": "3",
            "description": "根据A公司主页收集竞品的市场份额和产品特性数据",
            "rationale": "已完成竞品识别，现在需要具体数据"
        }}"""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是高级任务规划专家，擅长分解复杂任务并保持上下文连贯") + messages,
            mode=0  # JSON模式
        )
        return response

    def _execute_subtask(self, subtask: str,complex_task: str, manager: ManagerAgent, messages: List[Dict]):
        """执行子任务并返回结果和更新后的消息"""
        manager.stream_handler = self.stream_handler
        return manager.process_task(subtask, complex_task, messages)

    def _summarize_results(self, original_task: str, results: List[Dict]) -> str:
        """汇总结果并生成最终报告"""
        prompt = f"""请整合任务执行结果：
        
        原始任务: {original_task}
        执行步骤:
        {json.dumps(results, ensure_ascii=False, indent=2)}
        
        要求:
        1. 如果任务要求输出，按照任务要求直接输出，无需其它内容
        2. 如果任务是执行任务，依次给出执行结果、过程和评价
        3. 使用Markdown形式输出
        4. 如果是其他类型任务，可自由发挥，但尽量简短"""
        
        response, _ = send_message(
            clients=("deepseek-chat", self.llm),
            user_input=prompt,
            messages=message_initial("你是高级报告生成专家"),
            mode=2 if self.stream_handler else 1,  # 自动切换模式
            stream_handler=self.stream_handler
        )
        return response.content if hasattr(response, 'content') else str(response)

    def safe_check(self, task):
        safe_response = task_checker(self.llm, task)
        trail = self.trail
        while safe_response is None and trail:
            safe_response = task_checker(self.llm, task)
            trail -= 1
        if safe_response is None:
            err = f"安全检查连续{self.trail+1}次返回空，终止该任务"
            return False, err
        if safe_response["safety"] == "Unsafe":
            self._log_step(str(safe_response))
            err = f"任务未能通过安全检查：{safe_response["message"]}"
            return False, err
        return True, "通过安全检查"
        
    
    def runner(complex_task):
        from dotenv import load_dotenv
        import os
        load_dotenv()

        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        analyzer = TaskAnalyzer(client)
        print("执行结果:", analyzer.analyze_and_execute(complex_task))