


import Client
import sys
#import matplotlib.pyplot as plt



wlm = Client.wlmClient()
wlm.connect(ip = str(sys.argv[1]), port = int(sys.argv[2]))

wlm.getWavelength(7)

# mode 0 for single mode and 1 for switch mode
wlm.setSwitchMode(0)
switch_mode = wlm.getSwitchMode()
print(switch_mode)

# mode 0 for manual expo and 1 for auto axpo
wlm.setExpoAuto(1)
exp = wlm.getExpoAuto()
print(exp)

#wlm.setExpUp(10)
#expup = wlm.getExpUp()
#print(expup)

#wlm.setExpDown(10)
#expdown = wlm.getExpDown()
#print(expdown)

# number of digits (precision of wavemeter)
wlm.setPrec(4)

# channel
wavel = wlm.getWavelength(7)
print(wavel)

# channel
freq = wlm.getFrequency(5)
print(freq)

# channel
spec = wlm.getSpectrum(7)
#plt.plot(spec)
#plt.show()

# channel
#all = wlm.getAll(7)
#print(all["freq"])

wlm.disconnect()


