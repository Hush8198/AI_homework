from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, 
                            QTextEdit, QProgressBar)
from PyQt5.QtCore import Qt

class ProgressPanel(QGroupBox):
    def __init__(self):
        super().__init__("任务执行进度")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 总体进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        
        # 改用QTextEdit作为日志显示（支持多行、滚动）
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        self.log_display.setStyleSheet("font-family: Consolas, monospace;")
        
        layout.addWidget(QLabel("执行日志:"))
        layout.addWidget(self.log_display)
        
        self.setLayout(layout)
    
    def add_log_message(self, message: str):
        """添加新的日志消息（自动换行）"""
        # 获取当前时间
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 添加新行（使用HTML格式保持可读性）
        self.log_display.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        self.log_display.ensureCursorVisible()
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.End)
        self.log_display.setTextCursor(cursor)
    
    def update_progress(self, value: int, message: str = ""):
        """更新进度条和添加日志消息"""
        self.progress_bar.setValue(value)
        if message:
            self.add_log_message(message)