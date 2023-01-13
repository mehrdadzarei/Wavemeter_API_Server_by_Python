

@echo off

call C:\Users\srcal\anaconda3\Scripts\activate.bat

cd C:\Users\srcal\Desktop\mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP Port dllpath Wavemeter_Version 
python Server.py "192.168.0.154" 5015 "C:\Windows\System32\wlmData.dll" 4499
@REM python wavelength_meter.py

@pause