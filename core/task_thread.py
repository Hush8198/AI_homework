from PyQt5.QtCore import QThread, pyqtSignal

class TaskThread(QThread):
    log_received = pyqtSignal(str)
    task_completed = pyqtSignal(str)
    
    def __init__(self, task_func, task_args=()):
        super().__init__()
        self.task_func = task_func
        self.task_args = task_args
    
    def run(self):
        try:
            def log(message):
                self.log_received.emit(message)
            
            result = self.task_func(*self.task_args, log_callback=log)
            self.task_completed.emit(result)
        except Exception as e:
            self.log_received.emit(f"[ERROR] {str(e)}")
            self.task_completed.emit("")