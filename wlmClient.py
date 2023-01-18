######################################################################################################
# @author Mehrdad Zarei <mzarei@umk.pl>
# @date 2021.07.28
# @version 0
#
# @brief wlm client to get information of wavelength meter from server
#
######################################################################################################



import json
import socket
import numpy as np
# import matplotlib.pyplot as plt



class wlmClient:

    def __init__(self, client = None, time_out = 20):
        
        self.header = 64
        self.format = "utf-8"
        self.discon_msg = "!DISCONNECT"
        self.wavel = 0
        self.freq = 0
        self.ratio = 1
        self.spec = []
        self.spectrum_list = []
        
        if client is None:

            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(time_out)
        else:
            self.client = client

    def connect(self, ip = "192.168.0.154", port = 5015):
        
        self.client.connect((ip, port))

    def disconnect(self):

        obj_send = {"STATUS": self.discon_msg}
        data = json.dumps(obj_send)
        message = data.encode(self.format)
        self.my_send(message)

        self.client.close()

    def my_send(self, msg):

        total_sent = 0
        MSGLEN = len(msg)
        send_length = str(MSGLEN).encode(self.format)
        send_length += b' ' * (self.header - len(send_length))
        # print(send_length)

        # waiting for reply
        while True:

            msg_recv = self.client.recv(1)
            if msg_recv == '':
                return -1
            try:
                if int(msg_recv) == 1:
                    break
                elif int(msg_recv) == 0:
                    return 0
            except Exception:
                break

        # send msg len
        while total_sent < self.header:

            sent = self.client.send(send_length[total_sent:])
            if sent == 0:
                return -1
            total_sent += sent

        # waiting for reply
        while True:

            msg_recv = self.client.recv(1)
            if msg_recv == '':
                return -1
            try:
                if int(msg_recv) == 1:
                    break
                elif int(msg_recv) == 0:
                    return 0
            except Exception:
                break

        # send msg
        total_sent = 0
        while total_sent < MSGLEN:

            sent = self.client.send(msg[total_sent:])
            if sent == 0:
                return -1
            total_sent = total_sent + sent

        # waiting for reply
        while True:

            msg_recv = self.client.recv(1)
            if msg_recv == '':
                return -1
            try:
                if int(msg_recv) == 1:
                    break
                elif int(msg_recv) == 0:
                    return 0
            except Exception:
                break

    def my_recv(self):

        chunks = []
        bytes_recd = 0

        self.client.send(bytes("1".encode(self.format)))

        # recv msg len
        while bytes_recd < self.header:

            chunk = self.client.recv(min(self.header - bytes_recd, self.header))
            if chunk == '':
                return '-1'
            chunks.append(chunk.decode(self.format))
            bytes_recd += len(chunk)

        msg_len = ''.join(chunks)
        # print(msg_len)
        try:
            MSGLEN = int(msg_len)
            self.client.send(bytes("1".encode(self.format)))
        except :
            self.client.send(bytes("0".encode(self.format)))
            return '0'
        # print(MSGLEN)
        chunks = []
        bytes_recd = 0

        # recv msg
        while bytes_recd < MSGLEN:

            chunk = self.client.recv(min(MSGLEN - bytes_recd, 1024))
            if chunk == '':
                return '-1'
            chunks.append(chunk.decode(self.format))
            bytes_recd += len(chunk)

        self.client.send(bytes("1".encode(self.format)))

        return ''.join(chunks)

    def extractData(self, obj_recv = {}):

        if "WAVEL" in obj_recv:
            self.wavel = obj_recv["WAVEL"]

        if "FREQ" in obj_recv:
            self.freq = obj_recv["FREQ"]
        
        if "RATIO" in obj_recv:
            self.ratio = obj_recv["RATIO"]
        
        if "SPEC" in obj_recv:
            
            self.spectrum_list = []
            self.spec = obj_recv["SPEC"]

            self.spectrum_list = np.divide(self.spec, self.ratio)
            self.spectrum_list = np.interp(np.linspace(0, 1024, 2048), np.arange(1024), self.spectrum_list)
    
    def getWavelength(self, ch = 1):

        obj_send = {"WLM_RUN": 1, "CH": ch, "WAVEL": 1}
        data = json.dumps(obj_send)
        message = data.encode(self.format)
        err = self.my_send(message)

        if err == 0:
            return -31          # retry again
        elif err == -1:
            self.client.close()
            return -30          # connection is closed

        msg = self.my_recv()
        if msg == '0':
            return -31          # retry again
        elif msg == '-1':
            self.client.close()
            return -30          # connection is closed

        try:
            obj_recv = json.loads(msg)
        except :
            obj_recv = {}
        
        self.extractData(obj_recv)

        return self.wavel

    def getFrequency(self, ch = 1):

        obj_send = {"WLM_RUN": 1, "CH": ch, "FREQ": 1}
        data = json.dumps(obj_send)
        message = data.encode(self.format)
        err = self.my_send(message)

        if err == 0:
            return -31          # retry again
        elif err == -1:
            self.client.close()
            return -30          # connection is closed

        msg = self.my_recv()
        if msg == '0':
            return -31          # retry again
        elif msg == '-1':
            self.client.close()
            return -30          # connection is closed
            
        try:
            obj_recv = json.loads(msg)
        except :
            obj_recv = {}

        self.extractData(obj_recv)
        
        return self.freq

    def getSpectrum(self, ch = 1):

        obj_send = {"WLM_RUN": 1, "CH": ch, "SPEC": 1}
        data = json.dumps(obj_send)
        message = data.encode(self.format)
        err = self.my_send(message)

        if err == 0:
            return -31          # retry again
        elif err == -1:
            self.client.close()
            return -30          # connection is closed

        msg = self.my_recv()
        if msg == '0':
            return -31          # retry again
        elif msg == '-1':
            self.client.close()
            return -30          # connection is closed
            
        try:
            obj_recv = json.loads(msg)
        except :
            obj_recv = {}
        
        self.extractData(obj_recv)

        return self.spectrum_list

    def getAll(self, ch = 1):

        obj_send = {"WLM_RUN": 1, "CH": ch, "WAVEL": 1, "FREQ": 1, "SPEC": 1}
        data = json.dumps(obj_send)
        message = data.encode(self.format)
        err = self.my_send(message)

        if err == 0:
            return -31          # retry again
        elif err == -1:
            self.client.close()
            return -30          # connection is closed

        msg = self.my_recv()
        if msg == '0':
            return -31          # retry again
        elif msg == '-1':
            self.client.close()
            return -30          # connection is closed
            
        try:
            obj_recv = json.loads(msg)
        except :
            obj_recv = {}
        
        self.extractData(obj_recv)

        return {"wavelength": self.wavel, "freq": self.freq, "spec": self.spectrum_list}



# wlm = wlmClient()
# wlm.connect()
# wavel = wlm.getWavelength(7)
# print(wavel)
# freq = wlm.getFrequency(7)
# print(freq)
# spec = wlm.getSpectrum(7)
# plt.plot(spec)
# plt.show()
# all = wlm.getAll(7)
# print(all["freq"])
# wlm.disconnect()

