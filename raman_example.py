#!/usr/bin/env python

from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QDateTimeEdit,
        QDialog, QGridLayout, QGroupBox, QHBoxLayout, QProgressBar, QPushButton,
        QStyleFactory, QVBoxLayout, QFileDialog, QMessageBox, QSlider, QLabel)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
import sys
import numpy as np
import rampy as rp

class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.resize(1000, 700)
        self.originalPalette = QApplication.palette()
        self.spectrum = None
        self.load_file = 'cc'
        self.data = None
        # button
        self.load_Button = QPushButton(self)
        self.load_Button.setObjectName("load")
        self.load_Button.setText("导入txt文件")
        self.load_Button.clicked.connect(self.loadf)

        self.save_Button = QPushButton(self)
        self.save_Button.setObjectName("save")
        self.save_Button.setText("导出文件")
        self.save_Button.clicked.connect(self.savef)

        #  plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # spin
        self.upLabel = QLabel("基线参数:")
        self.upslider = QSlider(Qt.Horizontal)
        self.upslider.setValue(25)
        self.upslider.setMinimum(0)
        self.upslider.setMaximum(100)

        self.downLabel = QLabel("平滑参数:")
        self.downslider = QSlider(Qt.Horizontal)
        self.downslider.setValue(25)
        self.downslider.setMinimum(0)
        self.downslider.setMaximum(100)

        self.upslider.sliderReleased.connect(lambda: self._draw(self.spectrum))
        self.downslider.sliderReleased.connect(lambda: self._draw(self.spectrum))

        # style
        self.useStylePaletteCheckBox = QCheckBox("&Use style's standard palette")
        self.useStylePaletteCheckBox.setChecked(True)

        # layout
        self.useStylePaletteCheckBox.toggled.connect(self.changePalette)

        uplayer = QHBoxLayout()
        uplayer.addWidget(self.upLabel)
        uplayer.addWidget(self.upslider)
        downlayer = QHBoxLayout()
        downlayer.addWidget(self.downLabel)
        downlayer.addWidget(self.downslider)
        topLayout = QVBoxLayout()
        topLayout.addLayout(uplayer)
        topLayout.addLayout(downlayer)

        topLayout.addStretch(1)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.load_Button, 0, 0, 1, 1)
        mainLayout.addWidget(self.canvas, 1, 0, 1, 100)
        mainLayout.addLayout(topLayout, 2, 0, 1, 30)
        mainLayout.addWidget(self.save_Button, 2, 80, 1, 10)
        self.setLayout(mainLayout)

        self.setWindowTitle("拉曼光谱")
        self.changeStyle('Windows XP')

    def loadf(self):
        self.load_file, filetype = QFileDialog.getOpenFileName(self,
                                                          "选取文件",
                                                          "./",
                                                          "TXT (*.txt)")
        if os.path.exists(self.load_file):
            path = self.load_file
            # open original txt
            spectrum = np.genfromtxt(path)
            if spectrum is not None:
                # plot the figure of the raman curve.
                self.spectrum = spectrum
                self._draw(spectrum)
            else:
                QMessageBox.information(self, "错误提醒",
                                        self.tr("文件内容缺失或错误"))

    def savef(self):
        self.save_file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if os.path.exists(self.save_file) and os.path.exists(self.load_file):
            # new excel
            out_f = os.path.join(self.save_file, '拉曼光谱处理结果.txt')
            f = open(out_f, 'w')
            for i in self.data:
                f.write(str(i[0]) + '\t' + str(i[1]) + '\r\n')
            f.close()
            QMessageBox.information(self, "消息提醒",
                                    self.tr("文件已导出到{}".format(out_f)))

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        self.changePalette()

    def changePalette(self):
        QApplication.setPalette(QApplication.style().standardPalette())

    def _draw(self, spectrum):
        QApplication.processEvents()
        baseline_p = self.upslider.value()/5.0
        smooth_p = self.downslider.value()/5.0
        ax = self.figure.add_axes([0.1, 0.1, 0.8, 0.8])

        if os.path.exists(self.load_file):
            plt.cla()
            bir = np.array([[0, 100., 200., 1000]])  # the frequency regions devoid of signal, used by rp.baseline()
            y_corrected, background = rp.baseline(spectrum[:, 0], spectrum[:, 1], bir, "arPLS", lam=10 ** baseline_p)
            y_smo_1 = rp.smooth(spectrum[:, 0], y_corrected[:, 0], method="whittaker", Lambda=10 ** smooth_p)
            ax.plot(spectrum[:, 0], spectrum[:, 1], "k", label="raw data")
            ax.plot(spectrum[:, 0], y_smo_1, "r", label="corrected signal")
            self.data = np.hstack((spectrum[:, 0].reshape(-1, 1), y_smo_1.reshape(-1, 1)))
            self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec_()) 
