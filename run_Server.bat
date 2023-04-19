

@echo off
@REM set path of activeate.bat file
call C:\Users\stront\Anaconda3\Scripts\activate.bat

@REM set the path which you save the Server.py file
cd C:\Users\stront\Mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP(server) Port(server) dllpath(wavemeter) Wavemeter_Version 
python Server.py "192.168.3.212" 5015 "C:\Windows\System32\wlmData.dll" 491

@pause