######################################################################################################
# @author Mehrdad Zarei <mzarei@umk.pl>
# @date 2021.07.18
# @version 0
#
# @brief wlm server to get information from wavelength meter and send to clients
#
######################################################################################################



import json
import threading
import socket
import ctypes
import sys
import time

from wlmConst import *



HEADER = 64
PORT = int(sys.argv[2])
SERVER = str(sys.argv[1])
# SERVER = socket.gethostbyname(socket.gethostname())   # for private server
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
time_out = 20.0

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

dllpath = "C:\Windows\System32\wlmData.dll"
dll = ctypes.WinDLL(dllpath)

dll.GetSwitcherMode.restype = ctypes.c_long
dll.SetSwitcherMode.restype = ctypes.c_long
dll.GetSwitcherChannel.restype = ctypes.c_long
dll.SetSwitcherChannel.restype = ctypes.c_long
dll.GetWavelengthNum.restype = ctypes.c_double
dll.GetFrequencyNum.restype = ctypes.c_double
dll.GetPatternItemSize.restype = ctypes.c_long
dll.GetPatternItemCount.restype = ctypes.c_long
dll.SetPattern.restype = ctypes.c_long
dll.GetPatternNum.restype = ctypes.POINTER(ctypes.c_ulong)
dll.GetAmplitudeNum.restype = ctypes.c_long
dll.GetExposureNum.restype = ctypes.c_long
dll.SetExposureNum.restype = ctypes.c_long
dll.GetExposureModeNum.restype = ctypes.c_long
dll.SetExposureModeNum.restype = ctypes.c_long
dll.GetExposureRange.restype = ctypes.c_long

DATATYPE_MAP = {2: ctypes.c_int, 4: ctypes.c_long, 8: ctypes.c_double}
dll.SetPattern(cSignal1WideInterferometer, cPatternEnable)
size = dll.GetPatternItemSize(cSignal1WideInterferometer)                         # the size dosen't change for pattern
count = dll.GetPatternItemCount(cSignal1WideInterferometer)                       # the count dosen't change for pattern
access_size = DATATYPE_MAP[size]*count
n = round(count / 2)



def my_send(conn, msg):

    total_sent = 0
    MSGLEN = len(msg)
    send_length = str(MSGLEN).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    # print(send_length)
    
    # waiting for reply
    while True:

        msg_recv = conn.recv(1)
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
    while total_sent < HEADER:
        
        sent = conn.send(send_length[total_sent:])
        if sent == 0:
            return -1
        total_sent += sent
    
    # waiting for reply
    while True:

        msg_recv = conn.recv(1)
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
        
        sent = conn.send(msg[total_sent:])
        if sent == 0:
            return -1
        total_sent = total_sent + sent

    # waiting for reply
    while True:

        msg_recv = conn.recv(1)
        if msg_recv == '':
            return -1
        try:
            if int(msg_recv) == 1:
                break
            elif int(msg_recv) == 0:
                return 0
        except Exception:
            break

    return 1

def my_recv(conn):

    chunks = []
    bytes_recd = 0
    
    conn.send(bytes("1".encode(FORMAT)))

    # recv msg len
    while bytes_recd < HEADER:
        
        chunk = conn.recv(min(HEADER - bytes_recd, HEADER))
        if chunk == '':
            return '-1'
        chunks.append(chunk.decode(FORMAT))
        bytes_recd += len(chunk)
        
    msg_len = ''.join(chunks)
    # print(msg_len)
    try:
        MSGLEN = int(msg_len)
        conn.send(bytes("1".encode(FORMAT)))
    except :
        conn.send(bytes("0".encode(FORMAT)))
        return '0'
    # print(MSGLEN)
    chunks = []
    bytes_recd = 0

    # recv msg
    while bytes_recd < MSGLEN:
        
        chunk = conn.recv(min(MSGLEN - bytes_recd, 1024))
        if chunk == '':
            return '-1'
        chunks.append(chunk.decode(FORMAT))
        bytes_recd += len(chunk)

    conn.send(bytes("1".encode(FORMAT)))

    return ''.join(chunks)

def handle_client(conn, addr):
    
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.settimeout(time_out)

    connected = True
    while connected:

        try:

            msg = my_recv(conn)
            if msg == '0':
                continue
            elif msg == '-1':
                connected = False
                continue
            # print(msg)
            obj_send = {}
            
            try:
                obj_recv = json.loads(msg)
            except :
                obj_recv = {}
            
            if "STATUS" in obj_recv and obj_recv["STATUS"] == DISCONNECT_MESSAGE:
            
                connected = False
                continue
            
            if "CH" in obj_recv:

                ch = obj_recv["CH"]
                
                if ch < 0 or ch > 9:
                    ch = 1
                
                if "SWITCH_MODE" in obj_recv and obj_recv["SWITCH_MODE"] == 1 and not dll.GetSwitcherMode():
                    # 0 for single mode and 1 for switch mode
                    dll.SetSwitcherMode(1)
                elif "SWITCH_MODE" in obj_recv and obj_recv["SWITCH_MODE"] == 0 and dll.GetSwitcherMode():
                    # 0 for single mode and 1 for switch mode
                    dll.SetSwitcherMode(0)
                    if ch != dll.GetSwitcherChannel():
                        dll.SetSwitcherChannel(ctypes.c_long(ch))
                        time.sleep(0.3)
                elif not dll.GetSwitcherMode() and ch != dll.GetSwitcherChannel():
                    dll.SetSwitcherChannel(ctypes.c_long(ch))
                    time.sleep(0.3)
                
                exp_mode = dll.GetExposureModeNum(ctypes.c_long(ch), 0)

                if "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 1 and not exp_mode:
                    dll.SetExposureModeNum(ctypes.c_long(ch), ctypes.c_bool(True))
                    time.sleep(1)
                    exp_mode = True
                elif "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 0 and exp_mode:
                    dll.SetExposureModeNum(ctypes.c_long(ch), ctypes.c_bool(False))
                    exp_mode = False

                if not exp_mode:
                    
                    if "EXP_UP" in obj_recv:
                        # mode 1 for interferometer
                        dll.SetExposureNum(ctypes.c_long(ch), ctypes.c_long(1), ctypes.c_long(obj_recv["EXP_UP"]))

                    if "EXP_DOWN" in obj_recv:
                        # mode 2 for wide interferometer
                        dll.SetExposureNum(ctypes.c_long(ch), ctypes.c_long(2), ctypes.c_long(obj_recv["EXP_DOWN"]))

                # change the numbers to str during transfer with json
                obj_send["EXP_UP"] = str(dll.GetExposureNum(ctypes.c_long(ch), ctypes.c_long(1)))
                obj_send["EXP_DOWN"] = str(dll.GetExposureNum(ctypes.c_long(ch), ctypes.c_long(2)))
                
                if "WAVEL" in obj_recv and obj_recv["WAVEL"] == 1:
                    # to keep laset digit if it is 0, we should use format
                    wavelength = '{:.5f}'.format(round(dll.GetWavelengthNum(ctypes.c_long(ch), ctypes.c_double(0)), 6))
                    obj_send["WAVEL"] = wavelength

                if "FREQ" in obj_recv and obj_recv["FREQ"] == 1:
                    freq = '{:.5f}'.format(round(dll.GetFrequencyNum(ctypes.c_long(ch), ctypes.c_double(0)), 6))
                    obj_send["FREQ"] = freq
                    
                if "SPEC" in obj_recv and obj_recv["SPEC"] == 1:
                    
                    address = dll.GetPatternNum(ctypes.c_long(ch), cSignal1WideInterferometer)   # the address dosen't change for a specific channel
                    memory_values = ctypes.cast(address, ctypes.POINTER(access_size))

                    spectrum_list = []
                    
                    for i in range(0, n):
                        spectrum_list.append(memory_values.contents[i])
                    
                    max_main = dll.GetAmplitudeNum(ctypes.c_long(ch), cMax2)
                    max_spec = max(spectrum_list)
                    if max_main == 0:
                    
                        max_main = max_spec = 1

                    try:
                        ratio = round(max_spec / max_main, 4)
                        # spectrum_list = np.divide(spectrum_list, ratio)
                        # spectrum_list = np.interp(np.linspace(0, n, count), np.arange(n), spectrum_list)
                    except :
                        ratio = 1

                    obj_send["RATIO"] = str(ratio)
                    obj_send["SPEC"] = spectrum_list
                    
            obj_send["SEND"] = " "
            data = json.dumps(obj_send)

            message = data.encode(FORMAT)
            
            err = my_send(conn, message)
            if err == 0:
                continue
            elif err == -1:
                connected = False
                continue

            # time.sleep(0.001)

        except Exception:
            
            print(f"[ERROR] connection {addr} is closing with error...")
            connected = False
            conn.close()

            return

    print(f"[CLOSING] connection {addr} is closing...")
    conn.close()

def start():

    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")
    cheking = True
    while cheking:

        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        # cheking = False
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")



print("[STARTING] server is starting...")
start()




