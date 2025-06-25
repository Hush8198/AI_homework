from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit

class LogPanel(QGroupBox):
    def __init__(self):
        super().__init__("执行日志")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        self.setLayout(layout)
    
    def add_log(self, message: str):
        self.log_display.append(message)
        # 自动滚动到底部
        self.log_display.ensureCursorVisible()
    
    def clear_logs(self):
        self.log_display.clear()