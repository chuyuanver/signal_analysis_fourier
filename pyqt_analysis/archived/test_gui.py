from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

class MyQAction(QAction):
    '''
    edit action to also give a key with the toggle state
    '''
    btnToggled = pyqtSignal(bool, str) # (checked, key)
    def __init__(self, icon, text, key, parent=None):
        super(MyQAction, self).__init__(icon, text, parent)
        self.setCheckable(True)
        self.key = key
        self.toggled.connect(self.checked)

    def checked(self, is_checked):
        self.btnToggled.emit(is_checked, self.key)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__()
        self.toolbar = self.addToolBar('nsor_toolbar') #add a tool bar to the window
        btn = MyQAction(QIcon(r'C:\Users\yue\ownCloud\Yue\python\pyqt_analysis\icons\auto_time_x.png'),'&Move Cursor', 'xyz',self)
        self.toolbar.addAction(btn)
        btn.btnToggled.connect(self.test)

    def test(self, toggle_state, key):
        print(toggle_state,key)

app = QApplication(sys.argv)

window = MainWindow()
window.move(300,300)
window.show()
app.exec_()
