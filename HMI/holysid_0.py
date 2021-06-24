import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from gtts import gTTS
from playsound import playsound
import xml.etree.ElementTree as ET
import pandas as pd
import time
import os

form_class = uic.loadUiType("status.ui")[0]

ui = open('status.ui', 'rt', encoding='UTF8')
tree = ET.parse(ui)
root = tree.getroot()

class WindowClass(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.name = '류정환'
        self.filename = self.name + '.csv'
        if os.path.exists(self.filename):
            print(f'{self.name} 기록 시작합니다')
        else:
            df = pd.DataFrame(columns=['time', 'driver', 'status'])
            df.to_csv(self.filename, index=False)
            print(f'{self.filename} 파일을 생성하였습니다')
        self.df = pd.read_csv(f'{self.name}.csv', encoding='utf-8-sig')
        self.setWindowTitle('기록중')
        self.setWindowModality(2)
        self.show()
        self.lbl_driver.setText(self.name)
        pixmap = QPixmap('tempsnip.png')
        self.lbl_image.setPixmap(QPixmap(pixmap))
        self.btn_1.clicked.connect(self.btn1)
        self.btn_2.clicked.connect(self.btn2)
        self.btn_3.clicked.connect(self.btn3)

        self.lbl_driver.setStyleSheet("color: black;"
                                      "border-style: solid;"
                                      "border-width: 2px;"
                                      "background-color: #87CEFA;"
                                      "border-color: #1E90FF;"
                                      "border-radius: 3px")
        self.btn_1.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #f7453b;"
                                 "border-color: #f7453b;"
                                 "border-radius: 3px")
        self.btn_2.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #fcc82b;"
                                 "border-color: #fcc82b;"
                                 "border-radius: 3px")
        self.btn_3.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #4a7ac2;"
                                 "border-color: #4a7ac2;"
                                 "border-radius: 3px")

    def btn1(self):
        raw_data = [(time.time(), self.name, 1)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def btn2(self):
        raw_data = [(time.time(), self.name, 2)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def btn3(self):
        raw_data = [(time.time(), self.name, 3)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def alram(self):
        audio_in = 'in.mp3'
        audio_out = 'out.mp3'
        self.hide()
        self.setWindowTitle('알림')
        playsound(audio_out)
        time.sleep(1)
        playsound(audio_in)
        self.show()

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()