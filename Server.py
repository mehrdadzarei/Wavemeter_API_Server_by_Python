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
import wavelength_meter



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
    wlm_state = True
    ch = 1

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
            
            if "WLM_RUN" in obj_recv and obj_recv["WLM_RUN"] == 1:

                if wlm_state:
                    wlm_state = False
                    wlm = wavelength_meter.WavelengthMeter(dllpath = str(sys.argv[3]), WlmVer = int(sys.argv[4]))
            
                if "SWITCH_MODE" in obj_recv:
                    
                    # 0 for single mode and 1 for switch mode
                    wlm.setSwitcherMode(obj_recv["SWITCH_MODE"])
                    
                if "CH" in obj_recv:

                    ch = obj_recv["CH"]
                    if ch < 1 or ch > 8:
                        ch = 1
                else:
                    ch = ch
                wlm.setSwitcherChannel(ch)

                if "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 1:
                    wlm.setExposureMode(ch, True)
                    exp_mode = True
                elif "EXP_AUTO" in obj_recv and obj_recv["EXP_AUTO"] == 0:
                    wlm.setExposureMode(ch, False)
                    exp_mode = False
                else:
                    exp_mode = wlm.getExposureMode(ch)

                if not exp_mode:
                    
                    if "EXP_UP" in obj_recv:
                        # mode 1 for interferometer
                        wlm.setExposure(ch, 1, obj_recv["EXP_UP"])

                    if "EXP_DOWN" in obj_recv:
                        # mode 2 for wide interferometer
                        wlm.setExposure(ch, 2, obj_recv["EXP_DOWN"])

                # change the numbers to str during transfer with json
                obj_send["EXP_UP"] = str(wlm.getExposure(ch, 1))
                obj_send["EXP_DOWN"] = str(wlm.getExposure(ch, 2))
                
                if "WAVEL" in obj_recv and obj_recv["WAVEL"] == 1:
                    # to keep laset digit if it is 0, we should use format
                    wavelength = '{:.5f}'.format(round(wlm.getWavelength(ch), 6))
                    obj_send["WAVEL"] = wavelength

                if "FREQ" in obj_recv and obj_recv["FREQ"] == 1:
                    freq = '{:.5f}'.format(round(wlm.getFrequency(ch), 6))
                    obj_send["FREQ"] = freq
                    
                if "SPEC" in obj_recv and obj_recv["SPEC"] == 1:
                    
                    spectrum_list = []

                    ratio, spectrum_list = wlm.spectrum(ch)
                    ratio = round(ratio, 4)

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




