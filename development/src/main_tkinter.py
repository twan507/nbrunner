import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
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
        self.root.resizable(True, True)

        # --- Cấu trúc dữ liệu cho Sections ---
        self.sections = {}
        self.next_section_id = 0

        # Các biến theo dõi card và lựa chọn
        self.available_notebook_cards = {}
        self.highlighted_available = set()

        self.set_window_icon()

        self.base_path = config.ROOT_DIR
        self.modules_path = config.MODULES_DIR
        self.notebooks_path = config.NOTEBOOKS_DIR
        if os.path.exists(self.modules_path) and self.modules_path not in sys.path:
            sys.path.insert(0, self.modules_path)

        self.output_queue = queue.Queue()
        self.running_threads = {}

        self.setup_ui()
        self.refresh_notebook_list()

        self._update_window_size(initial=True)

        self.check_output_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _update_window_size(self, initial=False):
        """Cập nhật kích thước cửa sổ để vừa với nội dung."""
        self.root.update_idletasks()
        req_width = self.root.winfo_reqwidth()
        fixed_height = 700
        self.root.minsize(req_width + 10, fixed_height)
        if initial:
            self.root.geometry(f"{req_width + 10}x{fixed_height}")

    def get_resource_path(self, relative_path):
        if getattr(sys, "frozen", False):
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            return os.path.join(base_path, relative_path)
        return os.path.join(config.ROOT_DIR, relative_path)

    def set_window_icon(self):
        try:
            icon_path = self.get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"[ERROR] Không thể thiết lập icon: {e}")

    def setup_ui(self):
        """Thiết lập giao diện người dùng với layout pack và tự động co giãn."""
        global style
        style = ttk.Style()
        style.configure("CanvasFrame.TFrame", background="#ffffff")
        style.configure("Card.TFrame", background="white", borderwidth=1, relief="solid")
        style.configure("Selected.TFrame", background="#cce5ff", borderwidth=1, relief="solid")

        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. Cột Log (bên trái) ---
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        log_container = ttk.LabelFrame(log_frame, text="Console Log", padding=5)
        log_container.pack(fill=tk.BOTH, expand=True)
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)

        self.output_console = scrolledtext.ScrolledText(log_container, wrap=tk.WORD, width=50)
        self.output_console.grid(row=0, column=0, sticky="nsew")

        log_controls_frame = ttk.Frame(log_container)
        log_controls_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        ttk.Button(log_controls_frame, text="Xóa Console", command=self.clear_console).pack(side=tk.LEFT)

        # --- 2. Cột Notebooks có sẵn & Điều khiển toàn cục ---
        available_frame_container = ttk.Frame(main_frame)
        available_frame_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        available_frame = ttk.LabelFrame(available_frame_container, text="Notebooks có sẵn", padding=5)
        available_frame.pack(fill=tk.BOTH, expand=True)
        available_frame.grid_rowconfigure(0, weight=1)
        available_frame.grid_columnconfigure(0, weight=1)

        self.available_canvas = tk.Canvas(available_frame, borderwidth=0, background="#ffffff", highlightthickness=0, width=280)
        self.available_cards_frame = ttk.Frame(self.available_canvas, style="CanvasFrame.TFrame")
        available_scrollbar = ttk.Scrollbar(available_frame, orient="vertical", command=self.available_canvas.yview)
        self.available_canvas.configure(yscrollcommand=available_scrollbar.set)
        available_scrollbar.grid(row=0, column=1, sticky="ns")
        self.available_canvas.grid(row=0, column=0, sticky="nsew")
        self.available_canvas_window = self.available_canvas.create_window((0, 0), window=self.available_cards_frame, anchor="nw")
        self.available_cards_frame.bind(
            "<Configure>", lambda e: self.available_canvas.configure(scrollregion=self.available_canvas.bbox("all"))
        )
        self.available_canvas.bind("<Configure>", lambda e: self.available_canvas.itemconfig(self.available_canvas_window, width=e.width))

        global_controls = ttk.LabelFrame(available_frame_container, text="Điều khiển toàn cục", padding=5)
        global_controls.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        ttk.Button(global_controls, text="Làm Mới Danh Sách", command=self.refresh_notebook_list).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(global_controls, text="Dừng Tất Cả", command=self.stop_all_notebooks).pack(fill=tk.X)

        # --- 3. Khu vực Sections (động) ---
        self.sections_container = ttk.Frame(main_frame)
        self.sections_container.pack(side=tk.LEFT, fill=tk.Y)

        self.add_section_button = ttk.Button(self.sections_container, text="+", command=self._add_section, width=3)
        self.add_section_button.pack(side=tk.LEFT, fill=tk.Y)

    def _add_section(self):
        """Tạo một cột section mới, pack nó vào trước nút Add và mở rộng cửa sổ."""
        section_id = self.next_section_id
        self.next_section_id += 1

        section_name = f"Section {section_id + 1}"

        # Tạm thời gỡ nút add ra
        self.add_section_button.pack_forget()

        section_frame = ttk.LabelFrame(self.sections_container, text=section_name, padding=5)
        section_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        section_frame.grid_rowconfigure(1, weight=1)
        section_frame.grid_columnconfigure(0, weight=1)

        header_frame = ttk.Frame(section_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)
        title_label = ttk.Label(header_frame, text=section_name, font=("Segoe UI", 10, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        title_label.bind("<Double-1>", lambda e, sid=section_id: self._rename_section(sid))
        ttk.Button(header_frame, text="X", width=2, command=lambda sid=section_id: self._close_section(sid)).grid(
            row=0, column=1, sticky="e"
        )

        canvas = tk.Canvas(section_frame, borderwidth=0, background="#ffffff", highlightthickness=0, width=280)
        cards_frame = ttk.Frame(canvas, style="CanvasFrame.TFrame")
        scrollbar = ttk.Scrollbar(section_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas_window = canvas.create_window((0, 0), window=cards_frame, anchor="nw")
        cards_frame.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.bind("<Configure>", lambda e, c=canvas, cw=canvas_window: c.itemconfig(cw, width=e.width))

        buttons_frame = ttk.Frame(section_frame)
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        buttons_frame.columnconfigure((0, 1), weight=1)
        ttk.Button(buttons_frame, text="<< Thêm", command=lambda sid=section_id: self._move_to_section(sid)).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5)
        )
        ttk.Button(buttons_frame, text="Chạy Chọn", command=lambda sid=section_id: self._run_highlighted_in_section(sid)).grid(
            row=1, column=0, sticky="ew", padx=(0, 2)
        )
        ttk.Button(buttons_frame, text="Chạy Section", command=lambda sid=section_id: self._run_section(sid)).grid(
            row=1, column=1, sticky="ew", padx=(2, 0)
        )
        ttk.Button(buttons_frame, text="Bỏ chọn >>", command=lambda sid=section_id: self._move_from_section(sid)).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0)
        )

        self.sections[section_id] = {
            "name": section_name,
            "frame": section_frame,
            "title_label": title_label,
            "canvas": canvas,
            "cards_frame": cards_frame,
            "notebook_cards": {},
            "highlighted": set(),
        }

        # Pack lại nút Add ở cuối
        self.add_section_button.pack(side=tk.LEFT, fill=tk.Y)
        # Cập nhật kích thước cửa sổ
        self._update_window_size()

    def _close_section(self, section_id):
        """Xóa một cột section và thu hẹp cửa sổ."""
        if messagebox.askyesno("Xác nhận Xóa", f"Bạn có chắc muốn xóa '{self.sections[section_id]['name']}'?"):
            section = self.sections[section_id]
            for path in list(section["notebook_cards"].keys()):
                self._create_card_in_list(
                    path,
                    self.available_cards_frame,
                    self.available_notebook_cards,
                    self.highlighted_available,
                    self._on_card_click_available,
                )
            section["frame"].destroy()
            del self.sections[section_id]
            self.available_canvas.configure(scrollregion=self.available_canvas.bbox("all"))
            # Cập nhật kích thước cửa sổ
            self._update_window_size()

    def _rename_section(self, section_id):
        """Cho phép người dùng đổi tên section."""
        current_name = self.sections[section_id]["name"]
        new_name = simpledialog.askstring("Đổi tên Section", "Nhập tên mới:", initialvalue=current_name, parent=self.root)
        if new_name and new_name.strip():
            self.sections[section_id]["name"] = new_name
            self.sections[section_id]["frame"].config(text=new_name)
            self.sections[section_id]["title_label"].config(text=new_name)

    def _on_card_click_available(self, event, path):
        self._toggle_highlight(event, path, self.available_notebook_cards, self.highlighted_available)

    def _on_card_click_in_section(self, event, path, section_id):
        section = self.sections[section_id]
        self._toggle_highlight(event, path, section["notebook_cards"], section["highlighted"])

    def _toggle_highlight(self, event, path, card_list, selection_set):
        is_ctrl_pressed = (event.state & 4) != 0
        is_highlighted = path in selection_set

        if not is_ctrl_pressed:
            current_selection = list(selection_set)
            for p in current_selection:
                self._unhighlight_card(p, card_list, selection_set)
            if not is_highlighted or len(current_selection) > 1:
                self._highlight_card(path, card_list, selection_set)
        else:
            if is_highlighted:
                self._unhighlight_card(path, card_list, selection_set)
            else:
                self._highlight_card(path, card_list, selection_set)

    def _highlight_card(self, path, card_list, selection_set):
        card_info = card_list.get(path)
        if card_info and not card_info.get("highlighted"):
            card_info["highlighted"] = True
            selection_set.add(path)
            card_info["frame"].config(style="Selected.TFrame")
            for widget in card_info["frame"].winfo_children():
                widget.config(background=style.lookup("Selected.TFrame", "background"))

    def _unhighlight_card(self, path, card_list, selection_set):
        card_info = card_list.get(path)
        if card_info and card_info.get("highlighted"):
            card_info["highlighted"] = False
            selection_set.discard(path)
            card_info["frame"].config(style="Card.TFrame")
            for widget in card_info["frame"].winfo_children():
                widget.config(background=style.lookup("Card.TFrame", "background"))

    def refresh_notebook_list(self):
        for widget in self.available_cards_frame.winfo_children():
            widget.destroy()
        self.available_notebook_cards.clear()
        self.highlighted_available.clear()
        paths_in_sections = {path for sec in self.sections.values() for path in sec["notebook_cards"]}

        try:
            if not os.path.exists(self.notebooks_path):
                raise FileNotFoundError
            notebook_files = sorted([f for f in os.listdir(self.notebooks_path) if f.endswith(".ipynb")])
            available_files = [fn for fn in notebook_files if os.path.join(self.notebooks_path, fn) not in paths_in_sections]

            if not available_files:
                ttk.Label(self.available_cards_frame, text="Tất cả notebooks\nđã được chọn.", justify=tk.CENTER).pack(pady=20)
                return

            for filename in available_files:
                path = os.path.join(self.notebooks_path, filename)
                self._create_card_in_list(
                    path,
                    self.available_cards_frame,
                    self.available_notebook_cards,
                    self.highlighted_available,
                    self._on_card_click_available,
                )
        except Exception as e:
            ttk.Label(self.available_cards_frame, text=f"Lỗi: {e}", wraplength=250).pack()

        self.available_cards_frame.update_idletasks()
        self.available_canvas.config(scrollregion=self.available_canvas.bbox("all"))

    def _create_card_in_list(self, path, parent_frame, card_list, selection_set, on_click_handler):
        filename = os.path.basename(path)
        card_frame = ttk.Frame(parent_frame, style="Card.TFrame", padding=5)
        card_frame.pack(fill="x", pady=2, padx=2)
        description = self.get_notebook_description(path)
        lbl_filename = ttk.Label(card_frame, text=filename, font=("Segoe UI", 10, "bold"), background="white")
        lbl_filename.pack(anchor="w", fill="x")
        lbl_desc = ttk.Label(card_frame, text=description, font=("Segoe UI", 9), justify=tk.LEFT, background="white")
        lbl_desc.pack(anchor="w", fill="x", pady=(2, 0))
        card_list[path] = {"frame": card_frame, "highlighted": False}
        card_frame.bind("<Button-1>", lambda e, p=path: on_click_handler(e, p))
        lbl_filename.bind("<Button-1>", lambda e, p=path: on_click_handler(e, p))
        lbl_desc.bind("<Button-1>", lambda e, p=path: on_click_handler(e, p))

    def get_notebook_description(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "markdown":
                    source = "".join(cell.source)
                    for line in source.split("\n"):
                        if line.strip().startswith("# "):
                            return line.strip()[2:].strip()
            return "Không có mô tả"
        except Exception:
            return "Không thể đọc mô tả."

    def _move_to_section(self, section_id):
        if not self.highlighted_available:
            return
        section = self.sections[section_id]
        for path in list(self.highlighted_available):
            card_info = self.available_notebook_cards.pop(path)
            card_info["frame"].destroy()
            self._create_card_in_list(
                path,
                section["cards_frame"],
                section["notebook_cards"],
                section["highlighted"],
                lambda e, p=path, sid=section_id: self._on_card_click_in_section(e, p, sid),
            )
        self.highlighted_available.clear()
        self.available_canvas.configure(scrollregion=self.available_canvas.bbox("all"))
        section["canvas"].configure(scrollregion=section["canvas"].bbox("all"))

    def _move_from_section(self, section_id):
        section = self.sections[section_id]
        if not section["highlighted"]:
            return
        for path in list(section["highlighted"]):
            card_info = section["notebook_cards"].pop(path)
            card_info["frame"].destroy()
            self._create_card_in_list(
                path, self.available_cards_frame, self.available_notebook_cards, self.highlighted_available, self._on_card_click_available
            )
        section["highlighted"].clear()
        self.available_canvas.configure(scrollregion=self.available_canvas.bbox("all"))
        section["canvas"].configure(scrollregion=section["canvas"].bbox("all"))

    def _run_highlighted_in_section(self, section_id):
        section = self.sections[section_id]
        paths_to_run = list(section["highlighted"])
        if not paths_to_run:
            return
        self.log_message(f"--- Chạy mục đã chọn trong '{section['name']}' ---")
        for path in paths_to_run:
            self.run_notebook(path)

    def _run_section(self, section_id):
        section = self.sections[section_id]
        paths_to_run = list(section["notebook_cards"].keys())
        if not paths_to_run:
            return
        self.log_message(f"--- Chạy tất cả trong '{section['name']}' ---")
        for path in paths_to_run:
            self.run_notebook(path)

    def run_notebook(self, notebook_path):
        notebook_name = os.path.basename(notebook_path)
        if notebook_path in self.running_threads:
            self.log_message(f"[{notebook_name}] Đang chạy, bỏ qua.")
            return
        thread = threading.Thread(target=self._run_notebook_thread, args=(notebook_path,))
        thread.daemon = True
        self.running_threads[notebook_path] = thread
        thread.start()

    def _run_notebook_thread(self, notebook_path):
        notebook_name = os.path.basename(notebook_path)
        try:
            self.output_queue.put(f"[{notebook_name}] Bắt đầu...")
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
            python_code = self.convert_notebook_to_python(notebook)
            notebook_globals = {"__name__": f"nb_{notebook_name}", "__file__": notebook_path}
            old_stdout, old_stderr = sys.stdout, sys.stderr
            captured_output = io.StringIO()
            try:
                sys.stdout = sys.stderr = captured_output
                exec(python_code, notebook_globals)
                output = captured_output.getvalue()
                if output.strip():
                    self.output_queue.put(f"[{notebook_name}] Output:\n{output}")
                self.output_queue.put(f"[{notebook_name}] Hoàn thành!")
            except Exception as e:
                self.output_queue.put(f"[{notebook_name}] Lỗi: {e}\n{traceback.format_exc()}")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
        except Exception as e:
            self.output_queue.put(f"[{notebook_name}] Lỗi đọc file: {e}")
        finally:
            if notebook_path in self.running_threads:
                del self.running_threads[notebook_path]

    def stop_all_notebooks(self):
        if not self.running_threads:
            self.log_message("Không có notebook nào đang chạy.")
            return
        self.log_message(f"Gửi yêu cầu dừng {len(self.running_threads)} notebooks...")
        self.running_threads.clear()
        messagebox.showinfo("Dừng Notebooks", "Đã gửi yêu cầu dừng tất cả notebooks.")

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.output_queue.put(f"[{timestamp}] {message}\n")

    def check_output_queue(self):
        try:
            while True:
                self.output_console.insert(tk.END, self.output_queue.get_nowait())
        except queue.Empty:
            pass
        self.output_console.see(tk.END)
        self.root.after(100, self.check_output_queue)

    def clear_console(self):
        self.output_console.delete(1.0, tk.END)

    def on_closing(self):
        if self.running_threads and messagebox.askokcancel("Thoát", "Notebook đang chạy, bạn chắc chắn muốn thoát?"):
            self.root.destroy()
        elif not self.running_threads:
            self.root.destroy()

    def convert_notebook_to_python(self, notebook):
        lines = []
        for cell in notebook.cells:
            if cell.cell_type == "code":
                lines.append("".join(cell.source))
        return "\n\n".join(lines)


def main():
    root = tk.Tk()
    NotebookRunner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
