######################################################################################################
# @author Mehrdad Zarei <mzarei@umk.pl>
# @date 2022.12.07
# @version 0
#
# @brief DigiLock to control DUI (DigiLock User Interface) remotly 
#
######################################################################################################



import socket
import time
import matplotlib.pyplot as plt



class digiClient:

    # ptp is peak to peak amplitude
    def __init__(self):

        self.font = {'family': 'serif',
                    'color':  'darkred',
                    'weight': 'normal',
                    'size': 11,
                    }
        
        self.upd_time = 5
        self.scan_amp = 5.0
        self.scan_amp2 = 0.3
        self.amp_max = 0.0
        self.prev_ptp = -1
        self.cnt = 0                    # No. of scaning to find the peak
        self.lock_point = 0
        self.nounlock = 0
        self.uncnt = 0            # No. of checking unclocked
        self.vol_offset = 0
        self.FORMAT = "utf-8"
        
    def __del__(self):

        try:
            self.client.close()
        except:
            pass
    
    def connect(self, ip = "192.168.0.175", port = 60001):

        ADDR = (ip, port)

        try:
            
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(ADDR)
            self.client.settimeout(20)
            msg = self.recive(1024)
            # to be sure is not connected to DMS on port 60000
            if len(msg) == 0 or "Welcome to DigiLock110 remote interface!" not in msg:
                self.client.close()
                return 0
            self.client.settimeout(1)

            return 1
        except:

            return 0

    def set_peakTpeak(self, ptp = 0.04):

        if self.prev_ptp != ptp:

            self.amp_thr = ptp * 0.7        # amp with scan amplitude 5 v, 70% for error
            self.amp_thr2 = ptp * 2.0       # amp with scan amplitude 1 v, 200% 
            self.prev_ptp = ptp
    
    def send(self, msg):
    
        # add \n before sending the command
        msg += "\n"
        message = msg.encode(self.FORMAT)
        self.client.send(message)
        time.sleep(0.1)     # have to put this delay
    
    def recive(self, n):
    
        chunks = []
        bytes_recd = 0
    
        # recv msg
        while bytes_recd < n:
        
            len_msg = min(n - bytes_recd, 1024)
            try:
                chunk = self.client.recv(len_msg)
                chunks.append(chunk.decode(self.FORMAT))
            except :
                chunk = ''
            
            bytes_recd += len(chunk)
            if len(chunk) < len_msg:
                n = bytes_recd
    
        return ''.join(chunks)

    def get_comm(self, comm= "offset:value", case = "f"):
        
        time.sleep(0.1)     # to be sure of data
        self.recive(8192)
        comm += " ?"
        self.send(comm)
        data = self.recive(51200)
        try:
            data = data.split('=')
            data = (data[len(data) - 1].split('\r'))[0]
        except :
            return 0, 0
    
        if case == "f":
            
            try:
                data = float(data)
            except :
                data = 0
            return 1, data
        elif case == "i":
            
            try:
                data = int(data)
            except :
                data = 0
            return 1, data
    
    def get_graph(self):
    
        time.sleep(0.1)     # to be sure of data
        self.recive(8192)
        self.send("autolock:display:graph ?")
        time.sleep(0.5)
        data = self.recive(51200)
        
        if len(data) == 0:
            x, y = self.get_graph()
            return x, y
    
        try:
            data = data.split('=')
            data = data[1].split('\n')
        except :
            pass
        x = []
        y = []
        for i in range(0, len(data)-1):
            try:

                tmp = data[i].split('\t')
                x.append(float(tmp[0]))
                y.append(float(tmp[1]))
                x.append(float(tmp[2]))
                y.append(float((tmp[3].split('\r'))[0]))
            except :
                break
        return x, y

    def setting(self):
    
        self.send("autolock:lock:enable=false")
        
        self.send("autolock:enable=true")
        self.send("autolock:input=Main in")
        self.send("autolock:spectrum=Main in")
        self.send("autolock:controller:pid1=false")
        self.send("autolock:controller:pid2=true")
        # self.send("autolock:window:channel=Main in")
        # self.send("autolock:window:enable=true")
        # self.send("autolock:window:maxin=1.400")
        # self.send("autolock:window:maxout=1.400")
        # self.send("autolock:window:minin=0.800")
        # self.send("autolock:window:minout=0.800")
        self.send("autolock:cursor:track=true")
        self.send("autolock:cursor:snap=true")
        self.send("autolock:smart:engage=true")
        self.send("autolock:smart:setpoint=true")
    
        self.send("offset:output=SC110 out")
    
        self.send("scan:signal type=triangle")
        self.send("scan:frequency=10")
        self.send("scan:output=SC110 out")
        self.send("scan:enable=true")
        time.sleep(0.5)       # to start new scan
    
    def checking(self):
    
        x, y = self.get_graph()
        try:
            amp = max(y) - min(y)
            # print(amp)
        except :
            time.sleep(1)
            err = self.checking()
            return err
 
        if amp > self.amp_thr2:
            
            try:
                # set the peak to the center
                offset = x[y.index(min(y))]
                command = "offset:value=%.4f" %offset
                self.send(command)
                command = "scan:amplitude=%.4f" %self.scan_amp2
                self.send(command)
                time.sleep(1)
                err = 1
            except :
                err = 0
        else:
        
            err, offset = self.get_comm("offset:value", "f")
            if err == 0:
                err, offset = self.get_comm("offset:value", "f")
            # print(offset)
            err = self.find_peak(offset, 12)
            if err == 0:

                offset = 0.0
                command = "offset:value=%.4f" %offset
                self.send(command)
                err = self.find_peak(offset, 24)
                if err == 0:
                    
                    command = "offset:value=%.4f" %offset
                    self.send(command)
        
        return err
        
    def find_peak(self, init_offset, no_step):
    
        self.cnt = 0
        command = "scan:amplitude=%.4f" %self.scan_amp
        self.send(command)
        
        while True:
        
            x, y = self.get_graph()
            try:
                amp = max(y) - min(y)
            except :
                continue
            # print(amp)
            if amp > self.amp_thr:

                try:

                    # set the peak to the center
                    offset = x[y.index(min(y))]
                    command = "offset:value=%.4f" %offset
                    self.send(command)
                    time.sleep(1)
                except :
                    continue
            
                # print("amp: %f" %amp)
                if amp > self.amp_thr2:
                    
                    if self.cnt == 0:
                        self.send("scan:amplitude=0.3000")
                        time.sleep(1)
                    return 1
                # 1.8 * self.amp_thr should be bigger than amp_thr enough to avoid other modes
                elif amp < self.amp_thr2 and amp > 1.8 * self.amp_thr:
                    
                    if self.cnt < no_step:
                        
                        offset = x[len(x) - 1] + abs(x[len(x) - 1])
                        command = "offset:value=%.4f" %offset
                        self.send(command)
                    elif self.cnt >= no_step and self.cnt <= (no_step * 2):
                        
                        offset = x[0] - abs(x[0])
                        command = "offset:value=%.4f" %offset
                        self.send(command)
                    continue
                else:
                    
                    self.send("scan:amplitude=1.000")
                    time.sleep(1)
                    continue
            else:
            
                self.cnt += 1
                if self.cnt < no_step:
                
                    # shift to right
                    try:
                        offset = x[len(x) - 1]
                    except :
                        continue
                    command = "offset:value=%.4f" %offset
                    self.send(command)
                    command = "scan:amplitude=%.4f" %self.scan_amp
                    self.send(command)
                elif self.cnt >= no_step and self.cnt <= (no_step * 2):
                
                    # shift to left
                    if self.cnt == no_step:
                        offset = init_offset
                    else:
                        offset = x[0]
                    command = "offset:value=%.4f" %offset
                    self.send(command)
                    command = "scan:amplitude=%.4f" %self.scan_amp
                    self.send(command)
                else:
                    command = "offset:value=%.4f" %init_offset
                    self.send(command)
                    return 0

                time.sleep(1)
    
    def lock(self):
    
        # stabilizing data
        time.sleep(self.cnt)
        x, y = self.get_graph()
        try:
            
            # set the peak to the center
            offset = x[y.index(min(y))]
            command = "offset:value=%.4f" %offset
            self.send(command)
            self.amp_max = max(y)
            amp = self.amp_max - min(y)
            # print(amp)
            set_point = min(y) + (amp * 0.35)
            self.lock_point = offset
        except :
            time.sleep(1)
            err = self.lock()
            return err
    
        if amp > self.amp_thr2:
            
            command = "scan:amplitude=%.4f" %self.scan_amp2
            self.send(command)
            command = "autolock:setpoint=%.3f" %set_point
            self.send(command)
            time.sleep(2)
            self.send("autolock:lock:enable=true")
            err = 1

            time.sleep(1)
            # err, y_c = self.get_comm("autolock:display:ch1:mean", "f")
            err, index = self.get_comm("autolock:display:cursor index", "i")
            if err == 0:
                index = 500
            # x_c = x[index]
            # y_c = y[index]
            # print(index, "\t", set_point, "\t", y_c, "\t", set_point * 1.01)
            if index < 2 or index > 999:
            # if y_c > set_point * 1.01:
                self.send("autolock:lock:enable=false")
                err = self.lock()
        else:

            err, offset = self.get_comm("offset:value", "f")
            if err == 0:
                offset = self.lock_point
            err = self.find_peak(offset, 12)
            if err == 0:

                offset = 0.0
                command = "offset:value=%.4f" %offset
                self.send(command)
                err = self.find_peak(offset, 24)
                if err == 0:
                    
                    command = "offset:value=%.4f" %offset
                    self.send(command)
            if err == 1:
                err = self.lock()

        return err
            
    def check_lock(self):

        x, y = self.get_graph()
        try:
            
            err = 1
            self.upd_time = 5
            amp_min = min(y)
            lp = x[y.index(amp_min)]
            shift = self.lock_point - lp

            print("shift is: %.4f" %shift)#, "\t", "offset voltage is: %.4f" %self.vol_offset)
            self.lock_point = lp
            
            if abs(shift) > 0.05 and abs(shift) < 0.25:

                self.uncnt += 1
                self.upd_time = 0.01
                if self.uncnt == 2:

                    self.uncnt = 0
                    self.send("autolock:lock:enable=false")
                    self.nounlock += 1
                    print("unlocked! %d" %self.nounlock)
                    self.upd_time = 5
                    err = 0
            elif abs(shift) >= 0.25:

                self.uncnt = 0
                self.send("autolock:lock:enable=false")
                self.nounlock += 1
                print("unlocked! %d" %self.nounlock)
                err = 0   
            
            # if amp_min > self.amp_max * 0.9:
            #     self.send("autolock:lock:enable=false")
            #     err = 0
            #     print("amp")

        except :
            pass

        return err
    
    def update(self):

        cnt = 0
        while True:

            cnt += 1
            time.sleep(self.upd_time)
            err = self.check_lock()
            if err == 0:
                err = self.lock()
                if err == 0:
                    break

            if cnt == 20:
                self.client.close()
                time.sleep(1)
                self.connect()
                cnt = 0



# digi = digiClient()
# digi.connect(ip = "192.168.0.175", port = 60001)
# digi.set_peakTpeak(ptp = 0.04)
# digi.setting()
# err = digi.checking()
# if err == 0:
#     err = digi.checking()
# if err == 1:
    
#     err = digi.lock()
#     if err == 0:
#         err = digi.lock()
#     if err == 1:
#         digi.update()     # in [s]


# x, y = digi.get_graph()

# plt.plot(x, y, label='data')
# # plt.title('Life time of Sr atoms in the Lattice', fontdict=self.font)
# # plt.legend()
# plt.xlabel('SC110 out [V]', fontdict=digi.font)
# plt.ylabel('Main in [V]', fontdict=digi.font)
# plt.show()





# digi.recive(8192)    # to clean the server bufer
# # wait before closeing the connection
# time.sleep(1)
# digi.client.close()