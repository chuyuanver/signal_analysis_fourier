from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib

import sys

import numpy as np
from numpy import pi

import json

PARAMETER_FILE = r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\parameters.txt'

def read_parameter(parameter_file):
    with open(parameter_file, 'r') as f:
        parameter_raw = f.read()
    parameters = json.loads(parameter_raw)
    return parameters

def save_parameter(parameter_file, **kwargs):
    parameters = read_parameter(parameter_file)
    with open(parameter_file,'w') as f:
        for key,val in kwargs.items():
            parameters[key] = val
        json.dump(parameters, f, indent = 2)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    data = pyqtSignal(tuple)

class FourierWorker(QRunnable): #Multithreading
    def __init__(self, time_data_y, f_max):
        super(FourierWorker,self).__init__()
        self.f_max = f_max
        self.time_data_y = time_data_y
        self.signals = WorkerSignals()
    @pyqtSlot()
    def run(self):
        self.freq_data_y = np.fft.rfft(self.time_data_y,norm = "ortho")
        self.freq_data_x = np.linspace(0, self.f_max, int(len(self.time_data_y)/2)+1)
        self.signals.data.emit((self.freq_data_x,self.freq_data_y))
        self.signals.finished.emit()

class MyLineEdit(QLineEdit):
    textModified = pyqtSignal(str,str) # (key, text)
    def __init__(self, key, contents='', parent=None):
        super(MyLineEdit, self).__init__(contents, parent)
        self.key = key
        self.editingFinished.connect(self.checkText)
        self.textChanged.connect(lambda: self.checkText())
        self.returnPressed.connect(lambda: self.checkText(True))
        self._before = contents

    def checkText(self, _return=False):
        if (not self.hasFocus() or _return) and self._before != self.text():
            self._before = self.text()
            self.textModified.emit(self.key, self.text())

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__()


        self.setWindowTitle('Data Analysis for NSOR project')
        self.setWindowIcon(QIcon(r"C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\window_icon.png"))

        openFile = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\open_file.png'),'&Open File...',self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open the data file')
        openFile.triggered.connect(self.open_file)

        exitProgram = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\exit_program.png'),'&Exit',self)
        exitProgram.setShortcut("Ctrl+W")
        exitProgram.setStatusTip('Close the Program')
        exitProgram.triggered.connect(self.exit_program)

        renewData = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\renew.png'),'&Renew',self)
        renewData.setShortcut("Ctrl+R")
        renewData.setStatusTip('Reload the original data')
        renewData.triggered.connect(self.renew_data)

        verticalZoom = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\vertical_zoom.png'),'&Vertical Zoom',self)
        verticalZoom.setShortcut("Ctrl+V")
        verticalZoom.setStatusTip('Zoom in the vertical direction')
        verticalZoom.setCheckable(True)
        verticalZoom.triggered.connect(self.vzoom)

        horizontalZoom = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\horizontal_zoom.png'),'&Horizontal Zoom',self)
        horizontalZoom.setShortcut("Ctrl+H")
        horizontalZoom.setStatusTip('Zoom in the horizaontal direction')
        horizontalZoom.setCheckable(True)
        horizontalZoom.triggered.connect(self.hzoom)

        moveCursor = QAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\move_cursor.png'),'&Move Cursor',self)
        moveCursor.setShortcut("Ctrl+M")
        moveCursor.setStatusTip('Move cursors')
        moveCursor.setCheckable(True)
        moveCursor.triggered.connect(self.move_cursor)

        mainMenu = self.menuBar() #create a menuBar
        fileMenu = mainMenu.addMenu('&File') #add a submenu to the menu ba
        fileMenu.addAction(openFile) # add what happens when this menu is interacted
        fileMenu.addSeparator()
        fileMenu.addAction(exitProgram) # add an exit menu

        self.toolbar = self.addToolBar('nsor_toolbar') #add a tool bar to the window
        self.toolbar.setIconSize(QSize(64,64))
        self.toolbar.addAction(openFile) # add what happens when this tool is interacted
        self.toolbar.addAction(renewData)
        self.toolbar.addSeparator()
        self.toolbar.addAction(verticalZoom)
        self.toolbar.addAction(horizontalZoom)
        self.toolbar.addAction(moveCursor)

        self.statusBar() #create a status bar
        #setting matplotlib

        matplotlib.rcParams.update({'font.size': 28})
        canvas = FigureCanvas(Figure(figsize=(40, 9)))
        '''
        setting axis as dictionary, containing two axes of time and freq
        '''
        self.ax = {}
        self.ax['time'] = canvas.figure.add_subplot(121)
        self.ax['freq'] = canvas.figure.add_subplot(122)
        for axis in self.ax.values():
            axis.tick_params(pad=20) #move tick away from axis

        self.fourier_lb = QLabel("Ready", self)

        parameters = read_parameter(PARAMETER_FILE)

        '''
        setting edits and labels as dictionary, representing all time and freq edits
        '''
        self.edits = {}
        labels = {}
        for key,val in parameters.items():
            if type(val) == list:
                val = str(val[0])+' '+str(val[1])
            if key =='file_name':
                continue
            labels[key] = QLabel(key.replace('_',' ').title(),self)
            self.edits[key] = MyLineEdit(key, val,self)
            self.edits[key].setStatusTip(f'{key}')
            self.edits[key].textModified.connect(self.limit_and_cursor)
            if key[0:4] == 'freq':
                self.edits[key].setFixedWidth(250)

        self.zeroPadPower = QComboBox(self)
        self.zeroPadPower.addItems(['x1','x2','x4','x8'])
        self.zeroPadPower.setStatusTip('This sets the zerofilling of the data')
        self.zeroPadPower.activated[str].connect(self.zero_padding)

        #setting layout
        self._main = QWidget()
        self.setCentralWidget(self._main)
        layout1 = QHBoxLayout(self._main)
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()
        layout4 = QVBoxLayout()

        for key in labels.keys():
            if key[0:4] == 'time':
                layout2.addWidget(labels[key])
                layout2.addWidget(self.edits[key])
            elif key[0:4] == 'freq':
                layout4.addWidget(labels[key])
                layout4.addWidget(self.edits[key])

        layout2.addWidget(self.zeroPadPower)
        layout1.addLayout(layout2)
        layout2.addStretch(1)
        layout1.addLayout(layout3)
        layout3.addWidget(canvas)
        layout3.addWidget(self.fourier_lb)
        layout1.addLayout(layout4)
        layout4.addStretch(1)

        self.threadpool = QThreadPool() #Multithreading

    def limit_and_cursor(self, key, text):
        try:
            value = [float(x) for x in text.split(' ')]
            # if key[0:4] == 'time':
            #     self.ax'[time'].set
        except ValueError:
            print('please input only numbers')

        print(key+': ' + text)

    def move_cursor(self):
        pass

    def vzoom(self):
        pass

    def hzoom(self):
        pass

    def fourier_multithreading(self, time_sig):
        self.fourier_lb.setText('Waiting...')
        fourier_worker = FourierWorker(time_sig, self.f_max)
        fourier_worker.signals.data.connect(self.set_fourier)
        fourier_worker.signals.finished.connect(self.fourier_finished)
        self.threadpool.start(fourier_worker)

    def fourier_finished(self):
        self.fourier_lb.setText('Ready')

    def zero_padding(self, pad_power):
        try:
            pad_power = int(pad_power[1:])
            x = np.ceil(np.log2(len(self.data['time_y'])))
            n = 2**(pad_power-1)
            l = int(2**x*n)
            time_sig = np.pad(self.data['time_y'],(0,l-len(self.data['time_y'])),'constant')
            self.fourier_multithreading(time_sig)
        except AttributeError:
            dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                        QMessageBox.Ok)
            self.zeroPadPower.setCurrentIndex(0)

    def renew_data(self):
        try:
            self.data['time_x'] = self.data['raw_x']
            self.data['time_y'] = self.data['raw_y']
            self.draw('time')
            # .. add more fourier transform part

        except AttributeError:
            dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                        QMessageBox.Ok)

    def exit_program(self):
        choice = QMessageBox.question(self, 'Exiting',
                                                'Are you sure about exit?',
                                                QMessageBox.Yes | QMessageBox.No) #Set a QMessageBox when called
        if choice == QMessageBox.Yes:  # give actions when answered the question
            sys.exit()

    def open_file(self):
        dlg = QFileDialog()
        dlg.setDirectory(read_parameter(PARAMETER_FILE)['file_name'])
        if dlg.exec_():
            file_name = dlg.selectedFiles()[0]
            save_parameter(PARAMETER_FILE,
                        **{"file_name": file_name})

            raw_data = np.fromfile(file_name, '>f8')
            self.data = {}
            self.data['raw_x'] = raw_data[::2]
            self.data['raw_y'] = raw_data[1::2]
            self.data['time_x'] = self.data['raw_x']
            self.data['time_y'] = self.data['raw_y']

            dt = self.data['time_x'][1]-self.data['time_x'][0]
            self.f_max =1/(2*dt)
            self.fourier_multithreading(self.data['time_y'])
            self.draw('time')


    def set_fourier(self,data):
        self.data['freq_x'] = data[0]
        self.data['freq_y'] = data[1]
        self.draw('freq')

    def draw(self,key):
        self.ax[key].clear()
        if key == 'time':
            self.ax[key].plot(self.data[key+'_x'],self.data[key+'_y'])
        elif key == 'freq':
            self.ax[key].plot(self.data[key+'_x'],np.abs(self.data[key+'_y']))
        self.ax[key].figure.canvas.draw()


app = QApplication(sys.argv)

window = MainWindow()
window.move(300,300)
window.show()
app.exec_()
