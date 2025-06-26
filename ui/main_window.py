from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QStatusBar, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
from core.task_thread import TaskThread
from core.analyze import TaskAnalyzer
from ui.components.log_panel import LogPanel  # 新增导入
from core.agent import StreamHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务执行系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化UI
        self._init_ui_components()
        
        # 初始化任务系统
        self.llm_client = None  # 会在main.py中设置
        self.task_thread = None
        self.analyzer = None

        self.stream_handler = StreamHandler()
        self.stream_handler.stream_received.connect(self._handle_stream_chunk)
        self.stream_handler.final_received.connect(self._handle_final_result)
        
        # 连接信号
        self._connect_signals()

    def _init_ui_components(self):
        """初始化所有UI组件"""
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 左右分屏
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板(任务输入和历史)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 右侧面板(日志和结果)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 初始化组件
        from ui.components.task_input import TaskInput
        from ui.components.history_panel import HistoryPanel
        from ui.components.result_viewer import ResultViewer
        
        self.task_input = TaskInput()
        self.history_panel = HistoryPanel()
        self.log_panel = LogPanel()  # 替换原来的progress_panel
        self.result_viewer = ResultViewer()
        
        # 添加到布局
        left_layout.addWidget(self.task_input)
        left_layout.addWidget(self.history_panel)
        
        right_layout.addWidget(self.log_panel)
        right_layout.addWidget(self.result_viewer)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        """连接信号和槽"""
        self.task_input.execute_signal.connect(self.execute_task)

    def execute_task(self, task_description: str):
        """执行任务"""
        if self.task_thread and self.task_thread.isRunning():
            self.log_panel.add_log("[WARN] 请等待当前任务完成")
            return
            
        # 初始化分析器
        if not self.analyzer:
                self.analyzer = TaskAnalyzer(
                    self.llm_client, 
                    log_callback=self.log_panel.add_log,
                    stream_handler=self.stream_handler
                )
        
        # 准备执行
        self.log_panel.clear_logs()
        self.log_panel.add_log(f"[INFO] 开始执行任务: {task_description}")
        self.task_input.setEnabled(False)
        
        # 创建并启动线程，传递流式处理器
        self.task_thread = TaskThread(
            task_func=self.analyzer.analyze_and_execute,
            task_args=(task_description,),
            stream_handler=self.stream_handler  # 传递流式处理器
        )
        
        # 连接信号
        self.task_thread.log_received.connect(self.log_panel.add_log)
        self.task_thread.task_completed.connect(self._on_task_completed)
        self.task_thread.start()

    def _handle_stream_chunk(self, chunk):
        """流式片段只显示在结果视图"""
        self.result_viewer.append(chunk)
        # 可选：自动滚动到底部
        QApplication.processEvents()  # 确保UI及时更新
    
    def _handle_final_result(self, result):
        """最终结果格式化显示"""
        self.result_viewer.set_result(result)
        self.log_panel.add_log("[INFO] 生成完成")

    def _on_task_completed(self, result: str):
        """任务完成处理"""
        self.result_viewer.set_result(result)
        self.task_input.setEnabled(True)
        self.status_bar.showMessage("任务完成", 3000)
        self.task_thread = None

    def _on_task_failed(self, error_msg: str):
        """任务失败处理"""
        self.result_viewer.set_error(error_msg)
        self.task_input.setEnabled(True)
        self.status_bar.showMessage("任务失败", 5000)
        self.task_thread = None