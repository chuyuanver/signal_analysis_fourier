from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib
from matplotlib.ticker import FormatStrFormatter

import sys
import os

import numpy as np
from numpy import pi

import json

import time

BASE_FOLDER = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PARAMETER_FILE = BASE_FOLDER + r'\pyqt_analysis\parameters.txt'

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

'''
Multithreading preparation
'''
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
        self.freq_data_y = np.fft.rfft(self.time_data_y)/len(self.time_data_y)*2
        self.freq_data_x = np.linspace(0, self.f_max, int(len(self.time_data_y)/2)+1)
        self.signals.data.emit((self.freq_data_x,self.freq_data_y))
        self.signals.finished.emit()

'''
customized gui
'''
class MyLineEdit(QLineEdit):
    '''
    edit class for capturing input
    '''
    textModified = pyqtSignal(str,str) # (key, text)
    def __init__(self, key, contents='', parent=None):
        super(MyLineEdit, self).__init__(contents, parent)
        self.key = key
        self.editingFinished.connect(self.checkText)
        self.textChanged.connect(lambda: self.checkText())
        self.returnPressed.connect(lambda: self.checkText(True))
        self._before = contents

    def checkText(self, _return=False):
        if (not self.hasFocus() or _return):
            self._before = self.text()
            self.textModified.emit(self.key, self.text())

class MyQAction(QAction):
    '''
    edit action to also give a key with the toggle state
    '''
    btnToggled = pyqtSignal(str) # (checked, key)
    def __init__(self, icon, text, key, parent=None):
        super(MyQAction, self).__init__(icon, text, parent)
        # self.setCheckable(True)
        self.key = key
        self.triggered.connect(self._triggered)

    def _triggered(self):
        self.btnToggled.emit(self.key)

'''
################################################################################
main gui window intitation
'''


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__()

        self.setWindowTitle('Data Analysis for NSOR project')
        self.setWindowIcon(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\window_icon.png'))

        '''
        q actions that are intend to be in menu or toolbar
        '''

        openFile = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\open_file.png'),'&Open File...',self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open the data file')
        openFile.triggered.connect(self.open_file)

        exitProgram = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\exit_program.png'),'&Exit',self)
        exitProgram.setShortcut("Ctrl+W")
        exitProgram.setStatusTip('Close the Program')
        exitProgram.triggered.connect(self.exit_program)

        renewData = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\renew.png'),'&Renew',self)
        renewData.setShortcut("Ctrl+R")
        renewData.setStatusTip('Reload the original data')
        renewData.triggered.connect(self.renew_data)

        self.verticalZoom = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\vertical_zoom.png'),'&Vertical Zoom',self)
        self.verticalZoom.setShortcut("Ctrl+Shift+V")
        self.verticalZoom.setStatusTip('Zoom in the vertical direction')
        self.verticalZoom.setCheckable(True)
        self.verticalZoom.toggled.connect(self.vzoom)

        self.horizontalZoom = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\horizontal_zoom.png'),'&Horizontal Zoom',self)
        self.horizontalZoom.setShortcut("Ctrl+Shift+H")
        self.horizontalZoom.setStatusTip('Zoom in the horizaontal direction')
        self.horizontalZoom.setCheckable(True)
        self.horizontalZoom.toggled.connect(self.hzoom)

        self.moveCursor = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\move_cursor.png'),'&Move Cursor',self)
        self.moveCursor.setShortcut("Ctrl+M")
        self.moveCursor.setStatusTip('Move cursors')
        self.moveCursor.setCheckable(True)
        self.moveCursor.toggled.connect(self.move_cursor)

        self.autoAxis = {}
        self.autoAxis['time_x'] = MyQAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_time_x.png'),'&Auto X axis (time)', 'time_x', self)
        self.autoAxis['time_y'] = MyQAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_time_y.png'),'&Auto Y axis (time)', 'time_y', self)
        self.autoAxis['freq_x'] = MyQAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_freq_x.png'),'&Auto X axis (freq)', 'freq_x', self)
        self.autoAxis['freq_y'] = MyQAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_freq_y.png'),'&Auto Y axis (freq)', 'freq_y', self)

        editParameters = QAction('&Edit Parameter', self)
        editParameters.setShortcut('Ctrl+E')
        editParameters.setStatusTip('open and edit the parameter file')
        editParameters.triggered.connect(self.edit_parameters)

        saveParameters = QAction('&Save Parameter', self)
        saveParameters.setShortcut('Ctrl+S')
        saveParameters.setStatusTip('save the parameters on screen to file')
        saveParameters.triggered.connect(self.save_parameters)

        self.data_type = QComboBox()
        self.data_type.setStatusTip('bin for legacy data recorded from labview program, big endian coded binary data, npy for numpy type data')
        self.data_type.addItems(['bin', '.npy'])

        '''
        setting menubar
        '''
        mainMenu = self.menuBar() #create a menuBar
        fileMenu = mainMenu.addMenu('&File') #add a submenu to the menu bar
        fileMenu.addAction(openFile) # add what happens when this menu is interacted
        fileMenu.addSeparator()
        fileMenu.addAction(exitProgram) # add an exit menu
        parameterMenu = mainMenu.addMenu('&Parameter')
        parameterMenu.addAction(editParameters)
        parameterMenu.addAction(saveParameters)



        '''
        setting toolbar
        '''
        self.toolbar = self.addToolBar('nsor_toolbar') #add a tool bar to the window
        if app.desktop().screenGeometry().height() == 2160:
            self.toolbar.setIconSize(QSize(100,100))
        else:
            self.toolbar.setIconSize(QSize(60,60))
        self.toolbar.addAction(openFile) # add what happens when this tool is interacted


        self.toolbar.addWidget(self.data_type)
        self.toolbar.addAction(renewData)
        self.toolbar.addSeparator()

        self.toolbar.addAction(self.verticalZoom)
        self.toolbar.addAction(self.horizontalZoom)
        self.toolbar.addAction(self.moveCursor)
        self.toolbar.addSeparator()
        for key,item in self.autoAxis.items():
            self.autoAxis[key].setStatusTip(f'set {key} axis to size automatically')
            self.autoAxis[key].btnToggled.connect(self.auto_axis)
            self.toolbar.addAction(self.autoAxis[key])



        self.statusBar() #create a status bar
        '''
        setting matplotlib
        '''

        if app.desktop().screenGeometry().height() == 2160:
            matplotlib.rcParams.update({'font.size': 28})
        else:
            matplotlib.rcParams.update({'font.size': 14})
        self.canvas = FigureCanvas(Figure(figsize=(40, 9)))
        self.fig = self.canvas.figure

        '''
        setting axis as dictionary,

        containing two axes of time and freq
        ax['time']
        ax['freq']
        also initiate the vertical lines
        vline['time_l']
        vline['time_r']
        vline['freq_l']
        vline['freq_r']
        '''
        self.ax = {}
        self.vline = {}
        self.ax['time'] = self.fig.add_subplot(121)
        self.ax['freq'] = self.fig.add_subplot(122)

        for axis in self.ax.values():
            if app.desktop().screenGeometry().height() == 2160:
                axis.tick_params(pad=20)
            elif app.desktop().screenGeometry().height() == 1080:
                axis.tick_params(pad=10)
            # axis.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        self.fourier_lb = QLabel("Ready", self)

        self.parameters = read_parameter(PARAMETER_FILE)

        '''
        setting edits and labels as dictionary,

        representing all time and freq edits
        "file_name" is excluded
        "time_x_limit"
        "time_y_limit"
        "freq_x_limit"
        "freq_y_imit"
        "time_cursor"
        "freq_cursor"
        '''
        self.edits = {}
        labels = {}
        for key,value in self.parameters.items():
            if type(value) == list:
                val = str(value[0])+' '+str(value[1])
            if key =='file_name':
                continue
            labels[key] = QLabel(key.replace('_',' ').title(),self)
            self.edits[key] = MyLineEdit(key, val, self)
            self.edits[key].setStatusTip(f'{key}')
            self.edits[key].textModified.connect(self.limit_and_cursor)
            if key[0:4] == 'freq':
                self.edits[key].setFixedWidth(250)
            if 'cursor' in key:
                self.vline[key[0:4]+'_l'] = self.ax[key[0:4]].axvline(float(value[0]), c = 'red')
                self.vline[key[0:4]+'_r'] = self.ax[key[0:4]].axvline(float(value[1]), c = 'red')
                self.vline[key[0:4]+'_l'].set_animated(True)
                self.vline[key[0:4]+'_r'].set_animated(True)

        self.integral_label = QLabel('Peak Intensity: \n0',self)

        self.zeroPadPower = QComboBox(self)
        self.zeroPadPower.addItems(['x1','x2','x4','x8'])
        self.zeroPadPower.setStatusTip('This sets the zerofilling of the data')
        self.zeroPadPower.activated[str].connect(self.zero_padding)

        '''
        phase stuff
        '''
        self.toolbar.addSeparator()
        first_order_phase_check = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_phase_check.png'),'&First order on',self)
        first_order_phase_check.setStatusTip('Check to enbale 1st order phase')
        first_order_phase_check.setShortcut('Ctrl+F')
        first_order_phase_check.toggled.connect(self.first_order_phase_check)
        first_order_phase_check.setCheckable(True)
        self.toolbar.addAction(first_order_phase_check)

        auto_phase_btn = QAction(QIcon(BASE_FOLDER + r'\pyqt_analysis\icons\auto_phase_btn.png'),'&Auto Phase',self)
        auto_phase_btn.setStatusTip('Auto phase the peak (0th order only)')
        auto_phase_btn.setShortcut('Ctrl+A')
        auto_phase_btn.triggered.connect(self.auto_phase)
        self.toolbar.addAction(auto_phase_btn)

        self.zeroth_slider = QSlider(self)
        self.zeroth_slider.setMinimum(0)
        self.zeroth_slider.setMaximum(360)
        self.zeroth_slider.setValue(0)
        self.zeroth_slider.setTickInterval(1)
        self.zeroth_slider.valueChanged.connect(self.zeroth_order_phase)
        self.zeroth_slider.sliderReleased.connect(self.slider_released)


        self.first_slider = QSlider(self)
        self.first_slider.setMinimum(0)
        self.first_slider.setMaximum(360)
        self.first_slider.setValue(0)
        self.first_slider.hide()
        self.first_slider.valueChanged.connect(self.first_order_phase)

        self.phase_info = QLabel('Current Phase: \n0th: 0\n1st: 0 \nInt: 0',self)



        '''
        setting layout
        '''
        self._main = QWidget()
        self.setCentralWidget(self._main)
        layout1 = QHBoxLayout(self._main)
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()
        layout4 = QVBoxLayout()
        layout5 = QHBoxLayout()

        for key in labels.keys():
            if key[0:4] == 'time':
                layout2.addWidget(labels[key])
                layout2.addWidget(self.edits[key])
            elif key[0:4] == 'freq':
                layout4.addWidget(labels[key])
                layout4.addWidget(self.edits[key])
        layout4.addWidget(self.integral_label)
        layout4.addWidget(self.phase_info)

        layout4.addLayout(layout5)
        layout5.addWidget(self.zeroth_slider)
        layout5.addWidget(self.first_slider)


        layout2.addWidget(self.zeroPadPower)
        layout1.addLayout(layout2)
        layout2.addStretch(1)
        layout1.addLayout(layout3)
        layout3.addWidget(self.canvas)
        layout3.addWidget(self.fourier_lb)
        layout1.addLayout(layout4)
        # layout4.addStretch(1)

        self.threadpool = QThreadPool() #Multithreading

    '''
    ################################################################################
    phase
    '''
    def slider_released(self):
        self.canvas.draw()
        key = 'freq'
        self.ax[key[0:4]].ticklabel_format(style='sci', axis='both', scilimits=(0,0)) # format the tick label of the axes
        for k in self.ax.keys():
            self.ax[k].draw_artist(self.vline[k+'_l'])
            self.ax[k].draw_artist(self.vline[k+'_r'])

    def first_order_phase_check(self,toggle_state):
        if toggle_state:
            self.first_slider.show()
        else:
            self.first_slider.setValue(0)
            self.first_slider.hide()

    def auto_phase(self):
        try:
            reft = self.data['freq_y'].real[self.csL:self.csR]
            imft = self.data['freq_y'].imag[self.csL:self.csR]
            intensity_int = np.array([])
            for angle in range(360):
                phi = angle/360*2*pi
                intensity_int = np.append(intensity_int, np.sum(np.cos(phi)*reft + np.sin(phi)*imft))
            best_angle = intensity_int.argmax()
            best_phi = best_angle/360*2*pi
            self.zeroth_slider.setValue(best_angle)
            self.data['freq_real'] = self.data['freq_y'].real*np.cos(best_phi) + \
                                     self.data['freq_y'].imag*np.sin(best_phi)
            self.draw_phased_data()
        except AttributeError:
            dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                        QMessageBox.Ok)


    def zeroth_order_phase(self, value):
        phi = value/360*2*pi
        try:
            reft = self.data['freq_y'].real[self.csL:self.csR]
            imft = self.data['freq_y'].imag[self.csL:self.csR]
            self.data['freq_real'] = self.data['freq_y'].real*np.cos(phi) + \
                                     self.data['freq_y'].imag*np.sin(phi)
            intensity = np.sum(np.cos(phi)*reft + np.sin(phi)*imft)
            str = self.phase_info.text()
            str_lst = str.split('\n')
            intensity_str = "{:.5f}".format(intensity*2)
            self.phase_info.setText(f'Current Phase: \n0th: {value}\n'+str_lst[2]+f'\nInt: {intensity_str}')
            self.draw_phased_data()
            self.canvas.blit(self.ax['freq'].bbox)
        except AttributeError:
            dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                        QMessageBox.Ok)


    def first_order_phase(self, value):
        intensity = 0
        str = self.phase_info.text()
        str_lst = str.split('\n')
        intensity_str = "{:.5f}".format(intensity*2)
        self.phase_info.setText('Current Phase: \n'+ str_lst[1] +f'\n1st: {value}'+f'\nInt: {intensity_str}')

    def draw_phased_data(self):
        key = 'freq'
        self.ax[key].clear()
        self.ax[key].plot(self.data[key+'_x'],self.data[key+'_real'])

        cs_value = [float(x) for x in self.edits[key+'_cursor'].text().split(' ')]
        self.vline[key+'_l'].set_xdata([cs_value[0], cs_value[0]])
        self.vline[key+'_r'].set_xdata([cs_value[1], cs_value[1]])

        lm_value = [float(x) for x in self.edits[key+'_x_limit'].text().split(' ')]

        self.ax[key].set_xlim(lm_value[0],lm_value[1])

        self.canvas.draw()
        self.ax[key].ticklabel_format(style='sci', axis='both', scilimits=(0,0)) # format the tick label of the axes
        for k in self.ax.keys():
            self.ax[k].draw_artist(self.vline[k+'_l'])
            self.ax[k].draw_artist(self.vline[k+'_r'])






    '''
    ################################################################################
    some less complicated slot
    '''

    def edit_parameters(self):
        os.startfile(PARAMETER_FILE)

    def save_parameters(self):
        for key in self.parameters.keys():
            if key =='file_name':
                continue
            str = self.edits[key].text()
            self.parameters[key] = str.split(' ')

        save_parameter(PARAMETER_FILE, **self.parameters)

    def auto_axis(self, key):
        '''
        auto scale the axis
        '''
        if key != 'time_y':
            self.ax[key[0:4]].autoscale(axis = key[5])
        else:
            try:
                average = np.mean( np.abs( self.data['time_y'] ) )
                self.ax['time'].set_ylim(-2*average, 2*average)
            except AttributeError:
                self.ax[key[0:4]].autoscale(axis = key[5])


        self.canvas.draw()
        self.ax[key[0:4]].ticklabel_format(style='sci', axis='both', scilimits=(0,0)) # format the tick label of the axes
        for k in self.ax.keys():
            self.ax[k].draw_artist(self.vline[k+'_l'])
            self.ax[k].draw_artist(self.vline[k+'_r'])

    '''
    ################################################################################
    browse the figure
    calculate based on cursors
    '''

    def limit_and_cursor(self, key, text):
        '''
        respond to the change of text in the edits
        '''
        try:
            value = [float(x) for x in text.split(' ')]
            if 'limit' in key:
                if 'x' in key:
                    self.ax[key[0:4]].set_xlim(value[0],value[1])
                elif 'y' in key:
                    self.ax[key[0:4]].set_ylim(value[0],value[1])


            elif 'cursor' in key:
                self.vline[key[0:4]+'_l'].set_xdata([value[0], value[0]])
                self.vline[key[0:4]+'_r'].set_xdata([value[1], value[1]])
                try:
                    cs1 = np.argmin(np.abs(self.data[key[0:4]+'_x']-value[0])) # finding the index corresponding to the time stamp
                    cs2 = np.argmin(np.abs(self.data[key[0:4]+'_x']-value[1]))
                    if cs1>cs2:
                        self.cursor_operation(key, cs2, cs1)
                    else:
                        self.cursor_operation(key, cs1, cs2)
                except AttributeError:
                    dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                                QMessageBox.Ok)


            self.canvas.draw()
            self.ax[key[0:4]].ticklabel_format(style='sci', axis='both', scilimits=(0,0)) # format the tick label of the axes
            for k in self.ax.keys():
                self.ax[k].draw_artist(self.vline[k+'_l'])
                self.ax[k].draw_artist(self.vline[k+'_r'])


        except ValueError:
            dlg = QMessageBox.warning(self,'WARNING', 'Input only number',
                                        QMessageBox.Ok)


    def cursor_operation(self, key, csL, csR):
        self.csL = csL
        self.csR = csR
        if 'time' in key:
            self.zero_padding(self.zeroPadPower.currentText(),[csL,csR])
        elif 'freq' in key:
            intensity = ( np.sum(self.data['freq_y'].real)**2 + np.sum(self.data['freq_y'].imag)**2 )**(1/2)
            intensity_str = "{:.5f}".format(intensity)
            self.integral_label.setText(f'Peak Intensity: \n{intensity_str}') #

    def cursor_lines_in_axis(self,ax):
        if ax == self.ax['time']:
            line1 = self.vline['time_l']
            line2 = self.vline['time_r']
        else:
            line1 = self.vline['freq_l']
            line2 = self.vline['freq_r']
        return line1,line2

    def move_cursor(self, state):
        def on_press(event):
            if self.in_ax:
                if self.current_line != None:
                    if event.button == 1:
                        ax = event.inaxes
                        self.last_ax = ax
                        self.c_lock = True
                        self.x0 = event.xdata
                        self.current_line.set_xdata([event.xdata,event.xdata])
                        line1,line2 = self.cursor_lines_in_axis(ax)

                        self.canvas.draw()
                        self.background = self.canvas.copy_from_bbox(ax.bbox)
                        ax.draw_artist(line1)
                        ax.draw_artist(line2)
                        self.canvas.blit(ax.bbox)


        def on_motion(event):
            ax = event.inaxes
            if ax != None:
                line1,line2 = self.cursor_lines_in_axis(ax)

                if self.c_lock:
                    self.current_line.set_xdata([event.xdata,event.xdata])
                    self.canvas.restore_region(self.background)
                    ax.draw_artist(line1)
                    ax.draw_artist(line2)
                    self.canvas.blit(ax.bbox)
                    if self.x0 > event.xdata:
                        self.c_side = 'left'
                    else:
                        self.c_side = 'right'


                else:
                    if abs(event.xdata - line1.get_xdata()[0])/self.xrange <= 0.02:
                        if self.cursor == 'arrow':
                            QApplication.setOverrideCursor(Qt.CrossCursor)
                            self.current_line = line1
                            self.cursor = 'cross'
                    elif abs(event.xdata - line2.get_xdata()[0])/self.xrange <= 0.02:
                        if self.cursor == 'arrow':
                            QApplication.setOverrideCursor(Qt.CrossCursor)
                            self.cursor = 'cross'
                            self.current_line = line2
                    else:
                        if self.cursor == 'cross':
                            QApplication.restoreOverrideCursor()
                            self.cursor = 'arrow'
                            self.current_line = None

        def on_release(event):
            if self.c_lock:
                self.background = None
                self.c_lock = False

                ax = event.inaxes
                if ax != self.last_ax:
                    ax = self.last_ax

                    limit = ax.get_xlim()
                    if self.c_side == 'left':
                        event.xdata = limit[0]
                    else:
                        event.xdata = limit[1]

                line1,line2 = self.cursor_lines_in_axis(ax)

                str1 = "{:.5E}".format(line1.get_xdata()[0])
                str2 = "{:.5E}".format(line2.get_xdata()[0])


                if line2.get_xdata()[0] < line1.get_xdata()[0]:
                    str1,str2 = str2,str1

                if ax == self.ax['freq']:
                    self.edits['freq_cursor'].setText(str1+' '+str2)
                else:
                    self.edits['time_cursor'].setText(str1+' '+str2)


        def move_in_ax(event):
            self.in_ax = True
            ax = event.inaxes
            xmin,xmax = ax.get_xlim()
            self.xrange = xmax - xmin

        def move_out_ax(event):
            self.out_ax = False


        if state:
            self.cursor = 'arrow'
            self.verticalZoom.setChecked(False)
            self.horizontalZoom.setChecked(False)
            self.c_lock = False
            self.c_onpick = False
            self.c_cid_press = self.canvas.mpl_connect('button_press_event', on_press)
            self.c_cid_release = self.canvas.mpl_connect('button_release_event', on_release)
            self.c_cid_motion = self.canvas.mpl_connect('motion_notify_event', on_motion)
            self.c_in_ax = self.canvas.mpl_connect('axes_enter_event', move_in_ax)
            self.c_out_ax = self.canvas.mpl_connect('axes_leave_event', move_out_ax)

        else:
            self.canvas.mpl_disconnect(self.c_cid_press)
            self.canvas.mpl_disconnect(self.c_cid_release)
            self.canvas.mpl_disconnect(self.c_cid_motion)
            self.canvas.mpl_disconnect(self.c_in_ax)
            self.canvas.mpl_disconnect(self.c_out_ax)


    def vzoom(self, state):
        def on_press(event):
            if self.in_ax:
                ax = event.inaxes
                line1,line2 = self.cursor_lines_in_axis(ax)
                try:
                    if event.button == 1:
                        self.vlock = True
                        self.last_ax = ax
                        ymin,ymax = ax.get_ylim()
                        self.yrange = ymax - ymin
                        xmin,xmax = ax.get_xlim()
                        self.xrange = xmax - xmin
                        self.y0 = event.ydata
                        self.top_ln, = ax.plot([event.xdata-self.xrange*0.02, event.xdata+self.xrange*0.02],[event.ydata,event.ydata])
                        self.btm_ln, = ax.plot([event.xdata-self.xrange*0.02, event.xdata+self.xrange*0.02],[event.ydata,event.ydata])
                        self.vzoom_ln, = ax.plot([event.xdata, event.xdata],[event.ydata,event.ydata])
                        self.top_ln.set_color('m')
                        self.btm_ln.set_color('m')
                        self.vzoom_ln.set_color('m')
                        # print(self.right_ln.get_xdata(), self.right_ln.get_ydata())
                        self.btm_ln.set_animated(True)
                        self.vzoom_ln.set_animated(True)
                        self.canvas.draw()
                        self.background = self.canvas.copy_from_bbox(ax.bbox)
                        ax.draw_artist(self.vzoom_ln)
                        ax.draw_artist(self.btm_ln)
                        line1,line2 = self.cursor_lines_in_axis(ax)
                        ax.draw_artist(line1)
                        ax.draw_artist(line2)
                        self.canvas.blit(ax.bbox)
                    else:

                        self.top_ln.remove()
                        self.vzoom_ln.remove()
                        self.btm_ln.remove()
                        self.canvas.draw()
                        self.background = None
                        self.vlock = False
                        ax.draw_artist(line1)
                        ax.draw_artist(line2)
                        self.canvas.blit(ax.bbox)
                except:
                    print('no')
        def on_release(event):
            if self.vlock:
                try:
                    self.top_ln.remove()
                    self.vzoom_ln.remove()
                    self.btm_ln.remove()
                    self.canvas.draw()
                    self.background = None
                    self.vlock = False
                    ax = event.inaxes
                    if ax != self.last_ax:
                        ax = self.last_ax
                        limit = ax.get_ylim()
                        if self.vside == 'btm':
                            event.ydata = limit[0]
                        else:
                            event.ydata = limit[1]

                    if self.y0 > event.ydata:
                        self.y0, event.ydata = event.ydata, self.y0
                    str1 = "{:.5E}".format(self.y0)
                    str2 = "{:.5E}".format(event.ydata)
                    if ax == self.ax['freq']:
                        self.edits['freq_y_limit'].setText(str1+' '+str2)
                    else:
                        self.edits['time_y_limit'].setText(str1+' '+str2)
                except:
                    print('no')

        def on_motion(event):
            if self.vlock:
                ax = event.inaxes
                if ax != None:
                    self.btm_ln.set_ydata([event.ydata, event.ydata])
                    self.vzoom_ln.set_ydata([self.y0, event.ydata])
                    self.canvas.restore_region(self.background)
                    ax.draw_artist(self.vzoom_ln)
                    ax.draw_artist(self.btm_ln)
                    line1,line2 = self.cursor_lines_in_axis(ax)
                    ax.draw_artist(line1)
                    ax.draw_artist(line2)
                    self.canvas.blit(ax.bbox)
                    if self.y0 > event.ydata:
                        self.vside = 'btm'
                    else:
                        self.vside = 'top'

        def move_in_ax(event):
            self.in_ax = True

        def move_out_ax(event):
            self.out_ax = False

        if state:
            self.horizontalZoom.setChecked(False)
            self.moveCursor.setChecked(False)
            self.vlock = False
            self.vcid_press = self.canvas.mpl_connect('button_press_event', on_press)
            self.vcid_release = self.canvas.mpl_connect('button_release_event', on_release)
            self.vcid_motion = self.canvas.mpl_connect('motion_notify_event', on_motion)
            self.vin_ax = self.canvas.mpl_connect('axes_enter_event', move_in_ax)
            self.vout_ax = self.canvas.mpl_connect('axes_leave_event', move_out_ax)
        else:
            self.canvas.mpl_disconnect(self.vcid_press)
            self.canvas.mpl_disconnect(self.vcid_release)
            self.canvas.mpl_disconnect(self.vcid_motion)
            self.canvas.mpl_disconnect(self.vin_ax)
            self.canvas.mpl_disconnect(self.vout_ax)



    def hzoom(self, state):
        def on_press(event):
            if self.in_ax:
                ax = event.inaxes
                line1,line2 = self.cursor_lines_in_axis(ax)
                try:
                    if event.button == 1:
                        self.hlock = True
                        self.last_ax = ax
                        ymin,ymax = ax.get_ylim()
                        self.yrange = ymax - ymin
                        xmin,xmax = ax.get_xlim()
                        self.xrange = xmax - xmin
                        self.x0 = event.xdata
                        self.left_ln, = ax.plot([event.xdata, event.xdata],[event.ydata-self.yrange*0.02,event.ydata+self.yrange*0.02])
                        self.right_ln, = ax.plot([event.xdata, event.xdata],[event.ydata-self.yrange*0.02,event.ydata+self.yrange*0.02])
                        self.hzoom_ln, = ax.plot([event.xdata, event.xdata],[event.ydata,event.ydata])
                        self.left_ln.set_color('m')
                        self.right_ln.set_color('m')
                        self.hzoom_ln.set_color('m')
                        # print(self.right_ln.get_xdata(), self.right_ln.get_ydata())
                        self.right_ln.set_animated(True)
                        self.hzoom_ln.set_animated(True)
                        self.canvas.draw()
                        self.background = self.canvas.copy_from_bbox(ax.bbox)
                        ax.draw_artist(self.hzoom_ln)
                        ax.draw_artist(self.right_ln)
                        ax.draw_artist(line1)
                        ax.draw_artist(line2)
                        self.canvas.blit(ax.bbox)

                    else:
                        self.left_ln.remove()
                        self.hzoom_ln.remove()
                        self.right_ln.remove()
                        self.canvas.draw()
                        self.background = None
                        self.hlock = False
                        ax.draw_artist(line1)
                        ax.draw_artist(line2)
                        self.canvas.blit(ax.bbox)

                except:
                    print('no')

        def on_motion(event):
            if self.hlock:
                ax = event.inaxes
                if ax != None:
                    self.right_ln.set_xdata([event.xdata, event.xdata])
                    self.hzoom_ln.set_xdata([self.x0, event.xdata])
                    self.canvas.restore_region(self.background)
                    ax.draw_artist(self.hzoom_ln)
                    ax.draw_artist(self.right_ln)
                    line1,line2 = self.cursor_lines_in_axis(ax)
                    ax.draw_artist(line1)
                    ax.draw_artist(line2)
                    self.canvas.blit(ax.bbox)
                    if self.x0 > event.xdata:
                        self.hside = 'left'
                    else:
                        self.hside = 'right'



        def on_release(event):
            if self.hlock:
                try:
                    self.left_ln.remove()
                    self.hzoom_ln.remove()
                    self.right_ln.remove()
                    self.canvas.draw()
                    self.background = None
                    self.hlock = False
                    ax = event.inaxes
                    if ax != self.last_ax:
                        ax = self.last_ax
                        limit = ax.get_xlim()
                        if self.hside == 'left':
                            event.xdata = limit[0]
                        else:
                            event.xdata = limit[1]

                    if self.x0 > event.xdata:
                        self.x0, event.xdata = event.xdata, self.x0

                    # ax.set_xlim(self.x0, event.xdata)
                    str1 = "{:.5E}".format(self.x0)
                    str2 = "{:.5E}".format(event.xdata)
                    if ax == self.ax['freq']:
                        self.edits['freq_x_limit'].setText(str1+' '+str2)
                    else:
                        self.edits['time_x_limit'].setText(str1+' '+str2)


                except:
                    print('no')

        def move_in_ax(event):
            self.in_ax = True

        def move_out_ax(event):
            self.out_ax = False

        if state:
            self.moveCursor.setChecked(False)
            self.verticalZoom.setChecked(False)
            self.hlock = False
            self.hcid_press = self.canvas.mpl_connect('button_press_event', on_press)
            self.hcid_release = self.canvas.mpl_connect('button_release_event', on_release)
            self.hcid_motion = self.canvas.mpl_connect('motion_notify_event', on_motion)
            self.hin_ax = self.canvas.mpl_connect('axes_enter_event', move_in_ax)
            self.hout_ax = self.canvas.mpl_connect('axes_leave_event', move_out_ax)
        else:
            self.canvas.mpl_disconnect(self.hcid_press)
            self.canvas.mpl_disconnect(self.hcid_release)
            self.canvas.mpl_disconnect(self.hcid_motion)
            self.canvas.mpl_disconnect(self.hin_ax)
            self.canvas.mpl_disconnect(self.hout_ax)




    '''
    ################################################################################
    Multithreading fft calculation
    '''
    def fourier_multithreading(self, time_sig):
        self.fourier_lb.setText('Waiting...')
        fourier_worker = FourierWorker(time_sig, self.f_max)
        fourier_worker.signals.data.connect(self.set_fourier)
        fourier_worker.signals.finished.connect(self.fourier_finished)
        self.threadpool.start(fourier_worker)

    def set_fourier(self,data):
        self.data['freq_x'] = data[0]
        self.data['freq_y'] = data[1]
        self.draw('freq')
        self.edits['freq_x_limit'].returnPressed.emit()
        self.edits['freq_cursor'].returnPressed.emit()



    def fourier_finished(self):
        self.fourier_lb.setText('Ready')

    '''
    ################################################################################
    make zerofilling work
    '''


    def zero_padding(self, pad_power, value = []):
        if value == []:
            value = [float(val) for val in self.parameters['time_cursor']]
            cs1 = np.argmin(np.abs(self.data['time_x']-value[0])) # finding the index corresponding to the time stamp
            cs2 = np.argmin(np.abs(self.data['time_x']-value[1]))
        else:
            cs1 = value[0]
            cs2 = value[1]
        try:
            time_data =self.data['time_y'][cs1:cs2]
            pad_power = int(pad_power[1:])
            x = np.ceil(np.log2(len(self.data['time_y'])))
            n = 2**(pad_power-1)
            l = int(2**x*n)
            time_sig = np.pad(time_data,(0,l-len(time_data)),'constant')
            self.fourier_multithreading(time_sig)
        except AttributeError:
            dlg = QMessageBox.warning(self,'WARNING', 'No original data available!',
                                        QMessageBox.Ok)
            self.zeroPadPower.setCurrentIndex(0)

    '''
    ################################################################################
    other miscellaneous function
    '''

    def renew_data(self):
        try:
            self.data['time_x'] = self.data['raw_x']
            self.data['time_y'] = self.data['raw_y']
            self.draw('time')
            self.zeroPadPower.setCurrentIndex(0)
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
        '''
        open file and assign data to a dictionary self.Data
        self.data['raw_x']
        self.data['raw_y']
        above two are the original data
        self.data['time_x']
        self.data['time_y']
        self.data['freq_x']
        self.data['freq_y']

        '''
        dlg = QFileDialog()
        dlg.setDirectory(read_parameter(PARAMETER_FILE)['file_name'])
        if dlg.exec_():
            file_name = dlg.selectedFiles()[0]
            save_parameter(PARAMETER_FILE,
                        **{"file_name": file_name})
            if str(self.data_type.currentText()) =='bin':
                raw_data = np.fromfile(file_name, '>f8')
            elif str(self.data_type.currentText()) == '.npy':
                raw_data = np.load(file_name)
            self.data = {}
            self.data['raw_x'] = raw_data[::2]
            self.data['raw_y'] = raw_data[1::2]
            self.data['time_x'] = self.data['raw_x']
            self.data['time_y'] = self.data['raw_y']
            dt = self.data['time_x'][1]-self.data['time_x'][0]
            self.f_max =1/(2*dt)
            self.fourier_multithreading(self.data['time_y'])
            self.edits['time_cursor'].returnPressed.emit()

            self.draw('time')







    '''
    ################################################################################
    '''

    def draw(self,key):
        self.ax[key].clear()
        if key == 'time':
            self.ax[key].plot(self.data[key+'_x'],self.data[key+'_y'])
        elif key == 'freq':
            self.ax[key].plot(self.data[key+'_x'],np.abs(self.data[key+'_y']))
        value = [float(x) for x in self.edits[key+'_cursor'].text().split(' ')]
        self.vline[key+'_l'].set_xdata([value[0], value[0]])
        self.vline[key+'_r'].set_xdata([value[1], value[1]])

        self.canvas.draw()
        self.ax[key].ticklabel_format(style='sci', axis='both', scilimits=(0,0)) # format the tick label of the axes
        self.ax[key].draw_artist(self.vline[key+'_l'])
        self.ax[key].draw_artist(self.vline[key+'_r'])
        self.canvas.blit(self.ax[key].bbox)





'''
################################################################################
'''

app = QApplication(sys.argv)

window = MainWindow()
window.move(300,300)
window.show()
app.exec_()
