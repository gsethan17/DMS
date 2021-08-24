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

class alram(QDialog):
    def __init__(self, parent):
        super(alram, self).__init__(parent)
        audio_in = 'in.mp3'
        audio_out = 'out.mp3'
        alram_ui = 'alram.ui'
        uic.loadUi(alram_ui, self)
        self.setWindowModality(Qt.WindowModal)
        self.label.setStyleSheet("color: red;"
                              "border-style: solid;"
                              "border-width: 2px;"
                              "background-color: #fcbdbd;"
                              "border-color: #FA8072;"
                              "border-radius: 3px")
        parent.hide()
        self.setWindowTitle('알림')
        self.show()
        playsound(audio_out)
        time.sleep(10)
        self.close()
        parent.show()
        playsound(audio_in)
    # def alram(self):
    #     self.enter = QLabel('입력 완료', self.dialog)
    #     self.enter.setAlignment(Qt.AlignCenter)
    #     self.dialog.setWindowModality(2)
    #     self.dialog.resize(300, 200)
    #     self.dialog.show()
    #     time.sleep(5)
    #     self.dialog.close()

class WindowClass(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.name = '미정'
        self.filename = self.name + '.csv'
        if os.path.exists(self.filename):
            print(f'{self.name} 기록 시작합니다')
        else:
            df = pd.DataFrame(columns=['time', 'driver', 'status', 'km'])
            df.to_csv(self.filename, index=False)
            print(f'{self.filename} 파일을 생성하였습니다')
        self.df = pd.read_csv(f'{self.name}.csv', encoding='utf-8-sig')
        try:
            self.km = self.df.iloc[-1]['km']
        except:
            self.km = 0
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

    def tem(self):
        self.c.test.emit()

    def btn1(self):
        raw_data = [(time.time(), self.name, 1, self.km)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

    def btn2(self):
        raw_data = [(time.time(), self.name, 2, self.km)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

    def btn3(self):
        raw_data = [(time.time(), self.name, 3, self.km)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()