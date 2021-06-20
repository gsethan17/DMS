import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5 import uic
from gtts import gTTS
# from pydub import AudioSegment
# from pydub.playback import play
from playsound import playsound
import xml.etree.ElementTree as ET
import pandas as pd
import time
import os

form_class = uic.loadUiType("holysid_1.ui")[0]

ui = open('holysid_1.ui', 'rt', encoding='UTF8')
tree = ET.parse(ui)
root = tree.getroot()

class HMI(QDialog):
    def __init__(self, parent):
        super(HMI, self).__init__(parent)
        HMI_ui = 'status.ui'
        uic.loadUi(HMI_ui, self)
        self.name = str(parent.cmb_drivers.currentText())
        self.df = pd.read_csv(f'{self.name}.csv', encoding='utf-8-sig')
        try:
            self.km = self.df.iloc[-1]['km']
        except:
            self.km = 0
        #self.dialog = QDialog()

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
        raw_data = [(time.time(), self.name, 1, self.km)]
        data = pd.DataFrame(raw_data, columns = self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

    def btn2(self):
        raw_data = [(time.time(), self.name, 2, self.km)]
        data = pd.DataFrame(raw_data, columns = self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

    def btn3(self):
        raw_data = [(time.time(), self.name, 3, self.km)]
        data = pd.DataFrame(raw_data, columns = self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.km = self.km + 1
        alram(self)

class alram(QDialog):
    def __init__(self, parent):
        super(alram, self).__init__(parent)
        audio_in = 'in.mp3'
        audio_out = 'out.mp3'
        alram_ui = 'alram.ui'
        uic.loadUi(alram_ui, self)
        self.setWindowModality(2)
        self.label.setStyleSheet("color: red;"
                              "border-style: solid;"
                              "border-width: 2px;"
                              "background-color: #fcbdbd;"
                              "border-color: #FA8072;"
                              "border-radius: 3px")
        self.setWindowTitle('알림')
        self.show()
        playsound(audio_out)
        time.sleep(5)
        self.close()
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

        #버튼에 기능 연결
        self.btn_add.clicked.connect(self.addComboBoxItem)
        self.btn_del.clicked.connect(self.deleteComboBoxItem)
        self.btn_start.clicked.connect(self.start)

        #Style sheet
        self.btn_del.setStyleSheet("color: red;"
                              "border-style: solid;"
                              "border-width: 2px;"
                              "background-color: #fcbdbd;"
                              "border-color: #FA8072;"
                              "border-radius: 3px")

        self.btn_add.setStyleSheet("color: blue;"
                                "border-style: solid;"
                                "border-width: 2px;"
                                "background-color: #87CEFA;"
                                "border-color: #1E90FF;"
                                "border-radius: 3px")

        self.setWindowTitle("HMI")

    def start(self):
        name = str(self.cmb_drivers.currentText())
        filename = name + '.csv'
        if os.path.exists(filename):
            print(f'{name} 기록 시작합니다')
        else:
            df = pd.DataFrame(columns=['time', 'driver', 'status', 'km'])
            df.to_csv(filename, index=False)
            print(f'{filename} 파일을 생성하였습니다')
        HMI(self)
        self.hide()

    def addComboBoxItem(self) :
        self.cmb_drivers.addItem(self.lineedit_add.text())
        print("운전자가 추가 되었습니다")

        #UI파일에 신규 운전자 목록 추가
        new_driver = ET.SubElement(root[1][3], 'item')
        new_driver = ET.SubElement(new_driver, 'property', attrib={'name': 'text'})
        new_driver = ET.SubElement(new_driver, 'string')
        e = self.lineedit_add.text()
        new_driver.text = str(e)
        tree.write('holysid_1.ui', encoding='utf-8', xml_declaration=True)

        self.lineedit_add.clear()

    def deleteComboBoxItem(self) :
        self.delidx = self.cmb_drivers.currentIndex()
        print("운전자가 삭제 되었습니다")
        print(self.delidx)

        #UI파일에 기존 운전자 목록 삭제
        if self.delidx != -1:
            root[1][3].remove(root[1][3][self.delidx+1])
        else:
            try:
                root[1][3].remove(root[1][3][1])
            except:
                print('더이상 삭제할 운전자가 없습니다')
        tree.write('holysid_1.ui', encoding='utf-8', xml_declaration=True)

        self.cmb_drivers.removeItem(self.delidx)

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()