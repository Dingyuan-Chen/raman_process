import matplotlib.pyplot as plt
import numpy as np
import rampy as rp

# spectrum = np.genfromtxt(r"D:\temp\rampy\examples\data/M2_42_1.txt")
#
# bir = np.array([[0,100., 200., 1000]]) # the frequency regions devoid of signal, used by rp.baseline()
# y_corrected, background = rp.baseline(spectrum[:,0],spectrum[:,1],bir,"arPLS",lam=10**5)
# y_smo_1 = rp.smooth(spectrum[:,0],y_corrected[:, 0], method="whittaker",Lambda=10**5)
# plt.figure()
# plt.plot(spectrum[:,0],spectrum[:,1],"k",label="raw data")
# # plt.plot(spectrum[:,0],background,"k",label="background")
# plt.plot(spectrum[:,0],y_smo_1,"k",label="corrected signal")
# plt.show()
