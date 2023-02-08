

@echo off

@REM set path of activeate.bat file
call C:\Users\RydbergLaser\Anaconda3\Scripts\activate.bat

@REM set the path which you save the testDigiLock.py file
cd C:\Users\RydbergLaser\Desktop\Mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP(DigiLock) Port(DigiLock)
python testDigiLock.py "192.168.0.175" 60001 0.03


@pause

