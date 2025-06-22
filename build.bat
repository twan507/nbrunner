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
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.EXE_FILE_NAME)"') do set EXE_FILE_NAME=%%a


REM Don dep cac thu muc build va dist cu, va cac file exe + _internal cu trong app
echo Don dep cac thu muc cu...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Chi xoa file .exe va thu muc _internal cu trong app (giu nguyen data, modules, notebooks, output)
if exist "%APP_BUILD_DIR%\%EXE_FILE_NAME%" del /f /q "%APP_BUILD_DIR%\%EXE_FILE_NAME%"
if exist "%APP_BUILD_DIR%\_internal" rmdir /s /q "%APP_BUILD_DIR%\_internal"

REM Lenh PyInstaller build tu file .spec
echo Bat dau dong goi voi PyInstaller tu development/build.spec...
pyinstaller development/build.spec --noconfirm --distpath dist --workpath build

if %errorlevel% neq 0 (
    echo Loi: Qua trinh dong goi voi PyInstaller gap van de.
    goto :deactivate_and_end
)
echo PyInstaller da tao thu muc ung dung thanh cong.

REM *** SUA LOGIC: Build truc tiep vao thu muc app ***
echo Chuan bi thu muc phan phoi cuoi cung...

REM Tao thu muc app neu chua ton tai
if not exist "%APP_BUILD_DIR%" mkdir "%APP_BUILD_DIR%"

REM Di chuyen file .exe tu 'dist\%APP_NAME%' vao thu muc app
if exist "dist\%APP_NAME%\%EXE_FILE_NAME%" (
    move /Y "dist\%APP_NAME%\%EXE_FILE_NAME%" "%APP_BUILD_DIR%\" > nul
    echo Da di chuyen file '%EXE_FILE_NAME%' vao thu muc '%APP_BUILD_DIR%'.
) else (
    echo Loi: Khong tim thay file executable 'dist\%APP_NAME%\%EXE_FILE_NAME%'.
	goto :deactivate_and_end
)

REM Di chuyen thu muc _internal tu 'dist\%APP_NAME%' vao thu muc app (giu nguyen ten)
if exist "dist\%APP_NAME%\_internal" (
    move /Y "dist\%APP_NAME%\_internal" "%APP_BUILD_DIR%\_internal" > nul
    echo Da di chuyen thu muc '_internal' vao '%APP_BUILD_DIR%'.
) else (
    echo Loi: Khong tim thay thu muc '_internal' trong 'dist\%APP_NAME%'.
	goto :deactivate_and_end
)

REM Sao chep cac thu muc tu resources neu chua ton tai trong app
echo Kiem tra va sao chep cac thu muc can thiet...
if not exist "%APP_BUILD_DIR%\data" (
    xcopy /E /I /Y /Q "resources\data" "%APP_BUILD_DIR%\data\"
    echo Da sao chep thu muc 'data'.
)
if not exist "%APP_BUILD_DIR%\modules" (
    xcopy /E /I /Y /Q "resources\modules" "%APP_BUILD_DIR%\modules\"
    echo Da sao chep thu muc 'modules'.
)
if not exist "%APP_BUILD_DIR%\notebooks" (
    xcopy /E /I /Y /Q "resources\notebooks" "%APP_BUILD_DIR%\notebooks\"
    echo Da sao chep thu muc 'notebooks'.
)
if not exist "%APP_BUILD_DIR%\output" (
    mkdir "%APP_BUILD_DIR%\output" >nul 2>&1
    echo Da tao thu muc 'output'.
)


REM Don dep cac file va thu muc tam
echo Don dep...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"


echo.
echo =========================================
echo  Qua trinh dong goi hoan tat!
echo  File executable va thu muc _internal da duoc cap nhat tai: %APP_BUILD_DIR%
echo  File executable: %APP_BUILD_DIR%\%EXE_FILE_NAME%
echo  Thu muc _internal: %APP_BUILD_DIR%\_internal
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