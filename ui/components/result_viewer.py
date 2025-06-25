from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QTextBrowser, 
                            QTabWidget, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt

class ResultViewer(QGroupBox):
    def __init__(self):
        super().__init__("执行结果")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        # 结果展示标签页
        self.result_browser = QTextBrowser()
        self.result_browser.setOpenExternalLinks(True)
        self.tab_widget.addTab(self.result_browser, "结果汇总")
        
        # 原始数据标签页
        self.raw_data_browser = QTextBrowser()
        self.tab_widget.addTab(self.raw_data_browser, "原始数据")
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存结果")
        self.copy_btn = QPushButton("复制结果")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.copy_btn)
        
        layout.addWidget(self.tab_widget)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)