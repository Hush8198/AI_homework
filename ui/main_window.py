from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QStatusBar)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alita - AI任务管理系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 1. 先初始化所有UI组件
        self._init_ui_components()
        
        # 2. 然后连接信号
        self._connect_signals()
        
        # 3. 其他初始化
        self.analyzer = None
        self.llm_client = None  # 会在main.py中设置

    def _init_ui_components(self):
        """初始化所有UI组件"""
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 左右分屏
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板(任务输入和历史)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 右侧面板(执行和结果)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(5, 5, 5, 5)
        
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 初始化具体组件
        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧面板"""
        from .components.task_input import TaskInput
        from .components.history_panel import HistoryPanel
        
        self.task_input = TaskInput()  # 先创建task_input
        self.history_panel = HistoryPanel()
        
        self.left_layout.addWidget(self.task_input, 1)
        self.left_layout.addWidget(self.history_panel, 2)

    def _init_right_panel(self):
        """初始化右侧面板"""
        from .components.progress_panel import ProgressPanel
        from .components.result_viewer import ResultViewer
        
        self.progress_panel = ProgressPanel()
        self.result_viewer = ResultViewer()
        
        self.right_layout.addWidget(self.progress_panel, 1)
        self.right_layout.addWidget(self.result_viewer, 2)

    def _connect_signals(self):
        """连接所有信号和槽"""
        self.task_input.execute_signal.connect(self.execute_task)

    def execute_task(self, task_description):
        """执行任务的槽函数"""
        from core.analyze import TaskAnalyzer
        from ui.components.progress_panel import ProgressPanel
        if not self.analyzer:
            # 将progress_panel传递给Agent
            self.analyzer = TaskAnalyzer(
                self.llm_client, 
                progress_panel=self.progress_panel
            )
        try:
            # 更新UI状态
            self.status_bar.showMessage("任务执行中...")
            
            # 初始化任务分析器
            analyzer = TaskAnalyzer(self.llm_client)  # 需要提前初始化llm_client
            
            # 执行任务
            result = analyzer.analyze_and_execute(task_description)
            
            # 显示结果
            self.result_viewer.result_browser.setMarkdown(result)
            self.status_bar.showMessage("任务完成", 3000)
            
            # 添加到历史记录
            self.history_panel.add_history(task_description)
            
        except Exception as e:
            self.status_bar.showMessage(f"错误: {str(e)}", 5000)
            self.result_viewer.result_browser.setPlainText(f"执行出错:\n{str(e)}")