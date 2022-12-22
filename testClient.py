

import wlmClient
import sys
import matplotlib.pyplot as plt



wlm = wlmClient()
wlm.connect(ip = str(sys.argv[1]), port = int(sys.argv[2]))
wavel = wlm.getWavelength(7)
print(wavel)
freq = wlm.getFrequency(7)
print(freq)
spec = wlm.getSpectrum(7)
plt.plot(spec)
plt.show()

# all = wlm.getAll(7)
# print(all["freq"])

wlm.disconnect()



