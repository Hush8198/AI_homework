from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QGroupBox)
from PyQt5.QtCore import pyqtSignal

class TaskInput(QGroupBox):
    execute_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__("任务输入")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("输入您的复杂任务:")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("例如: 随机生成10个正整数存储在E:/example.txt中")
        self.text_edit.setMinimumHeight(100)
        
        self.submit_btn = QPushButton("执行任务")
        self.submit_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.submit_btn)
        
        self.setLayout(layout)
        self.submit_btn.clicked.connect(self._on_submit)
    
    def _on_submit(self):
        task_text = self.text_edit.toPlainText().strip()
        if task_text:
            # 发射信号时传递任务内容和回调占位符
            self.execute_signal.emit(task_text)