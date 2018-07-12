from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib

import numpy as np

import sys


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)
        # setting the window title
        self.setWindowTitle("test window")
        self.canvas = FigureCanvas(Figure(figsize=(15, 15)))
        self.fig = self.canvas.figure
        self.ax = self.fig.add_subplot(111)
        self.setCentralWidget(self.canvas)
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.lock = 'off'

    def on_press(self, event):
        self.lock = 'on'
        xmin,xmax = self.ax.get_xlim()
        self.xrange = xmax - xmin
        self.x0 = event.x
        self.hline = self.ax.axhline(y = event.y, xmin = event.x/self.xrange-0.01, xmax = event.x/self.xrange+0.01)
        self.hline.linewidth = 10
        self.hline.figure.canvas.draw()

    def on_release(self,event):
        self.lock = 'off'

    def on_motion(self, event):
        if self.lock == 'on':
            self.hline.set_xdata([self.x0,event.x])
            self.hline.linewidth = 10
            self.hline.figure.canvas.draw()



app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()
