import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import sys
import os
import time
import io
import traceback

# Import thư viện xử lý notebook
try:
    import nbformat
except ImportError:
    messagebox.showerror("Lỗi Import", "Không thể import nbformat. Vui lòng cài đặt thư viện cần thiết.")
    sys.exit(1)

# Import config
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
except ImportError:
    messagebox.showerror("Lỗi Config", "Không thể import config.py. Vui lòng đảm bảo file config.py tồn tại.")
    sys.exit(1)


class NotebookRunner:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_NAME)
        self.root.geometry("1000x700")

        # Thiết lập icon cho cửa sổ và taskbar
        self.set_window_icon()

        # Sử dụng ROOT_DIR từ config thay vì tính toán riêng
        self.base_path = config.ROOT_DIR

        # Đường dẫn đến thư mục modules và notebooks
        self.modules_path = config.MODULES_DIR
        self.notebooks_path = config.NOTEBOOKS_DIR  # Thêm modules path vào sys.path để có thể import
        if os.path.exists(self.modules_path):
            if self.modules_path not in sys.path:
                sys.path.insert(0, self.modules_path)
        else:
            print(f"Warning: Modules path does not exist: {self.modules_path}")

        # Queue để giao tiếp giữa các thread
        self.output_queue = queue.Queue()

        # Danh sách các thread đang chạy
        self.running_threads = {}

        # Biến điều khiển auto-run
        self.auto_run_enabled = False
        self.auto_run_interval = 60  # seconds
        self.auto_run_timer = None

        self.setup_ui()
        self.refresh_notebook_list()

        # Bắt đầu kiểm tra output queue
        self.check_output_queue()  # Xử lý sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_resource_path(self, relative_path):
        """
        Lấy đường dẫn tới resource, xử lý cả trường hợp development và production
        """
        if getattr(sys, "frozen", False):
            # Khi chạy từ .exe, PyInstaller đặt resource vào sys._MEIPASS
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            return os.path.join(base_path, relative_path)
        else:
            # Khi chạy từ source code
            return os.path.join(config.ROOT_DIR, relative_path)

    def set_window_icon(self):
        """
        Thiết lập icon cho cửa sổ ứng dụng và taskbar
        """
        try:
            if getattr(sys, "frozen", False):
                # Khi chạy từ .exe, icon được embed vào resource bundle
                icon_path = self.get_resource_path("logo.ico")
            else:
                # Khi chạy từ source code
                icon_path = config.ICON_PATH

            if os.path.exists(icon_path):
                # Thiết lập icon cho cửa sổ tkinter
                self.root.iconbitmap(icon_path)
                print(f"[INFO] Đã thiết lập icon: {icon_path}")
            else:
                print(f"[WARNING] Icon file không tồn tại: {icon_path}")
        except Exception as e:
            print(f"[ERROR] Không thể thiết lập icon: {e}")

    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nswe")

        # Cấu hình grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Panel trái - Danh sách notebooks
        left_frame = ttk.LabelFrame(main_frame, text="Notebooks", padding="5")
        left_frame.grid(row=0, column=0, rowspan=3, sticky="nswe", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        # Listbox với scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.grid(row=0, column=0, sticky="nswe")
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        self.notebook_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED)
        self.notebook_listbox.grid(row=0, column=0, sticky="nswe")

        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.notebook_listbox.yview)
        listbox_scrollbar.grid(row=0, column=1, sticky="ns")
        self.notebook_listbox.configure(yscrollcommand=listbox_scrollbar.set)

        # Nút điều khiển notebooks
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, sticky="we", pady=(5, 0))
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)

        self.run_button = ttk.Button(buttons_frame, text="Chạy Đã Chọn", command=self.run_selected_notebooks)
        self.run_button.grid(row=0, column=0, sticky="we", padx=(0, 2))

        self.run_all_button = ttk.Button(buttons_frame, text="Chạy Tất Cả", command=self.run_all_notebooks)
        self.run_all_button.grid(row=0, column=1, sticky="we", padx=(2, 2))

        self.stop_all_button = ttk.Button(buttons_frame, text="Dừng Tất Cả", command=self.stop_all_notebooks)
        self.stop_all_button.grid(row=0, column=2, sticky="we", padx=(2, 0))

        # Nút refresh
        refresh_button = ttk.Button(left_frame, text="Làm Mới Danh Sách", command=self.refresh_notebook_list)
        refresh_button.grid(row=2, column=0, sticky="we", pady=(5, 0))

        # Panel phải trên - Điều khiển
        control_frame = ttk.LabelFrame(main_frame, text="Điều Khiển", padding="5")
        control_frame.grid(row=0, column=1, sticky="we", pady=(0, 5))

        # Auto-run controls
        auto_run_frame = ttk.Frame(control_frame)
        auto_run_frame.grid(row=0, column=0, sticky="we")
        auto_run_frame.columnconfigure(2, weight=1)

        self.auto_run_var = tk.BooleanVar()
        auto_run_checkbox = ttk.Checkbutton(auto_run_frame, text="Tự động chạy", variable=self.auto_run_var, command=self.toggle_auto_run)
        auto_run_checkbox.grid(row=0, column=0, sticky=tk.W)

        ttk.Label(auto_run_frame, text="Mỗi").grid(row=0, column=1, padx=(10, 5))

        self.interval_var = tk.StringVar(value="60")
        interval_spinbox = ttk.Spinbox(auto_run_frame, from_=10, to=3600, textvariable=self.interval_var, width=10)
        interval_spinbox.grid(row=0, column=2, padx=(0, 5))

        ttk.Label(auto_run_frame, text="giây").grid(row=0, column=3)

        # Status frame
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=1, column=0, sticky="we", pady=(5, 0))
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Trạng thái:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="Sẵn sàng", foreground="green")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        # Panel phải dưới - Console output
        output_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="5")
        output_frame.grid(row=1, column=1, sticky="nswe")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_console = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=20)
        self.output_console.grid(row=0, column=0, sticky="nswe")

        # Console control buttons
        console_buttons_frame = ttk.Frame(output_frame)
        console_buttons_frame.grid(row=1, column=0, sticky="we", pady=(5, 0))

        clear_button = ttk.Button(console_buttons_frame, text="Xóa Console", command=self.clear_console)
        clear_button.grid(row=0, column=0, sticky=tk.W)

        save_log_button = ttk.Button(console_buttons_frame, text="Lưu Log", command=self.save_log)
        save_log_button.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        # Panel cuối - Thông tin
        info_frame = ttk.LabelFrame(main_frame, text="Thông Tin", padding="5")
        info_frame.grid(row=2, column=1, sticky="we", pady=(5, 0))

        info_text = f"Đường dẫn cơ sở: {self.base_path}\n"
        info_text += f"Thư mục modules: {self.modules_path}\n"
        info_text += f"Thư mục notebooks: {self.notebooks_path}"

        info_label = ttk.Label(info_frame, text=info_text, font=("Consolas", 8))
        info_label.grid(row=0, column=0, sticky=tk.W)

    def refresh_notebook_list(self):
        """Làm mới danh sách notebooks"""
        self.notebook_listbox.delete(0, tk.END)

        if not os.path.exists(self.notebooks_path):
            self.log_message(f"Thư mục notebooks không tồn tại: {self.notebooks_path}")
            return

        try:
            files = [f for f in os.listdir(self.notebooks_path) if f.endswith(".ipynb")]
            files.sort()

            for file in files:
                self.notebook_listbox.insert(tk.END, file)

            self.log_message(f"Đã tải {len(files)} notebook(s)")
        except Exception as e:
            self.log_message(f"Lỗi khi đọc thư mục notebooks: {str(e)}")

    def get_selected_notebooks(self):
        """Lấy danh sách notebooks đã được chọn"""
        selected_indices = self.notebook_listbox.curselection()
        return [self.notebook_listbox.get(i) for i in selected_indices]

    def get_all_notebooks(self):
        """Lấy tất cả notebooks"""
        return [self.notebook_listbox.get(i) for i in range(self.notebook_listbox.size())]

    def run_selected_notebooks(self):
        """Chạy các notebooks đã được chọn"""
        selected = self.get_selected_notebooks()
        if not selected:
            messagebox.showwarning("Chọn Notebook", "Vui lòng chọn ít nhất một notebook để chạy.")
            return

        for notebook in selected:
            self.run_notebook(notebook)

    def run_all_notebooks(self):
        """Chạy tất cả notebooks"""
        notebooks = self.get_all_notebooks()
        if not notebooks:
            messagebox.showwarning("Không có Notebook", "Không có notebook nào để chạy.")
            return

        for notebook in notebooks:
            self.run_notebook(notebook)

    def run_notebook(self, notebook_name):
        """Chạy một notebook trong thread riêng biệt"""
        if notebook_name in self.running_threads:
            self.log_message(f"[{notebook_name}] Đã đang chạy, bỏ qua...")
            return

        # Tạo thread mới để chạy notebook
        thread = threading.Thread(target=self._run_notebook_thread, args=(notebook_name,))
        thread.daemon = True
        self.running_threads[notebook_name] = thread
        thread.start()

        self.update_status()

    def _run_notebook_thread(self, notebook_name):
        """Chạy notebook trong thread (method private)"""
        notebook_path = os.path.join(self.notebooks_path, notebook_name)

        try:
            self.output_queue.put(f"[{notebook_name}] Bắt đầu chạy...")
            self.output_queue.put(f"[{notebook_name}] Đường dẫn: {notebook_path}")

            # Kiểm tra file tồn tại
            if not os.path.exists(notebook_path):
                raise FileNotFoundError(f"Notebook file không tồn tại: {notebook_path}")  # Đọc notebook
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)

            # Chuyển đổi notebook thành Python code bằng cách tự xử lý
            python_code = self.convert_notebook_to_python(notebook)

            self.output_queue.put(f"[{notebook_name}] Đã chuyển đổi thành Python code")

            # Đảm bảo modules có thể được import
            if self.modules_path not in sys.path:
                sys.path.insert(0, self.modules_path)

            # Tạo namespace riêng cho notebook
            notebook_globals = {
                "__name__": f"notebook_{notebook_name}",
                "__file__": notebook_path,
                "__builtins__": __builtins__,
            }

            # Chuyển hướng stdout và stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            captured_output = io.StringIO()

            try:
                sys.stdout = captured_output
                sys.stderr = captured_output

                # Thực thi code
                exec(python_code, notebook_globals)

                # Lấy output
                output = captured_output.getvalue()
                if output.strip():
                    self.output_queue.put(f"[{notebook_name}] Output:\n{output}")

                self.output_queue.put(f"[{notebook_name}] Hoàn thành thành công!")

            except Exception as e:
                error_msg = f"[{notebook_name}] Lỗi: {str(e)}\n{traceback.format_exc()}"
                self.output_queue.put(error_msg)

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except Exception as e:
            error_msg = f"[{notebook_name}] Lỗi khi đọc/chuyển đổi notebook: {str(e)}"
            self.output_queue.put(error_msg)

        finally:
            # Xóa thread khỏi danh sách đang chạy
            if notebook_name in self.running_threads:
                del self.running_threads[notebook_name]

            # Cập nhật trạng thái
            self.root.after(0, self.update_status)

    def stop_all_notebooks(self):
        """Dừng tất cả notebooks đang chạy"""
        if not self.running_threads:
            self.log_message("Không có notebook nào đang chạy.")
            return

        # Ghi log các notebook bị dừng
        for notebook_name in list(self.running_threads.keys()):
            self.log_message(f"[{notebook_name}] Đã được yêu cầu dừng...")

        # Xóa tất cả threads (threads sẽ tự kết thúc)
        self.running_threads.clear()
        self.update_status()

        messagebox.showinfo("Dừng Notebooks", "Đã gửi yêu cầu dừng tất cả notebooks.")

    def toggle_auto_run(self):
        """Bật/tắt chế độ tự động chạy"""
        self.auto_run_enabled = self.auto_run_var.get()

        if self.auto_run_enabled:
            try:
                self.auto_run_interval = int(self.interval_var.get())
                if self.auto_run_interval < 10:
                    self.auto_run_interval = 10
                    self.interval_var.set("10")
            except ValueError:
                self.auto_run_interval = 60
                self.interval_var.set("60")

            self.log_message(f"Đã bật tự động chạy mỗi {self.auto_run_interval} giây")
            self.schedule_auto_run()
        else:
            self.log_message("Đã tắt tự động chạy")
            if self.auto_run_timer:
                self.root.after_cancel(self.auto_run_timer)
                self.auto_run_timer = None

    def schedule_auto_run(self):
        """Lên lịch chạy tự động"""
        if self.auto_run_enabled:
            self.auto_run_timer = self.root.after(self.auto_run_interval * 1000, self.auto_run_execute)

    def auto_run_execute(self):
        """Thực thi auto-run"""
        if self.auto_run_enabled:
            self.log_message("=== Tự động chạy notebooks ===")
            self.run_all_notebooks()
            self.schedule_auto_run()

    def log_message(self, message):
        """Ghi message vào console"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.output_queue.put(formatted_message)

    def check_output_queue(self):
        """Kiểm tra queue và cập nhật console"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.output_console.insert(tk.END, message)
                self.output_console.see(tk.END)
        except queue.Empty:
            pass

        # Lên lịch kiểm tra lại sau 100ms
        self.root.after(100, self.check_output_queue)

    def update_status(self):
        """Cập nhật trạng thái hiển thị"""
        running_count = len(self.running_threads)
        if running_count > 0:
            self.status_label.config(text=f"Đang chạy {running_count} notebook(s)", foreground="orange")
        else:
            self.status_label.config(text="Sẵn sàng", foreground="green")

    def clear_console(self):
        """Xóa console"""
        self.output_console.delete(1.0, tk.END)
        self.log_message("Console đã được xóa.")

    def save_log(self):
        """Lưu log ra file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title="Lưu Log File"
            )

            if file_path:
                content = self.output_console.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log_message(f"Đã lưu log vào: {file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu log: {str(e)}")

    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        if self.running_threads:
            if messagebox.askokcancel("Thoát", "Có notebook đang chạy. Bạn có chắc muốn thoát?"):
                self.stop_all_notebooks()
                self.root.destroy()
        else:
            self.root.destroy()

    def convert_notebook_to_python(self, notebook):
        """
        Chuyển đổi notebook thành Python code mà không cần PythonExporter
        """
        python_lines = []

        for cell in notebook.cells:
            if cell.cell_type == "code":
                # Thêm separator comment
                python_lines.append(f"\n# %%\n# Cell: {cell.get('id', 'unknown')}\n")

                # Thêm source code của cell
                source = cell.source
                if isinstance(source, list):
                    source = "".join(source)

                python_lines.append(source)
                python_lines.append("\n")

        return "\n".join(python_lines)


def main():
    """Hàm main"""
    root = tk.Tk()
    # Thiết lập icon nếu có
    icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass  # Bỏ qua nếu không load được icon

    NotebookRunner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
