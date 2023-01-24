

@echo off

@REM set path of activeate.bat file
call C:\Users\srcal\anaconda3\Scripts\activate.bat

@REM set the path which you save the testClient.py file
cd C:\Users\srcal\Desktop\mehrdad\Wavemeter_API_Server_by_Python

@REM args: IP(server) Port(server)
python testClient.py "192.168.0.154" 5015


@pause

