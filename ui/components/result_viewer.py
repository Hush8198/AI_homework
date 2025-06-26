from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextBrowser, QApplication
import time

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
    
    def append(self, text):
        """真正的逐词追加实现"""
        cursor = self.result_browser.textCursor()
        cursor.movePosition(cursor.End)
        
        # 针对流式输出的特殊处理
        if len(text) == 1:  # 单字符
            cursor.insertText(text)
            # 中文等宽字符特殊处理
            if ord(text) > 255:  
                self.result_browser.setTextCursor(cursor)
                QApplication.processEvents()
        else:  # 多字符（可能来自非流式调用）
            for char in text:  # 模拟逐字输出
                cursor.insertText(char)
                cursor.movePosition(cursor.End)
                self.result_browser.setTextCursor(cursor)
                QApplication.processEvents()
                time.sleep(0.01)  # 控制输出速度
        
        self.result_browser.ensureCursorVisible()