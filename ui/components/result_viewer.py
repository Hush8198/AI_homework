from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextBrowser

class ResultViewer(QGroupBox):
    def __init__(self):
        super().__init__("任务结果")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.result_browser = QTextBrowser()
        self.result_browser.setOpenExternalLinks(True)  # 允许打开超链接
        layout.addWidget(self.result_browser)
        self.setLayout(layout)
    
    def set_result(self, result: str):
        """设置任务结果（支持Markdown格式）"""
        self.result_browser.setMarkdown(result if result else "无结果")
    
    def set_error(self, error_msg: str):
        """设置错误信息（红色显示）"""
        self.result_browser.setHtml(f'<span style="color:red">{error_msg}</span>')
    
    def clear(self):
        """清空结果"""
        self.result_browser.clear()