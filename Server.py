######################################################################################################
# @author Mehrdad Zarei <mzarei@umk.pl>
# @date 2021.07.18
# @version 0
#
# @brief Server to get information from wavelength meter and DigiLock to send them to the clients
#
######################################################################################################



import json
import threading
import socket
import sys
import time
from wlmConst import *
import wavelength_meter
import DigiLock



HEADER = 64
PORT = int(sys.argv[2])
SERVER = str(sys.argv[1])
# SERVER = socket.gethostbyname(socket.gethostname())   # for private server
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
time_out = 20.0

digi_update = False
digi_state = True
digi_con = 0
digi_err = 1            # 1 no error, 0 error
ptp_lvl = 0.04

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
wlm = wavelength_meter.WavelengthMeter(dllpath = str(sys.argv[3]), WlmVer = int(sys.argv[4]))
digi = DigiLock.digiClient()



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

def handle_digi(ip, port):

    global digi_update, digi_con, digi_err, ptp_lvl

    digi_con = digi.connect(ip = ip, port = port)

    if digi_con == 0:
        digi_update = True
        return
    
    digi.set_peakTpeak(ptp = ptp_lvl)
    digi.setting()
    digi_err = digi.checking()
    # check digi_con maybe it is changed by operator
    if digi_err == 0 and digi_con == 1:                        # try one more time
        digi_err = digi.checking()
    if digi_err == 1 and digi_con == 1:
        digi_err = digi.lock()
        if digi_err == 0 and digi_con == 1:                   # try one more time
            digi_err = digi.lock()   

    upd_t = 2           # update every 2 s
    t1 = time.time()    # start timing
    while digi_con != 0 and digi_err != 0:

        # refresh digilock connection every 100 s to avoid freezing
        if (time.time() - t1) > 99:

            digi.__del__()
            time.sleep(1)
            digi_con = digi.connect(ip = ip, port = port)

            if digi_con == 0:
                digi_update = True
                return

            t1 = time.time()    # restart timing

        digi.set_peakTpeak(ptp = ptp_lvl)
        
        digi_err = 2        # don't do anything before returning from check_lock which may takes long time
        digi_update = True
        digi_err, upd_t = digi.check_lock()

        digi_update = True
        time.sleep(upd_t)

    if digi_err == 0:
        digi_update = True
    
    digi.__del__()

def handle_client(conn, addr):
    
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.settimeout(time_out)

    global digi_state, digi_update, digi_con, digi_err, ptp_lvl
    
    connected = True
    
    wlm_state = True
    ch = 1
    switch_mode = -1
    exp_mode = False
    exp_up = -1
    exp_down = -1

    digi_update = False
    digi_state = True
    digi_con = 0
    digi_err = 1
    ptp_lvl = 0.04

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
                digi_con = 0
                continue
            
            if "WLM_RUN" in obj_recv and obj_recv["WLM_RUN"] == 1:

                if wlm_state:
                    wlm_state = False
                    wlm.run(action = 'show')    # show or hide
                    wlm.measurement(cCtrlStartMeasurement)   # state : cCtrlStopAll, cCtrlStartMeasurement
            
                if "CH" in obj_recv:

                    ch = obj_recv["CH"]
                    if ch < 1 or ch > 8:
                        ch = 1
                else:
                    ch = ch

                wlmSwitch_mode = wlm.getSwitcherMode()
                # take changes from wavemeter
                if wlmSwitch_mode != switch_mode:
                    switch_mode = wlmSwitch_mode
                # apply changes from operator
                elif "SWITCH_MODE" in obj_recv and obj_recv["SWITCH_MODE"] != switch_mode:

                    # 0 for single mode and 1 for switch mode
                    wlm.setSwitcherMode(obj_recv["SWITCH_MODE"])
                    switch_mode = obj_recv["SWITCH_MODE"]
                    if obj_recv["SWITCH_MODE"] == 1:
                        wlm.setSwitcherSignalStates(ch, 1, 0)
                obj_send["SWITCH_MODE"] = switch_mode

                wlm.setSwitcherChannel(ch)

                wlmExp_auto = wlm.getExposureMode(ch)
                # take changes from wavemeter
                if wlmExp_auto != exp_mode:
                    exp_mode = wlmExp_auto
                # apply changes from operator
                elif "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 1:
                    wlm.setExposureMode(ch, True)
                    exp_mode = True
                elif "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 0:
                    wlm.setExposureMode(ch, False)
                    exp_mode = False

                if not exp_mode:

                    wlmExp_up = wlm.getExposure(ch, 1)
                    # take changes from wavemeter
                    if wlmExp_up != exp_up:
                        exp_up = wlmExp_up
                    # apply changes from operator
                    elif "EXP_UP" in obj_recv:
                        # mode 1 for interferometer
                        wlm.setExposure(ch, 1, obj_recv["EXP_UP"])
                    
                    wlmExp_down = wlm.getExposure(ch, 2)
                    # take changes from wavemeter
                    if wlmExp_down != exp_down:
                        exp_down = wlmExp_down
                    # apply changes from operator
                    elif "EXP_DOWN" in obj_recv:
                        # mode 2 for wide interferometer
                        wlm.setExposure(ch, 2, obj_recv["EXP_DOWN"])

                exp_up = wlm.getExposure(ch, 1)
                exp_down = wlm.getExposure(ch, 2)
                if (exp_up > 1000 or exp_down > 1000) and exp_mode:
                    
                    wlm.setExposureMode(ch, False)
                    exp_mode = False
                    wlm.setExposure(ch, 1, 2)
                    exp_up = 2
                    wlm.setExposure(ch, 2, 2)
                    exp_down = 2

                # change the numbers to str during transfer with json
                obj_send["EXP_AUTO"] = 1 if exp_mode else 0
                obj_send["EXP_UP"] = str(exp_up)
                obj_send["EXP_DOWN"] = str(exp_down)
                
                if "PREC" in obj_recv:
                    prec = obj_recv["PREC"]
                else:
                    prec = 5
                
                if "WAVEL" in obj_recv and obj_recv["WAVEL"] == 1:
                    # to keep laset digit if it is 0, we should use format
                    # if your digits are variable use this
                    wavelength = f'{wlm.getWavelength(ch):.{prec}f}'
                    # wavelength = '{:.5f}'.format(round(wlm.getWavelength(ch), 6))
                    obj_send["WAVEL"] = wavelength
                else:
                    obj_send["WAVEL"] = "None"

                if "FREQ" in obj_recv and obj_recv["FREQ"] == 1:
                    # if your digits are variable use this
                    freq = f'{wlm.getFrequency(ch):.{prec}f}'
                    # freq = '{:.5f}'.format(round(wlm.getFrequency(ch), 6))
                    obj_send["FREQ"] = freq
                else:
                    obj_send["FREQ"] = "None"
                    
                if "SPEC" in obj_recv and obj_recv["SPEC"] == 1:
                    
                    spectrum_list = []

                    ratio, spectrum_list = wlm.spectrum(ch)
                    ratio = round(ratio, 4)

                    obj_send["RATIO"] = str(ratio)
                    obj_send["SPEC"] = spectrum_list
                else:
                    obj_send["RATIO"] = "None"
                    
            if "TRANSFER_LOCK" in obj_recv and obj_recv["TRANSFER_LOCK"] == 1:

                if digi_update:

                    digi_update = False
                    
                    obj_send["TRANSFER_LOCK"] = digi_con
                    obj_send["ERROR_STATE"] = digi_err
                    
                    if digi_con == 0 or digi_err == 0:
                        obj_send["TRANSFER_LOCK"] = 0       # overwrite, in case only error is 0
                        digi_state = True
                else:
                    obj_send["TRANSFER_LOCK"] = 2       # no update
                    obj_send["ERROR_STATE"] = 1         # no error
                
                if digi_state:
                    
                    digi_state = False
                    obj_send["ERROR_STATE"] = 2         # for the first time hold on till digi is locked
                    digi_err = 2                        # don't do anything for the first time which may takes long time

                    if "DIGI_IP" in obj_recv:
                        digi_ip = obj_recv["DIGI_IP"]
                    else:
                        digi_ip = "192.168.0.175"

                    if "DIGI_PORT" in obj_recv:
                        digi_port = obj_recv["DIGI_PORT"]
                    else:
                        digi_port = 60001

                    digi_thread = threading.Thread(target=handle_digi, args=(digi_ip, digi_port))
                    digi_thread.start()
                    
                if "PTP_LVL" in obj_recv:
                    ptp_lvl = obj_recv["PTP_LVL"]
                else:
                    ptp_lvl = 0.04

            else:
                
                if digi_err != 2:       # don't change parameters if it is in the check_lock

                    digi_err = 1
                    digi_con = 0
                    digi_state = True
                    digi_update = False

            obj_send["SEND"] = " "
            data = json.dumps(obj_send)

            message = data.encode(FORMAT)
            
            err = my_send(conn, message)
            if err == 0:
                continue
            elif err == -1:
                connected = False
                continue

        except Exception:
            
            print(f"[ERROR] connection {addr} is closing with error...")
            digi_con = 0
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




