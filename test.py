import mysql.connector
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import os
import requests
from io import BytesIO


# Kết nối tới MySQL
def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="hieu05012004x@X",
        database="quanlyquanan"
    )

# Tạo giao diện Tkinter
class QuanAnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Quán Ăn")
        self.root.geometry("800x600")

        # Kết nối DB và lấy danh sách món ăn
        self.conn = connect_db()
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT ma_mon, ten_mon, gia, hinh_anh_url FROM mon_an WHERE con_ban = TRUE")
        self.menus = self.cursor.fetchall()

        self.order_items = []  # Lưu chi tiết đơn hàng
        self.menu_quantities = [0] * len(self.menus)  # Số lượng cho từng món

        self.create_widgets()

    def create_widgets(self):
        # Khung chọn món
        self.menu_label = tk.Label(self.root, text="Chọn món ăn", font=("Arial", 16))
        self.menu_label.pack(pady=10)

        # Tạo frame để chứa các món ăn với hình ảnh
        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.pack()

        for menu in self.menus:
            self.display_menu_item(menu)

        # Thêm món vào đơn hàng
        self.add_button = tk.Button(self.root, text="Thêm vào đơn", font=("Arial", 12), command=self.add_to_order)
        self.add_button.pack(pady=10)

        # Hiển thị đơn hàng
        self.order_label = tk.Label(self.root, text="Đơn hàng:", font=("Arial", 14))
        self.order_label.pack(pady=5)

        self.order_listbox = tk.Listbox(self.root, font=("Arial", 12), height=10)
        self.order_listbox.pack(pady=5)

        # Tổng tiền
        self.total_label = tk.Label(self.root, text="Tổng tiền: 0 VND", font=("Arial", 14))
        self.total_label.pack(pady=10)

        # In hóa đơn
        self.print_button = tk.Button(self.root, text="In hóa đơn", font=("Arial", 12), command=self.print_invoice)
        self.print_button.pack(pady=10)

    def display_menu_item(self, menu):
        index = self.menus.index(menu)
        ma_mon, ten_mon, gia, hinh_anh_url = menu

        # Nếu có hình ảnh, hiển thị nó
        image_path = hinh_anh_url
        if image_path:  # Kiểm tra nếu URL hình ảnh không trống
            try:
                # Tải hình ảnh từ URL
                response = requests.get(image_path)
                response.raise_for_status()  # Kiểm tra xem yêu cầu có thành công không (mã trạng thái 200)
                
                # Mở hình ảnh từ dữ liệu tải về
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                img = img.resize((100, 100))  # Điều chỉnh kích thước hình ảnh
                img = ImageTk.PhotoImage(img)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                # Nếu có lỗi, dùng hình ảnh mặc định
                default_image = Image.new("RGB", (100, 100), (200, 200, 200))  # Tạo một hình ảnh nền màu xám
                img = ImageTk.PhotoImage(default_image)  # Chuyển đổi nó thành ImageTk.PhotoImage
        else:
            # Nếu không có URL hình ảnh, sử dụng hình ảnh mặc định
            default_image = Image.new("RGB", (100, 100), (200, 200, 200))  # Tạo một hình ảnh nền màu xám
            img = ImageTk.PhotoImage(default_image)  # Chuyển đổi nó thành ImageTk.PhotoImage

        # Tạo Label hiển thị hình ảnh và tên món ăn
        frame = tk.Frame(self.menu_frame)
        frame.pack(side=tk.LEFT, padx=20, pady=10)

        img_label = tk.Label(frame, image=img)
        img_label.image = img  # Lưu ảnh để không bị garbage collected
        img_label.pack()

        name_label = tk.Label(frame, text=f"{ten_mon} - {gia:,.0f} VND", font=("Arial", 12))
        name_label.pack()

        # Thêm nút tăng/giảm số lượng cho từng món
        qty_frame = tk.Frame(frame)
        qty_frame.pack()
        minus_btn = tk.Button(qty_frame, text="-", command=lambda i=index: self.change_quantity(i, -1))
        minus_btn.pack(side=tk.LEFT)
        qty_label = tk.Label(qty_frame, text="0", width=3)
        qty_label.pack(side=tk.LEFT)
        plus_btn = tk.Button(qty_frame, text="+", command=lambda i=index: self.change_quantity(i, 1))
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
                self.order_listbox.insert(tk.END, f"{menu[1]} - {qty} x {menu[2]:,.0f} = {total_price:,.0f} VND")
                self.update_total_price(total_price)
                self.order_items.append({
                    "ma_mon": menu[0],
                    "ten_mon": menu[1],
                    "so_luong": qty,
                    "don_gia": menu[2]
                })
                self.menu_quantities[i] = 0
                self.qty_labels[i].config(text="0")
                added = True
        if not added:
            messagebox.showwarning("Lỗi", "Vui lòng chọn ít nhất một món và số lượng hợp lệ!")

    def update_total_price(self, price):
        current_total = self.total_label.cget("text").split(": ")[1]
        current_total = int(current_total.replace(" VND", "").replace(",", ""))
        new_total = current_total + price
        self.total_label.config(text=f"Tổng tiền: {new_total:,.0f} VND")

    def print_invoice(self):
        order_items = self.order_listbox.get(0, tk.END)
        if not order_items:
            messagebox.showwarning("Lỗi", "Đơn hàng chưa có món ăn!")
            return

        # Tạo mã hóa đơn và STT
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        stt = self.get_stt_for_today(date)

        total_price = self.total_label.cget("text").split(": ")[1]
        total_price = total_price.replace(" VND", "").replace(",", "")

        invoice = f"Hóa đơn #{stt}\nNgày: {date} - Giờ: {time}\n"
        invoice += "\n".join(order_items)
        invoice += f"\nTổng tiền: {total_price} VND"

        messagebox.showinfo("Hóa đơn", invoice)

        # Lưu hóa đơn vào CSDL
        self.save_invoice(stt, date, total_price)

    def get_stt_for_today(self, date):
        self.cursor.execute("SELECT MAX(stt_trong_ngay) FROM hoa_don WHERE DATE(ngay_gio) = %s", (date,))
        result = self.cursor.fetchone()
        return result[0] + 1 if result[0] else 1

    def save_invoice(self, stt, date, total_price):
        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        ma_hoa_don = f"HĐ-{stt}-{date.replace('-', '')}"

        self.cursor.execute(
            "INSERT INTO hoa_don (ma_hoa_don, stt_trong_ngay, ngay_gio, tong_tien) VALUES (%s, %s, %s, %s)",
            (ma_hoa_don, stt, time, total_price)
        )

        # Lưu chi tiết hóa đơn
        for item in self.order_items:
            self.cursor.execute(
                "INSERT INTO chi_tiet_hoa_don (ma_hoa_don, ma_mon, so_luong, don_gia) VALUES (%s, %s, %s, %s)",
                (ma_hoa_don, item["ma_mon"], item["so_luong"], item["don_gia"])
            )

        self.conn.commit()

        # Cập nhật doanh thu ngày
        self.update_daily_revenue(date, total_price)

        # Xóa đơn hàng sau khi lưu
        self.order_items.clear()
        self.order_listbox.delete(0, tk.END)
        self.total_label.config(text="Tổng tiền: 0 VND")

    def update_daily_revenue(self, date, total_price):
        self.cursor.execute("SELECT * FROM doanh_thu_ngay WHERE ngay = %s", (date,))
        result = self.cursor.fetchone()

        if result:
            self.cursor.execute("UPDATE doanh_thu_ngay SET tong_don = tong_don + 1, tong_tien = tong_tien + %s WHERE ngay = %s",
                                (total_price, date))
        else:
            self.cursor.execute("INSERT INTO doanh_thu_ngay (ngay, tong_don, tong_tien) VALUES (%s, 1, %s)",
                                (date, total_price))

        self.conn.commit()

# Khởi chạy ứng dụng
if __name__ == "__main__":
    root = tk.Tk()
    app = QuanAnApp(root)
    root.mainloop()