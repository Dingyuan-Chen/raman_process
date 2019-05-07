#!/usr/bin/env python

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication,
        QDialog, QGridLayout, QHBoxLayout, QPushButton,
        QVBoxLayout, QFileDialog, QMessageBox, QSlider, QLabel)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
import sys
import numpy as np
import scipy.sparse as sparse
from numpy.linalg import norm
from sklearn import preprocessing

class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)
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
        QApplication.setPalette(QApplication.style().standardPalette())

        # layout
        uplayer = QHBoxLayout()
        uplayer.addWidget(self.upLabel)
        uplayer.addWidget(self.upslider)
        downlayer = QHBoxLayout()
        downlayer.addWidget(self.downLabel)
        downlayer.addWidget(self.downslider)
        topLayout = QVBoxLayout()
        topLayout.addLayout(uplayer)
        topLayout.addLayout(downlayer)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.load_Button, 0, 0, 1, 1)
        mainLayout.addWidget(self.canvas, 1, 0, 1, 100)
        mainLayout.addLayout(topLayout, 2, 0, 1, 30)
        mainLayout.addWidget(self.save_Button, 2, 80, 1, 10)
        self.setLayout(mainLayout)

        self.setWindowTitle("拉曼光谱")

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

    def _draw(self, spectrum):
        QApplication.processEvents()
        baseline_p = self.upslider.value()/5.0
        smooth_p = self.downslider.value()/5.0
        ax = self.figure.add_axes([0.1, 0.1, 0.8, 0.8])

        if os.path.exists(self.load_file):
            plt.cla()
            bir = np.array([[0, 100., 200., 1000]])  # the frequency regions devoid of signal, used by rp.baseline()
            y_corrected, background = baseline(spectrum[:, 0], spectrum[:, 1], bir, "arPLS", lam=10 ** baseline_p)
            y_smo_1 = whittaker(y_corrected[:, 0], Lambda=10 ** smooth_p)
            ax.plot(spectrum[:, 0], spectrum[:, 1], "k", label="raw data")
            ax.plot(spectrum[:, 0], y_smo_1, "r", label="corrected signal")
            self.data = np.hstack((spectrum[:, 0].reshape(-1, 1), y_smo_1.reshape(-1, 1)))
            self.canvas.draw()

def get_portion_interest(x,y,bir):
    birlen = np.array(bir.shape[0])

    sp = np.transpose(np.vstack((x.reshape(-1),y.reshape(-1))))
    ### selection of bir data
    for i in range(birlen):
        if i == 0:
            yafit = sp[np.where((sp[:,0]> bir[i,0]) & (sp[:,0] < bir[i,1]))]
        else:
            je = sp[np.where((sp[:,0]> bir[i,0]) & (sp[:,0] < bir[i,1]))]
            yafit = np.vstack((yafit,je))

    return yafit

def baseline(x_input, y_input, bir, method, **kwargs):
    # we get the signals in the bir
    yafit_unscaled = get_portion_interest(x_input, y_input, bir)

    # signal standard standardization with sklearn
    # this helps for polynomial fitting
    X_scaler = preprocessing.StandardScaler().fit(x_input.reshape(-1, 1))
    Y_scaler = preprocessing.StandardScaler().fit(y_input.reshape(-1, 1))

    # transformation
    y = Y_scaler.transform(y_input.reshape(-1, 1))

    yafit = np.copy(yafit_unscaled)
    yafit[:, 0] = X_scaler.transform(yafit_unscaled[:, 0].reshape(-1, 1))[:, 0]
    yafit[:, 1] = Y_scaler.transform(yafit_unscaled[:, 1].reshape(-1, 1))[:, 0]

    y = y.reshape(len(y_input))
    # optional parameters
    lam = kwargs.get('lam', 1.0 * 10 ** 5)
    ratio = kwargs.get('ratio', 0.01)

    N = len(y)
    D = sparse.csc_matrix(np.diff(np.eye(N), 2))
    w = np.ones(N)

    while True:
        W = sparse.spdiags(w, 0, N, N)
        Z = W + lam * D.dot(D.transpose())
        z = sparse.linalg.spsolve(Z, w * y)
        d = y - z
        # make d- and get w^t with m and s
        dn = d[d < 0]
        m = np.mean(dn)
        s = np.std(dn)
        wt = 1.0 / (1 + np.exp(2 * (d - (2 * s - m)) / s))
        # check exit condition and backup
        if norm(w - wt) / norm(w) < ratio:
            break
        w = wt

    baseline_fitted = z

    return y_input.reshape(-1, 1) - Y_scaler.inverse_transform(
        baseline_fitted.reshape(-1, 1)), Y_scaler.inverse_transform(baseline_fitted.reshape(-1, 1))

def whittaker(y,**kwargs):
    # optional parameters
    lam = kwargs.get('Lambda',1.0*10**5)

    # starting the algorithm
    L = len(y)
    D = sparse.csc_matrix(np.diff(np.eye(L), 2))
    w = np.ones(L)
    W = sparse.spdiags(w, 0, L, L)
    Z = W + lam * D.dot(D.transpose())
    z = sparse.linalg.spsolve(Z, w*y)

    return z

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec_()) 
