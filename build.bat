@echo off
REM build.bat - Dong goi ung dung theo kieu ONE-FOLDER tu file .spec

echo.
echo =========================================
echo  Bat dau qua trinh dong goi ONE-FOLDER
echo =========================================
echo.

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
if not exist "development\venv\Scripts\activate.bat" (
    echo Loi: Moi truong ao chua duoc thiet lap. Vui long chay setup.bat truoc.
    goto :end
)
call development\venv\Scripts\activate.bat
echo Da kich hoat moi truong ao.

REM Doc ten thu muc build tu config de phuc vu viec sao chep
echo Doc cau hinh tu config.py...
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_NAME)"') do set APP_NAME=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_BUILD_DIR)"') do set APP_BUILD_DIR=%%a


REM Don dep cac thu muc build va dist cu, bao gom ca thu muc app cu
echo Don dep cac thu muc cu...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%APP_BUILD_DIR%" rmdir /s /q "%APP_BUILD_DIR%"

REM Lenh PyInstaller build tu file .spec
echo Bat dau dong goi voi PyInstaller tu development/build.spec...
pyinstaller development/build.spec --noconfirm --distpath dist --workpath build

if %errorlevel% neq 0 (
    echo Loi: Qua trinh dong goi voi PyInstaller gap van de.
    goto :deactivate_and_end
)
echo PyInstaller da tao thu muc ung dung thanh cong.

REM *** SUA LOI LOGIC: Su dung MOVE thay cho REN ***
echo Chuan bi thu muc phan phoi cuoi cung...

REM Di chuyen thu muc output tu 'dist' ra ngoai va doi ten thanh 'app'
if exist "dist\%APP_NAME%" (
    move /Y "dist\%APP_NAME%" "%APP_BUILD_DIR%" > nul
    echo Da tao thu muc '%APP_BUILD_DIR%' hoan chinh.
) else (
    echo Loi: Khong tim thay thu muc output 'dist\%APP_NAME%'.
	goto :deactivate_and_end
)

REM Sao chep thu muc notebooks va modules vao thu muc app
echo Sao chep 'notebooks' va 'modules'...
xcopy /E /I /Y /Q "resources\notebooks" "%APP_BUILD_DIR%\notebooks\"
xcopy /E /I /Y /Q "resources\modules" "%APP_BUILD_DIR%\modules\"


REM Don dep cac file va thu muc tam
echo Don dep...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"


echo.
echo =========================================
echo  Qua trinh dong goi hoan tat!
echo  Thu muc ung dung hoan chinh da san sang tai: %APP_BUILD_DIR%
echo =========================================
echo.

:deactivate_and_end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    call deactivate >nul 2>&1
)
pause
exit /b %errorlevel%

:end
pause
exit /b %errorlevel%