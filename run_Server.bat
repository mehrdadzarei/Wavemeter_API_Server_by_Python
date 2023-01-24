

@echo off
@REM set path of activeate.bat file
call C:\Users\srcal\anaconda3\Scripts\activate.bat

@REM set the path which you save the Server.py file
cd C:\Users\srcal\Desktop\mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP(server) Port(server) dllpath(wavemeter) Wavemeter_Version 
python Server.py "192.168.0.154" 5015 "C:\Windows\System32\wlmData.dll" 4499

@pause