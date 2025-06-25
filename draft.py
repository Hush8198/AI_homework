# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

app = QApplication([])
window = QWidget()

main_layout = QVBoxLayout()
btn_layout = QHBoxLayout()

btn1 = QPushButton("按钮1")
btn2 = QPushButton("按钮2")

btn_layout.addWidget(btn1)
btn_layout.addWidget(btn2)
main_layout.addLayout(btn_layout)

window.setLayout(main_layout)
window.show()
app.exec_()