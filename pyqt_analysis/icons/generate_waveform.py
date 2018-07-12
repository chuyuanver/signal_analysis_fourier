import matplotlib.pyplot as plt
import numpy as np

plt.figure(figsize=[6, 6])
x = np.arange(0, 100, 0.01)
y = np.cos(x*12500)*np.exp(-x/0.8)
plt.plot(np.fft.rfft(y,norm = "ortho").real)
# plt.axis('off')
# plt.gca().set_position([0, 0, 1, 1])
# plt.savefig("test.svg")
plt.show()
