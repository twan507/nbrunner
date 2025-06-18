# NBRunner - Jupyter Notebook Runner

🚀 Ứng dụng Python nhỏ gọn để chạy và quản lý Jupyter Notebooks với giao diện Tkinter.

## 🔧 Hướng dẫn nhanh

### Setup (Thiết lập lần đầu)
```cmd
setup.bat
```
*Tạo môi trường ảo và cài đặt dependencies*

### Start (Chạy thử nghiệm)
```cmd
start.bat
```
*Khởi chạy ứng dụng trong chế độ development*

### Build (Đóng gói thành .exe)
```cmd
build.bat
```
*Tạo file thực thi standalone trong thư mục `app/`*

## 📁 Cấu trúc
```
nbrunner/
├── setup.bat      # 🔧 Thiết lập môi trường
├── start.bat      # ▶️ Chạy development
├── build.bat      # 📦 Đóng gói .exe
├── app/           # 🎯 Ứng dụng đã build
│   ├── nbrunner.exe
│   ├── notebooks/ # 📓 Đặt .ipynb files ở đây
│   └── modules/   # 🧩 Python modules
└── development/   # 💻 Source code
    ├── src/
    └── requirements.txt
```

## ✨ Tính năng chính
- ✅ Chạy multiple notebooks
- ⚡ Multi-threading execution
- 🔄 Auto-run scheduler
- 📊 Real-time console output
- 📦 Import custom modules
- 💾 Log management

## 🎯 Sử dụng
1. Đặt notebook files (`.ipynb`) vào `app/notebooks/`
2. Add Python modules vào `app/modules/`
3. Chạy `app/nbrunner.exe`
4. Chọn notebooks và nhấn "Run"

## 📋 Yêu cầu
- Windows OS
- Python 3.7+ (chỉ cần khi development)
