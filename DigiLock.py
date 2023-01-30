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



class digiClient:

    def __init__(self):

        self.scan_amp = 5.0
        self.scan_amp2 = 0.3
        self.amp_max = 0.0
        self.amp_thr = 0.04 * 0.7        # amp with scan amplitude 5 v, 70% for error
        self.amp_thr2 = 0.04 * 2.0       # amp with scan amplitude 1 v, 200% 
        self.prev_ptp = -1
        self.cnt = 0                     # No. of scaning to find the peak
        self.lock_point = 0
        self.uncnt = 0                   # No. of checking unclocked
        self.vol_offset = 0
        self.shift_list = [1, 1]
        self.shift_cnt = 0

        self.FORMAT = "utf-8"
        
    def __del__(self):

        try:
            
            self.recive(8192)    # to clean the server bufer
            # wait before closeing the connection
            time.sleep(1)
            self.client.close()
        except:
            pass
    
    def connect(self, ip = "192.168.0.175", port = 60001):

        ADDR = (ip, port)

        try:
            
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(ADDR)
            self.client.settimeout(20)
            err_con, msg = self.recive(1024)
            # to be sure is not connected to DMS on port 60000
            if err_con == 0 or len(msg) == 0 or "Welcome to DigiLock110 remote interface!" not in msg:
                self.client.close()
                return 0
            self.client.settimeout(1)
            # print("done")
            return 1
        except:

            return 0

    def set_peakTpeak(self, ptp = 0.04):

        # ptp is peak to peak amplitude
        if self.prev_ptp != ptp:

            self.amp_thr = ptp * 0.7        # amp with scan amplitude 5 v, 70% for error
            self.amp_thr2 = ptp * 2.0       # amp with scan amplitude 1 v, 200% 
            self.prev_ptp = ptp
    
    def send(self, msg):
    
        err = 1
        # add \n before sending the command
        msg += "\n"
        message = msg.encode(self.FORMAT)
        try:
            self.client.send(message)
        # except ConnectionAbortedError:
        #     err = 0
        except Exception as e:
            
            # 10053 connection aborted, 10054 connection closed forcefuly
            if e.args[0] == 10053 or e.args[0] == 10054:
                err = 0
        time.sleep(0.1)     # have to put this delay

        return err
    
    def recive(self, n):
    
        chunks = []
        bytes_recd = 0
        err = 1

        # recv msg
        while bytes_recd < n:
        
            len_msg = min(n - bytes_recd, 1024)
            try:
                chunk = self.client.recv(len_msg)
                chunks.append(chunk.decode(self.FORMAT))
            except Exception as e:

                # 10053 connection aborted, 10054 connection closed forcefuly
                if e.args[0] == 10053 or e.args[0] == 10054:
                    return 0, ''.join(chunks)
                chunk = ''
            
            bytes_recd += len(chunk)
            if len(chunk) < len_msg:
                n = bytes_recd
    
        return err, ''.join(chunks)

    def get_comm(self, comm= "offset:value", case = "f"):
        
        time.sleep(0.1)     # to be sure of data
        err_con, msg = self.recive(8192)
        if err_con == 0:
            return err_con, 0, 0

        comm += " ?"
        if self.send(comm) == 0:
            return 0, 0, 0

        err_con, data = self.recive(51200)
        if err_con == 0:
            return err_con, 0, 0
        try:
            data = data.split('=')
            data = (data[len(data) - 1].split('\r'))[0]
        except :
            return err_con, 0, 0
    
        if case == "f":
            
            try:
                data = float(data)
            except :
                data = 0
            return err_con, 1, data
        elif case == "i":
            
            try:
                data = int(data)
            except :
                data = 0
            return err_con, 1, data
    
    def get_graph(self):
    
        time.sleep(0.1)     # to be sure of data
        err_con, msg = self.recive(8192)
        if err_con == 0:
            return err_con, 0, 0

        if self.send("autolock:display:graph ?") == 0:
            return 0, 0, 0

        time.sleep(0.5)
        err_con, data = self.recive(51200)
        if err_con == 0:
            return err_con, 0, 0
        
        # if len(data) == 0:
        #     err_con, x, y = self.get_graph()
        #     if err_con == 0:
        #         return err_con, 0, 0
        #     return err_con, x, y
    
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
        return err_con, x, y

    def setting(self):
    
        err = self.send("function:view=Lock")
        err = self.send("display:view=Autolock")
        
        err = self.send("autolock:lock:enable=false")
        
        err = self.send("autolock:enable=true")
        err = self.send("autolock:input=Main in")
        err = self.send("autolock:spectrum=Main in")
        err = self.send("autolock:controller:pid1=false")
        err = self.send("autolock:controller:pid2=true")
        # err = self.send("autolock:window:channel=Main in")
        # err = self.send("autolock:window:enable=true")
        # err = self.send("autolock:window:maxin=1.400")
        # err = self.send("autolock:window:maxout=1.400")
        # err = self.send("autolock:window:minin=0.800")
        # err = self.send("autolock:window:minout=0.800")
        err = self.send("autolock:cursor:track=true")
        err = self.send("autolock:cursor:snap=true")
        err = self.send("autolock:smart:engage=true")
        err = self.send("autolock:smart:setpoint=true")
    
        err = self.send("offset:output=SC110 out")
    
        err = self.send("scan:signal type=triangle")
        err = self.send("scan:frequency=10")
        err = self.send("scan:output=SC110 out")
        err = self.send("scan:enable=true")
        
        time.sleep(0.5)       # to start new scan

        return err
            
    def find_peak(self, init_offset, no_step):
    
        command = "scan:amplitude=%.4f" %self.scan_amp
        if self.send(command) == 0:
            return 0, 1
        
        if self.shift_list[0] < 0:          # start scaning from left
            self.cnt = no_step - 1
        else:
            self.cnt = 0
        
        while True:
        
            err_con, x, y = self.get_graph()
            if err_con == 0:
                return err_con, 1
            try:
                amp = max(y) - min(y)
            except :
                continue
            # print(amp)
            if amp > self.amp_thr:

                try:

                    # shift the peak to the center
                    offset = x[y.index(min(y))]
                    command = "offset:value=%.4f" %offset
                    if self.send(command) == 0:
                        return 0, 1

                    time.sleep(1)
                except :
                    continue
            
                # print("amp: %f" %amp)
                if amp > self.amp_thr2:
                    
                    if self.cnt == 0:
                        if self.send("scan:amplitude=0.3000") == 0:
                            return 0, 1
                        time.sleep(1)
                    return err_con, 1
                # 1.8 * self.amp_thr should be bigger than amp_thr enough to avoid other modes
                elif amp < self.amp_thr2 and amp > 1.8 * self.amp_thr:
                    
                    if self.cnt < no_step:
                        
                        offset = x[len(x) - 1] + abs(x[len(x) - 1])
                        command = "offset:value=%.4f" %offset
                        if self.send(command) == 0:
                            return 0, 1
                    elif self.cnt >= no_step and self.cnt <= (no_step * 2):
                        
                        offset = x[0] - abs(x[0])
                        command = "offset:value=%.4f" %offset
                        if self.send(command) == 0:
                            return 0, 1
                    continue
                else:
                    
                    if self.send("scan:amplitude=1.000") == 0:
                        return 0, 1
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
                    if offset > 90:             # don't apply more than of 90 v
                        self.cnt = no_step - 1
                        continue
                    command = "offset:value=%.4f" %offset
                    if self.send(command) == 0:
                        return 0, 1
                    command = "scan:amplitude=%.4f" %self.scan_amp
                    if self.send(command) == 0:
                        return 0, 1
                elif self.cnt >= no_step and self.cnt <= (no_step * 2):
                
                    # shift to left
                    if self.cnt == no_step:
                        offset = init_offset
                    else:
                        offset = x[0]
                    if offset < -90:             # don't apply less than of -90 v
                        self.cnt = no_step * 2
                        continue
                    command = "offset:value=%.4f" %offset
                    if self.send(command) == 0:
                        return 0, 1
                    command = "scan:amplitude=%.4f" %self.scan_amp
                    if self.send(command) == 0:
                        return 0, 1
                else:
                    command = "offset:value=%.4f" %init_offset
                    if self.send(command) == 0:
                        return 0, 1
                    return err_con, 0

                time.sleep(1)
    
    def checking(self):
    
        err_con, x, y = self.get_graph()
        if err_con == 0:
            return err_con, 1
        try:
            amp = max(y) - min(y)
            # print(amp)
        except:
            time.sleep(1)
            err_con, err = self.checking()
            if err_con == 0:
                return err_con, 1
            return err_con, err
 
        if amp > self.amp_thr2:
            
            try:
                # shift the peak to the center
                offset = x[y.index(min(y))]
                command = "offset:value=%.4f" %offset
                if self.send(command) == 0:
                    return 0, 1
                command = "scan:amplitude=%.4f" %self.scan_amp2
                if self.send(command) == 0:
                    return 0, 1
                time.sleep(1)
                err = 1
            except :
                err = 0
        else:
        
            err_con, err, offset = self.get_comm("offset:value", "f")
            if err_con == 0:
                return err_con, 1
            if err == 0:
                err_con, err, offset = self.get_comm("offset:value", "f")
                if err_con == 0:
                    return err_con, 1
            # print(offset)
            err_con, err = self.find_peak(offset, 6)
            if err_con == 0:
                return err_con, 1
            if err == 0:

                offset = 0.0
                command = "offset:value=%.4f" %offset
                if self.send(command) == 0:
                    return 0, 1
                self.shift_list[0] = 1          # don't care about direction
                err_con, err = self.find_peak(offset, 30)
                if err_con == 0:
                    return err_con, 1
                if err == 0:
                    
                    command = "offset:value=%.4f" %offset
                    if self.send(command) == 0:
                        return 0, 1
        
        return err_con, err

    def lock(self):
    
        # stabilizing data
        time.sleep(self.cnt)
        err_con, x, y = self.get_graph()
        if err_con == 0:
            return err_con, 1
        try:
            
            # shift the peak to the center
            offset = x[y.index(min(y))]
            command = "offset:value=%.4f" %offset
            if self.send(command) == 0:
                return 0, 1
            self.amp_max = max(y)
            amp = self.amp_max - min(y)
            # print(amp)
            set_point = min(y) + (amp * 0.35)
            self.lock_point = offset
        except :
            time.sleep(1)
            err_con, err = self.lock()
            if err_con == 0:
                return err_con, 1
            return err_con, err
    
        if amp > self.amp_thr2:
            
            command = "scan:amplitude=%.4f" %self.scan_amp2
            if self.send(command) == 0:
                return 0, 1
            command = "autolock:setpoint=%.3f" %set_point
            if self.send(command) == 0:
                return 0, 1
            
            err1 = self.send("autolock:cursor:track=true")
            err1 = self.send("autolock:cursor:snap=true")
            if err1 == 0:
                return 0, 1
            time.sleep(2)
            if self.send("autolock:lock:enable=true") == 0:
                return 0, 1
            err = 1

            time.sleep(1)
            # err_con, err, y_c = self.get_comm("autolock:display:ch1:mean", "f")
            err_con, err, index = self.get_comm("autolock:display:cursor index", "i")
            if err_con == 0:
                return err_con, 1
            if err == 0:
                index = 500
            # x_c = x[index]
            # y_c = y[index]
            # print(index, "\t", set_point, "\t", y_c, "\t", set_point * 1.01)
            if index < 2 or index > 999:
            # if y_c > set_point * 1.01:
                if self.send("autolock:lock:enable=false") == 0:
                    return 0, 1
                err_con, err = self.lock()
                if err_con == 0:
                    return err_con, 1
        else:

            err_con, err, offset = self.get_comm("offset:value", "f")
            if err_con == 0:
                return err_con, 1
            if err == 0:
                offset = self.lock_point
            err_con, err = self.find_peak(offset, 6)
            if err_con == 0:
                return err_con, 1
            if err == 0:

                offset = 0.0
                command = "offset:value=%.4f" %offset
                if self.send(command) == 0:
                    return 0, 1
                self.shift_list[0] = 1          # don't care about direction
                err_con, err = self.find_peak(offset, 30)
                if err_con == 0:
                    return err_con, 1
                if err == 0:
                    
                    command = "offset:value=%.4f" %offset
                    if self.send(command) == 0:
                        return 0, 1
            if err == 1:
                err_con, err = self.lock()
                if err_con == 0:
                    return err_con, 1

        return err_con, err
            
    def unlock(self):

        if self.send("autolock:lock:enable=false") == 0:
            return 0
        return 1
    
    def check_lock(self):

        err_con, x, y = self.get_graph()
        if err_con == 0:
            return err_con, 1, 2
        try:
            
            err = 1
            upd_time = 2
            amp_min = min(y)
            lp = x[y.index(amp_min)]
            shift = self.lock_point - lp
            if self.shift_cnt > 1:
                self.shift_cnt = 0
            self.shift_list[self.shift_cnt] = shift
            self.shift_cnt +=1

            # print("shift is: %.4f" %shift)#, "\t", "offset voltage is: %.4f" %self.vol_offset)
            
            if abs(shift) > 0.05 and abs(shift) < 0.25:

                self.uncnt += 1
                upd_time = 0.01
                err = 2
                # for safety, to be sure is unlocked
                if self.uncnt == 2:

                    self.uncnt = 0
                    if self.send("autolock:lock:enable=false") == 0:
                        return 0, 1, 2
                    err = 0
            elif abs(shift) >= 0.25:

                self.uncnt = 0
                if self.send("autolock:lock:enable=false") == 0:
                    return 0, 1, 2
                upd_time = 0.01
                err = 0   
            
            if err == 0:
                self.cnt = 0
                command = "offset:value=%.4f" %self.lock_point      # back to lock point
                if self.send(command) == 0:
                    return 0, 1, 2
                err_con, err = self.lock()
                if err_con == 0:
                    return err_con, 1, upd_time

            self.lock_point = lp
            
            # if amp_min > self.amp_max * 0.9:
                # if self.send("autolock:lock:enable=false") == 0:
                #     return 0, 1, 2
            #     err = 0
            #     print("amp")

        except :
            pass

        return err_con, err, upd_time
 

