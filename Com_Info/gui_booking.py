import tkinter as tk
from tkinter import ttk, messagebox
from booking import E12  # นำเข้าคลาสที่สร้างไว้แล้ว
from datetime import datetime

class BookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Room Booking System")
        self.root.geometry("400x500")
        
        self.booking = E12()  # ใช้งานคลาส E12

        # สร้าง Label
        ttk.Label(root, text="Room ID:").grid(row=0, column=0, padx=10, pady=10)
        self.room_var = tk.StringVar()
        self.room_dropdown = ttk.Combobox(root, textvariable=self.room_var)
        self.room_dropdown['values'] = [f"E12-{i}0{j}" for i in range(1, 13) for j in range(1,8)]
        self.room_dropdown.grid(row=0, column=1, padx=10, pady=10)
        self.room_dropdown.current(0)

        ttk.Label(root, text="Guest Name:").grid(row=1, column=0, padx=10, pady=10)
        self.guest_entry = ttk.Entry(root)
        self.guest_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(root, text="Field:").grid(row=2, column=0, padx=10, pady=10)
        self.field_var = tk.StringVar()
        self.field_dropdown = ttk.Combobox(root, textvariable=self.field_var)
        self.field_dropdown['values'] = [
            'Electrical Engineering',
            'Electrical Communication and Network Engineering',
            'Electronic Engineering',
            'Mechanical Engineering',
            'Civil Engineering',
            'Industrial Engineering',
            'Mechatronics and Automation Engineering',
            'Computer Engineering',
            'Railway Transportation Engineering',
            'IoT and Information Systems Engineering',
            'Chemical Engineering',
            'Food Engineering',
            'Smart Agricultural Engineering',
            'Integrated Production Engineering'
        ]
        self.field_dropdown.grid(row=2, column=1, padx=10, pady=10)
        self.field_dropdown.current(0)

        ttk.Label(root, text="Activity:").grid(row=3, column=0, padx=10, pady=10)
        self.Activity_var = tk.StringVar()
        self.Activity_dropdown = ttk.Combobox(root, textvariable=self.Activity_var)
        self.Activity_dropdown['values'] = ['Education','Recreation','Catering','Conference','ETC.']
        self.Activity_dropdown.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(root, text="Role:").grid(row=4, column=0, padx=10, pady=10)
        self.Role_var = tk.StringVar()
        self.Role_dropdown = ttk.Combobox(root, textvariable=self.Role_var)
        self.Role_dropdown['values'] = ['Student','Professor','ETC.']
        self.Role_dropdown.grid(row=4, column=1, padx=10, pady=10)
        
        ttk.Label(root, text="Booking Date (DD-MM-YYYY):").grid(row=5, column=0, padx=10, pady=10)
        today_date = datetime.today().strftime("%d-%m-%Y")
        self.date_var = tk.StringVar(value=today_date)
        self.date_entry = ttk.Entry(root, textvariable=self.date_var, state="readonly")
        self.date_entry.grid(row=5, column=1, padx=10, pady=10)

        ttk.Label(root, text="Start Time (HH.MM):").grid(row=6, column=0, padx=10, pady=10)
        self.start_var = tk.StringVar()
        self.start_entry = ttk.Combobox(root, textvariable=self.start_var)
        self.start_entry['values'] = ['09.00','10.00','11.00','12.00','13.00','14.00','15.00','16.00']
        self.start_entry.grid(row=6, column=1, padx=10, pady=10)
        
        ttk.Label(root, text="End Time (HH.MM):").grid(row=7, column=0, padx=10, pady=10)
        self.end_var = tk.StringVar()
        self.end_entry = ttk.Combobox(root, textvariable=self.end_var)
        self.end_entry['values'] = ['09.00','10.00','11.00','12.00','13.00','14.00','15.00','16.00']
        self.end_entry.grid(row=7, column=1, padx=10, pady=10)
        # ปุ่มจองห้อง
        self.book_button = ttk.Button(root, text="Book Room", command=self.book_room)
        self.book_button.grid(row=8, column=0, columnspan=2, pady=10)
        
        self.clear_button = ttk.Button(root, text="Clear Room", command=self.clear_room)
        self.clear_button.grid(row=9, column=0, columnspan=2, pady=10)

        # ปุ่มดูสถานะห้องทั้งหมด
        self.status_button = ttk.Button(root, text="Show Room Status", command=self.show_status)
        self.status_button.grid(row=10, column=0, columnspan=2, pady=10)
    
    def clear_room(self):
        room = self.room_var.get()
        guest = self.guest_entry.get()
        field = self.field_var.get()
        activity = self.Activity_var.get()
        role = self.Role_var.get()
        date = self.date_entry.get()
        start = self.start_entry.get()
        end = self.end_entry.get()

        # ตรวจสอบให้แน่ใจว่ามีการกรอกข้อมูลก่อนที่จะทำการเคลียร์
        if not all([room, guest, field, activity, role, date, start, end]):
            messagebox.showerror("Error", "Please fill in all fields before clearing")
            return

        try:
            # อัปเดตข้อมูลในฐานข้อมูลให้กลับไปเป็นค่าเริ่มต้น
            self.booking.cursor.execute("""
            UPDATE RoomStatus
            SET guest_name = NULL, field = NULL, duration = NULL, booking_str = NULL, start_str = NULL,
            end_str = NULL, Activity = NULL, Role = NULL
            WHERE roomID = ? AND guest_name = ? AND field = ? AND booking_str = ? AND start_str = ?
            AND end_str = ? AND Activity = ? AND Role = ?
            """, (room, guest, field, date, start, end, activity, role))

            self.booking.cursor.execute("""
            DELETE FROM Booking_History
            WHERE roomID = ? AND guest_name = ? AND field = ? AND booking_str = ? AND start_str = ?
            AND end_str = ? AND Activity = ? AND Role = ?
            """, (room, guest, field, date, start, end, activity, role))
            self.booking.conn.commit()  


            # รีเฟรชค่าในฟอร์มให้เป็นค่าเริ่มต้น
            self.room_dropdown.set('')
            self.guest_entry.delete(0, tk.END)
            self.field_dropdown.set('')
            self.Activity_dropdown.set('')
            self.Role_dropdown.set('')
            self.date_entry.delete(0, tk.END)
            self.start_entry.delete(0, tk.END)
            self.end_entry.delete(0, tk.END)

            messagebox.showinfo("Success", f"Room {room} by {guest} has been cleared.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

       
    def book_room(self):
        room = self.room_var.get()
        guest = self.guest_entry.get()
        field = self.field_var.get()
        activity = self.Activity_var.get()
        role = self.Role_var.get()
        date = self.date_entry.get()
        start = self.start_entry.get()
        end = self.end_entry.get()
        
        if not all([room, guest, field, activity, role, date, start, end]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # ตรวจสอบการจองซ้อน
            self.booking.cursor.execute(
                """
                SELECT * FROM RoomStatus 
                WHERE RoomID = ? 
                AND booking_str = ?
                AND (
                    (start_str < ? AND end_str > ?) OR
                    (start_str >= ? AND start_str < ?) OR
                    (end_str > ? AND end_str <= ?)
                )
                """,
                (room, date, end, start, start, end, start, end)
            )
            existing_booking = self.booking.cursor.fetchone()
            
            if existing_booking:
                messagebox.showerror("Error", f"Room {room} is already booked during this time")
                return
            
            if self.booking.rent(room, guest, field, activity, role, date, start, end):
                messagebox.showinfo("Success", f"Room {room} booked successfully")
            else:
                messagebox.showerror("Error", "Failed to book the room")
                
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        
    def show_status(self):
        status_window = tk.Toplevel(self.root)
        status_window.title("Room Status")
        
        status_text = tk.Text(status_window, width=50, height=20)
        status_text.pack(padx=10, pady=10)
        
        for room in self.booking.rooms:
            self.booking.cursor.execute("SELECT * FROM RoomStatus WHERE RoomID = ?", (room,))
            row = self.booking.cursor.fetchone()
            if row:
                status_text.insert(tk.END, f"{room}: {'Occupied' if row.duration else 'Available'}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = BookingApp(root)
    root.mainloop()