from PyQt5.QtCore import QThread, pyqtSignal

class TaskThread(QThread):
    log_received = pyqtSignal(str)
    task_completed = pyqtSignal(str)
    
    def __init__(self, task_func, task_args=(), stream_handler=None):
        super().__init__()
        self.task_func = task_func
        self.task_args = task_args
        self.stream_handler = stream_handler
    
    def run(self):
        try:
            def log(message):
                self.log_received.emit(message)
            
            # 如果有流式处理器，将其传递给任务函数
            if self.stream_handler:
                result = self.task_func(*self.task_args, log_callback=log, stream_handler=self.stream_handler)
            else:
                result = self.task_func(*self.task_args, log_callback=log)
                
            self.task_completed.emit(result)
        except Exception as e:
            self.log_received.emit(f"[ERROR] {str(e)}")
            self.task_completed.emit("")