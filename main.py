import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 初始化LLM客户端
    from openai import OpenAI
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    llm_client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    window = MainWindow()
    window.llm_client = llm_client  # 传递LLM客户端
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()