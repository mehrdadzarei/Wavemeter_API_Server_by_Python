

@echo off

@REM set path of activeate.bat file
call C:\Users\stront\Anaconda3\Scripts\activate.bat

@REM set the path which you save the Server.py file
cd C:\Users\stront\Mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP(server) Port(server)
python testClient.py "192.168.3.212" 5015


@pause

