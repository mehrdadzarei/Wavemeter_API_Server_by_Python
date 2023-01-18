

@echo off

@REM call C:\Users\RydbergLaser\Anaconda3\Scripts\activate.bat
call C:\Users\mehrz\anaconda3\Scripts\activate.bat

@REM cd C:\Users\RydbergLaser\Desktop\Mehrdad
cd D:\Programming\KL FAMO\Wavemeter_API_Server_by_Python

python wlmClient.py "192.168.0.154" 5015


@pause

