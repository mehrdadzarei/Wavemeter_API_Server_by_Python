######################################################################################################
# @author Mehrdad Zarei <mzarei@umk.pl>
# @date 2022.01.24
# @version 0
#
# @brief API for DigiLock to control DUI (DigiLock User Interface) remotly 
#
######################################################################################################



import DigiLock
import sys
import time
import matplotlib.pyplot as plt


digi = DigiLock.digiClient()
digi_ip = str(sys.argv[1])
digi_port = int(sys.argv[2])
digi.connect(ip = digi_ip, port = digi_port)

# peak to peak level which you can measure from amplitude on DigiLock
digi.set_peakTpeak(ptp = float(sys.argv[3]))

err_con = digi.setting()
err_con, err = digi.checking()
if err == 0:
    err_con, err = digi.checking()
if err_con == 1 and err == 1:
    
    err_con, err = digi.lock()
    if err == 0:
        err_con, err = digi.lock()

up_t = 1
t1 = time.time()
while err_con == 1:

    # refresh digilock connection every 100 s to avoid freezing
    if (time.time() - t1) > 99:

        digi.__del__()
        time.sleep(1)
        digi_con = digi.connect(ip = digi_ip, port = digi_port)
        
        t1 = time.time()    # restart timing
            
    
    time.sleep(up_t)
    err_con, err, up_t = digi.check_lock()



# x, y = digi.get_graph()
# plt.plot(x, y, label='data')
# plt.title('Life time of Sr atoms in the Lattice', fontdict=self.font)
# plt.legend()
# plt.xlabel('SC110 out [V]', fontdict=digi.font)
# plt.ylabel('Main in [V]', fontdict=digi.font)
# plt.show()


digi.__del__()


