@echo off
REM build.bat - Dong goi ung dung thanh file .exe

echo.
echo =========================================
echo  Bat dau qua trinh dong goi ung dung
echo =========================================
echo.

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
if not exist "development\venv\Scripts\activate.bat" (
    echo Loi: Moi truong ao chua duoc thiet lap. Vui long chay setup.bat truoc.
    goto :end
)
call development\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Loi: Khong the kich hoat moi truong ao.
    goto :end
)
echo Da kich hoat moi truong ao.

REM Lay cac bien tu config.py bang cach chay mot script Python nho
echo Doc cau hinh tu config.py...

REM Doc tung bien mot cach rieng biet
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_NAME)"') do set APP_NAME=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.EXE_FILE_NAME)"') do set EXE_FILE_NAME=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.ICON_PATH)"') do set ICON_PATH=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_BUILD_DIR)"') do set APP_BUILD_DIR=%%a
set PYINSTALLER_EXTRA_ARGS_STR=

if not defined APP_NAME (
    echo Loi: Khong doc duoc APP_NAME tu config.py.
    goto :deactivate_and_end
)
if not defined EXE_FILE_NAME (
    echo Loi: Khong doc duoc EXE_FILE_NAME tu config.py.
    goto :deactivate_and_end
)
if not defined ICON_PATH (
    echo Loi: Khong doc duoc ICON_PATH tu config.py.
    goto :deactivate_and_end
)
if not defined APP_BUILD_DIR (
    echo Loi: Khong doc duoc APP_BUILD_DIR tu config.py.
    goto :deactivate_and_end
)

echo Cau hinh da doc:
echo   APP_NAME: %APP_NAME%
echo   EXE_FILE_NAME: %EXE_FILE_NAME%
echo   ICON_PATH: %ICON_PATH%
echo   APP_BUILD_DIR: %APP_BUILD_DIR%
echo   PYINSTALLER_EXTRA_ARGS: %PYINSTALLER_EXTRA_ARGS_STR%

REM Dam bao thu muc dich ton tai
if not exist "%APP_BUILD_DIR%" (
    echo Tao thu muc dich "%APP_BUILD_DIR%"...
    mkdir "%APP_BUILD_DIR%"
)

REM Don dep cac thu muc build va dist cu cua PyInstaller
echo Don dep cac thu muc build va dist cu...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Lenh PyInstaller
echo Bat dau dong goi voi PyInstaller...

REM Kiem tra xem icon co ton tai khong
set ICON_ARG=
set ICON_DATA_ARG=
if exist "%ICON_PATH%" (
    set ICON_ARG=--icon "%ICON_PATH%"
    set ICON_DATA_ARG=--add-data "%ICON_PATH%;."
    echo Su dung icon: %ICON_PATH%
) else (
    echo Canh bao: File icon khong ton tai: %ICON_PATH%
    echo Tiep tuc build ma khong co icon...
)

pyinstaller ^
    development\src\main.py ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    %ICON_ARG% ^
    %ICON_DATA_ARG% ^
    --clean ^
    %PYINSTALLER_EXTRA_ARGS_STR%

if %errorlevel% neq 0 (
    echo Loi: Qua trinh dong goi voi PyInstaller gap van de.
    goto :deactivate_and_end
)
echo PyInstaller da tao file thanh cong.

REM Di chuyen file .exe vao thu muc app
echo Di chuyen %EXE_FILE_NAME% vao thu muc %APP_BUILD_DIR%...
REM PyInstaller voi --onefile se tao file dist/APP_NAME.exe
if exist "dist\%APP_NAME%.exe" (    copy /y "dist\%APP_NAME%.exe" "%APP_BUILD_DIR%\%EXE_FILE_NAME%"
    if %errorlevel% neq 0 (
        echo Loi: Khong the sao chep file .exe.
    ) else (
        echo Da sao chep %EXE_FILE_NAME% thanh cong vao %APP_BUILD_DIR%.
    )
) else (
    echo Loi: Khong tim thay file %APP_NAME%.exe trong thu muc dist\.
    echo Vui long kiem tra lai qua trinh PyInstaller.
)

REM Don dep cac file va thu muc tam do PyInstaller tao ra
echo Don don cac file va thu muc tam PyInstaller...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "main.spec" del "main.spec"
if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"

echo.
echo =========================================
echo  Qua trinh dong goi hoan tat!
echo  Ban co the tim thay %EXE_FILE_NAME% tai %APP_BUILD_DIR%
echo =========================================
echo.

:deactivate_and_end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    conda deactivate >nul 2>&1
    if errorlevel 1 (
        call deactivate >nul 2>&1
    )
)
pause
exit /b %errorlevel%

:end
pause
exit /b %errorlevel%
