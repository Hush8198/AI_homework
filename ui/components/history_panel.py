from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QListWidget, 
                            QPushButton, QInputDialog, QHBoxLayout)

class HistoryPanel(QGroupBox):
    def __init__(self):
        super().__init__("任务历史")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("加载历史")
        self.clear_btn = QPushButton("清空历史")
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addWidget(self.history_list)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def add_history(self, task_description):
        self.history_list.addItem(task_description)