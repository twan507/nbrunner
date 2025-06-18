@echo off
REM setup.bat - Thiet lap moi truong ao va cai dat thu vien

echo.
echo ====================================
echo  Bat dau thiet lap moi truong ao
echo ====================================
echo.

REM Kiem tra xem Python da duoc cai dat va co trong PATH chua
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Loi: Python khong tim thay trong PATH.
    echo Vui long cai dat Python phien ban 3.x va them no vao bien moi truong PATH.
    goto :end
)

REM Tao moi truong ao neu chua ton tai
if not exist "development\venv" (
    echo Tao moi truong ao tai development\venv...
    python -m venv development\venv
    if %errorlevel% neq 0 (
        echo Loi: Khong the tao moi truong ao.
        goto :end
    )
    echo Da tao moi truong ao thanh cong.
) else (
    echo Moi truong ao development\venv da ton tai. Bo qua buoc tao.
)

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
call development\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Loi: Khong the kich hoat moi truong ao.
    goto :end
)
echo Da kich hoat moi truong ao.

REM Cai dat cac thu vien tu requirements.txt trong thu muc development
echo Cai dat cac thu vien tu development/requirements.txt...
pip install --upgrade pip
pip install -r development\requirements.txt
if %errorlevel% neq 0 (
    echo Loi: Khong the cai dat cac thu vien.
    goto :deactivate_and_end
)
echo Da cai dat tat ca thu vien thanh cong.

echo.
echo ==========================================
echo  Thiet lap hoan tat. San sang de phat trien.
echo ==========================================
echo.
goto :deactivate_and_end

:deactivate_and_end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    call deactivate
)
pause
exit /b %errorlevel%

:end
pause
exit /b %errorlevel%
