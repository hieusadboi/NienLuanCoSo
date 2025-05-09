import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import requests
from io import BytesIO
import webbrowser
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký font Arial hỗ trợ Unicode (tiếng Việt)
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))

# Kết nối tới MySQL
def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="hieu05012004x@X",
        database="quanlyquanan"
    )

# Tạo giao diện Tkinter hiện đại
class ModernQuanAnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Quản Lý Quán Ăn")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f5f5f5")
        
        # Thiết lập phông chữ
        self.font_title = ("Arial", 18, "bold")
        self.font_subtitle = ("Arial", 14)
        self.font_normal = ("Arial", 12)
        self.font_small = ("Arial", 10)
        
        # Kết nối DB và lấy danh sách món ăn
        self.conn = connect_db()
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT ma_mon, ten_mon, gia, hinh_anh_url, mo_ta FROM mon_an WHERE con_ban = TRUE")
        self.menus = self.cursor.fetchall()

        self.order_items = []  # Lưu chi tiết đơn hàng
        self.menu_quantities = [0] * len(self.menus)  # Số lượng cho từng món
        self.total_price = 0  # Tổng tiền
        
        # Tạo style cho ttk
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TButton", font=self.font_normal, padding=6)
        self.style.configure("TLabel", background="#f5f5f5", font=self.font_normal)
        self.style.configure("Title.TLabel", font=self.font_title, background="#f5f5f5")
        self.style.configure("Subtitle.TLabel", font=self.font_subtitle, background="#f5f5f5")
        self.style.configure("Total.TLabel", font=("Arial", 14, "bold"), foreground="red")
        self.style.configure("MenuCard.TFrame", background="white", borderwidth=1, relief="solid", padding=5)
        self.style.configure("Order.TFrame", background="white", borderwidth=1, relief="solid", padding=10)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.title_label = ttk.Label(header_frame, text="HỆ THỐNG QUẢN LÝ QUÁN ĂN", style="Title.TLabel")
        self.title_label.pack(side=tk.LEFT)
        
        # Thêm nút hỗ trợ
        help_btn = ttk.Button(header_frame, text="Hỗ trợ", command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # Main content
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Menu section
        menu_frame = ttk.Frame(main_frame, style="MenuCard.TFrame")
        menu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        menu_title = ttk.Label(menu_frame, text="THỰC ĐƠN", style="Subtitle.TLabel")
        menu_title.pack(pady=(0, 10))
        
        # Canvas và Scrollbar cho menu
        menu_canvas = tk.Canvas(menu_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(menu_frame, orient="vertical", command=menu_canvas.yview)
        scrollable_frame = ttk.Frame(menu_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: menu_canvas.configure(
                scrollregion=menu_canvas.bbox("all")
            )
        )
        
        menu_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        menu_canvas.configure(yscrollcommand=scrollbar.set)
        
        menu_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Hiển thị các món ăn trong scrollable_frame
        self.menu_items_frame = ttk.Frame(scrollable_frame)
        self.menu_items_frame.pack(fill=tk.BOTH, expand=True)
        
        for menu in self.menus:
            self.display_menu_item(menu)
        
        # Order section
        order_frame = ttk.Frame(main_frame, width=350, style="Order.TFrame")
        order_frame.pack(side=tk.RIGHT, fill=tk.Y)
        order_frame.pack_propagate(False)
        
        order_title = ttk.Label(order_frame, text="ĐƠN HÀNG", style="Subtitle.TLabel")
        order_title.pack(pady=(0, 10))
        
        # Danh sách đơn hàng
        self.order_listbox = tk.Listbox(
            order_frame, 
            font=self.font_normal, 
            height=15,
            selectmode=tk.SINGLE,
            activestyle="none",
            relief="flat",
            bg="white",
            highlightthickness=0
        )
        self.order_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Nút xóa món đã chọn
        remove_btn = ttk.Button(
            order_frame, 
            text="Xóa món đã chọn", 
            command=self.remove_selected_item,
            style="TButton"
        )
        remove_btn.pack(fill=tk.X, pady=5)
        
        # Tổng tiền
        total_frame = ttk.Frame(order_frame)
        total_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(total_frame, text="Tổng tiền:", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self.total_label = ttk.Label(total_frame, text="0 VND", style="Total.TLabel")
        self.total_label.pack(side=tk.RIGHT)
        
        # Nút thêm vào đơn và in hóa đơn
        btn_frame = ttk.Frame(order_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        add_btn = ttk.Button(
            btn_frame, 
            text="Thêm vào đơn", 
            command=self.add_to_order,
            style="TButton"
        )
        add_btn.pack(fill=tk.X, pady=5)
        
        print_btn = ttk.Button(
            btn_frame, 
            text="In hóa đơn", 
            command=self.print_invoice,
            style="TButton"
        )
        print_btn.pack(fill=tk.X)
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            footer_frame, 
            text="© 2023 Quản Lý Quán Ăn - Phần mềm được phát triển bởi Hệ thống quản lý nhà hàng", 
            style="TLabel"
        ).pack(side=tk.LEFT)
    
    def display_menu_item(self, menu):
        index = self.menus.index(menu)
        ma_mon, ten_mon, gia, hinh_anh_url, mo_ta = menu
        
        # Tạo frame cho mỗi món ăn
        item_frame = ttk.Frame(self.menu_items_frame, style="MenuCard.TFrame")
        item_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Hiển thị hình ảnh
        img_frame = ttk.Frame(item_frame)
        img_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        try:
            if hinh_anh_url:
                response = requests.get(hinh_anh_url)
                response.raise_for_status()
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
            else:
                raise ValueError("No image URL")
        except:
            # Nếu không có hình ảnh hoặc lỗi, dùng hình ảnh mặc định
            img = Image.new("RGB", (120, 120), "#e0e0e0")
        
        img = img.resize((120, 120))
        img = ImageTk.PhotoImage(img)
        
        img_label = tk.Label(img_frame, image=img, bg="white")
        img_label.image = img
        img_label.pack()
        
        # Thông tin món ăn
        info_frame = ttk.Frame(item_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        name_label = ttk.Label(
            info_frame, 
            text=ten_mon, 
            font=("Arial", 12, "bold"),
            style="TLabel"
        )
        name_label.pack(anchor=tk.W)
        
        desc_label = ttk.Label(
            info_frame, 
            text=mo_ta or "Món ngon, hấp dẫn", 
            font=self.font_small,
            style="TLabel",
            wraplength=300
        )
        desc_label.pack(anchor=tk.W)
        
        price_label = ttk.Label(
            info_frame, 
            text=f"Giá: {gia:,.0f} VND", 
            font=("Arial", 11, "bold"),
            foreground="#e53935",
            style="TLabel"
        )
        price_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Nút điều chỉnh số lượng
        qty_frame = ttk.Frame(info_frame)
        qty_frame.pack(anchor=tk.W, pady=5)
        
        minus_btn = ttk.Button(
            qty_frame, 
            text="-", 
            width=3,
            command=lambda i=index: self.change_quantity(i, -1)
        )
        minus_btn.pack(side=tk.LEFT)
        
        qty_label = ttk.Label(
            qty_frame, 
            text="0", 
            width=3,
            anchor=tk.CENTER,
            font=self.font_normal,
            style="TLabel"
        )
        qty_label.pack(side=tk.LEFT, padx=5)
        
        plus_btn = ttk.Button(
            qty_frame, 
            text="+", 
            width=3,
            command=lambda i=index: self.change_quantity(i, 1)
        )
        plus_btn.pack(side=tk.LEFT)
        
        # Lưu label để cập nhật số lượng
        if not hasattr(self, 'qty_labels'):
            self.qty_labels = {}
        self.qty_labels[index] = qty_label
    
    def change_quantity(self, index, delta):
        self.menu_quantities[index] = max(0, self.menu_quantities[index] + delta)
        self.qty_labels[index].config(text=str(self.menu_quantities[index]))
    
    def add_to_order(self):
        added = False
        for i, qty in enumerate(self.menu_quantities):
            if qty > 0:
                menu = self.menus[i]
                total_price = menu[2] * qty
                
                # Kiểm tra xem món đã có trong đơn hàng chưa
                existing_index = None
                for idx, item in enumerate(self.order_items):
                    if item["ma_mon"] == menu[0]:
                        existing_index = idx
                        break
                
                if existing_index is not None:
                    # Cập nhật số lượng nếu món đã có trong đơn
                    self.order_items[existing_index]["so_luong"] += qty
                    self.order_listbox.delete(existing_index)
                    item = self.order_items[existing_index]
                    new_text = f"{item['ten_mon']} - {item['so_luong']} x {item['don_gia']:,.0f} = {item['so_luong'] * item['don_gia']:,.0f} VND"
                    self.order_listbox.insert(existing_index, new_text)
                else:
                    # Thêm món mới vào đơn hàng
                    self.order_listbox.insert(tk.END, f"{menu[1]} - {qty} x {menu[2]:,.0f} = {total_price:,.0f} VND")
                    self.order_items.append({
                        "ma_mon": menu[0],
                        "ten_mon": menu[1],
                        "so_luong": qty,
                        "don_gia": menu[2]
                    })
                
                self.total_price += total_price
                self.total_label.config(text=f"{self.total_price:,.0f} VND")
                self.menu_quantities[i] = 0
                self.qty_labels[i].config(text="0")
                added = True
        
        if not added:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ít nhất một món và số lượng hợp lệ!")
    
    def remove_selected_item(self):
        selected = self.order_listbox.curselection()
        if not selected:
            messagebox.showwarning("Thông báo", "Vui lòng chọn món cần xóa!")
            return
        
        index = selected[0]
        item = self.order_items[index]
        self.total_price -= item["so_luong"] * item["don_gia"]
        self.total_label.config(text=f"{self.total_price:,.0f} VND")
        
        self.order_listbox.delete(index)
        self.order_items.pop(index)
    
    def print_invoice(self):
        if not self.order_items:
            messagebox.showwarning("Thông báo", "Đơn hàng chưa có món ăn!")
            return

        # Lấy ngày giờ hiện tại
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        stt = self.get_stt_for_today(date)

        # Gán lại để dùng khi gọi show_invoice_preview
        self.invoice_filename = f"invoice_{stt:04d}.pdf"
        self.invoice_number = stt
        self.date = date

        # Tạo buffer PDF
        pdf_buffer = BytesIO()

        # Tạo document
        doc = SimpleDocTemplate(pdf_buffer,
                                pagesize=A4,
                                rightMargin=20 * mm,
                                leftMargin=20 * mm,
                                topMargin=20 * mm,
                                bottomMargin=20 * mm)

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName='Arial-Bold',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading2'],
            fontName='Arial',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=10
        )

        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontName='Arial-Bold',
            fontSize=12,
            alignment=TA_RIGHT,
            spaceBefore=10
        )

        story = []

        # Tiêu đề hóa đơn
        story.append(Paragraph("NHÀ HÀNG ABC", title_style))
        story.append(Paragraph(f"HÓA ĐƠN #{stt:04d}", header_style))

        # Thông tin ngày giờ
        info_data = [
            [Paragraph(f"<b>Ngày:</b> {date}", normal_style),
            Paragraph(f"<b>Giờ:</b> {time}", normal_style)],
        ]
        info_table = Table(info_data, colWidths=[100 * mm, 100 * mm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))

        # Bảng món ăn
        story.append(Paragraph("DANH SÁCH MÓN ĂN", header_style))
        item_data = [["STT", "Tên món", "Số lượng", "Đơn giá", "Thành tiền"]]
        for idx, item in enumerate(self.order_items, start=1):
            item_data.append([
                str(idx),
                item['ten_mon'],
                str(item['so_luong']),
                f"{item['don_gia']:,.0f} VND",
                f"{item['so_luong'] * item['don_gia']:,.0f} VND"
            ])
        item_table = Table(item_data, colWidths=[15 * mm, 70 * mm, 25 * mm, 40 * mm, 40 * mm])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
        ]))
        story.append(item_table)

        # Tổng tiền
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"TỔNG CỘNG: {self.total_price:,.0f} VND", total_style))
        story.append(Spacer(1, 30))

        # Chân trang
        footer = Paragraph(
            "Cảm ơn quý khách!<br/>Hẹn gặp lại quý khách lần sau",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontName='Arial',
                alignment=TA_CENTER,
                fontSize=10,
                textColor=colors.grey,
                spaceBefore=20
            )
        )
        story.append(footer)

        # Xuất PDF
        doc.build(story)
        # ✅ Ghi PDF ra file thật
        with open(self.invoice_filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        # Mở cửa sổ xem trước
        self.show_invoice_preview(filename=self.invoice_filename, stt=stt, date=date)

    def show_invoice_preview(self, filename, stt, date):
        """Hiển thị cửa sổ xem trước hóa đơn và các nút chức năng"""
        invoice_window = tk.Toplevel(self.root)
        invoice_window.title(f"Hóa đơn #{stt}")
        invoice_window.geometry("800x600")
        
        # Frame chứa PDF viewer (cần cài đặt thư viện như pdf2image hoặc tkinterPDF)
        pdf_frame = ttk.Frame(invoice_window)
        pdf_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ở đây bạn cần thêm code để hiển thị PDF
        # Có thể sử dụng thư viện như pdf2image để hiển thị hình ảnh PDF
        # Hoặc sử dụng tkinterPDF nếu muốn hiển thị trực tiếp
        
        # Tạm thời hiển thị thông báo
        label = ttk.Label(pdf_frame, text=f"Đã tạo hóa đơn: {filename}", font=('Arial', 12))
        label.pack(expand=True)
        
        # Frame chứa các nút
        btn_frame = ttk.Frame(invoice_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="In hóa đơn", 
                command=lambda: self.print_pdf(filename)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Mở file", 
                command=lambda: self.open_pdf(filename)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Lưu và đóng", 
                command=lambda: self.save_and_close(invoice_window, stt, date)).pack(side=tk.RIGHT)

    def print_pdf(self, filename):
        """In file PDF"""
        try:
            import os
            if os.name == 'nt':  # Windows
                os.startfile(filename, "print")
            else:  # MacOS và Linux
                os.system(f'lpr "{filename}"')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể in file: {str(e)}")

    def open_pdf(self, filename):
        """Mở file PDF bằng ứng dụng mặc định"""
        try:
            import os
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            elif os.name == 'posix':  # MacOS và Linux
                subprocess.run(['open', filename] if sys.platform == 'darwin' else ['xdg-open', filename])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file: {str(e)}")

    def save_and_close(self, window, stt, date):
        # Lưu hóa đơn vào CSDL
        self.save_invoice(stt, date)
        window.destroy()
        
        # Xóa đơn hàng sau khi lưu
        self.order_items.clear()
        self.order_listbox.delete(0, tk.END)
        self.total_price = 0
        self.total_label.config(text="0 VND")
    
    def get_stt_for_today(self, date):
        self.cursor.execute("SELECT MAX(stt_trong_ngay) FROM hoa_don WHERE DATE(ngay_gio) = %s", (date,))
        result = self.cursor.fetchone()
        return result[0] + 1 if result[0] else 1
    
    def save_invoice(self, stt, date):
        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        ma_hoa_don = f"HĐ-{stt}-{date.replace('-', '')}"

        self.cursor.execute(
            "INSERT INTO hoa_don (ma_hoa_don, stt_trong_ngay, ngay_gio, tong_tien) VALUES (%s, %s, %s, %s)",
            (ma_hoa_don, stt, time, self.total_price)
        )

        # Lưu chi tiết hóa đơn
        for item in self.order_items:
            self.cursor.execute(
                "INSERT INTO chi_tiet_hoa_don (ma_hoa_don, ma_mon, so_luong, don_gia) VALUES (%s, %s, %s, %s)",
                (ma_hoa_don, item["ma_mon"], item["so_luong"], item["don_gia"])
            )

        self.conn.commit()

        # Cập nhật doanh thu ngày
        self.update_daily_revenue(date)
    
    def update_daily_revenue(self, date):
        self.cursor.execute("SELECT * FROM doanh_thu_ngay WHERE ngay = %s", (date,))
        result = self.cursor.fetchone()

        if result:
            self.cursor.execute("UPDATE doanh_thu_ngay SET tong_don = tong_don + 1, tong_tien = tong_tien + %s WHERE ngay = %s",
                              (self.total_price, date))
        else:
            self.cursor.execute("INSERT INTO doanh_thu_ngay (ngay, tong_don, tong_tien) VALUES (%s, 1, %s)",
                              (date, self.total_price))

        self.conn.commit()
    
    def show_help(self):
        help_text = """
HƯỚNG DẪN SỬ DỤNG

1. Chọn món ăn từ thực đơn bằng cách nhấn nút '+' để tăng số lượng
2. Nhấn 'Thêm vào đơn' để thêm món đã chọn vào đơn hàng
3. Trong đơn hàng, bạn có thể:
   - Xóa món đã chọn bằng nút 'Xóa món đã chọn'
   - Nhấn 'In hóa đơn' để tạo hóa đơn
4. Trong cửa sổ hóa đơn, bạn có thể:
   - In hóa đơn ra máy in
   - Lưu hóa đơn vào hệ thống

Mọi thắc mắc vui lòng liên hệ: 0123.456.789
"""
        messagebox.showinfo("Trợ giúp", help_text)

# Khởi chạy ứng dụng
if __name__ == "__main__":
    root = tk.Tk()
    app = ModernQuanAnApp(root)
    root.mainloop()
