import threading
import pyodbc
from datetime import datetime,timedelta

class E12:
    def __init__(self):
        # สร้างรายชื่อห้องในรูปแบบ 'E12-101', 'E12-102', ...
        self.rooms = [f'E12-{i+1}0{j+1}' for i in range(12) for j in range(7)]
        self.status = {room: {'status': False, 'guest': None} for room in self.rooms}

        # เชื่อมต่อฐานข้อมูล SQL Server
        self.conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=kmitl.database.windows.net;'
            'DATABASE=Project rent E12;'
            'UID=E12-admin;'
            'PWD=Kmitl123456789'
        )
        self.cursor = self.conn.cursor()

        # อัปเดตข้อมูลห้องในฐานข้อมูล (ไม่สร้างตาราง)
        self._initialize_database()
        self._size_of_rooms()

    def _initialize_database(self):
        """เพิ่มห้องที่ยังไม่มีในฐานข้อมูล"""
        for room in self.rooms:
            self.cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM RoomStatus WHERE RoomID = ?)
                INSERT INTO RoomStatus (RoomID, guest_name, field, booking_str, start_str, end_str,duration,Activity,Role)
                VALUES (?, NULL, NULL, NULL, NULL, NULL,NULL,NULL,NULL)
                """,
                room, room
            )
        self.conn.commit()
    
    def _size_of_rooms(self):
        for room in self.rooms:
            if room[-1] == '4':
                size = 'Big'
            
            elif room[-1] == '5':
                size = 'Small'
            
            else:
                size = 'Middle'
            self.cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM Room_Size WHERE RoomID = ?)
                INSERT INTO Room_Size(RoomID,Size)
                VALUES (?,?)
                """,
                room, room, size
            )
        self.conn.commit()

    def show_data(self, room=None,status=None):
        """แสดงข้อมูลห้องทั้งหมดหรือห้องที่กำหนด"""
        if room is None and status is None:
            self.cursor.execute("SELECT * FROM RoomStatus")
            rows = self.cursor.fetchall()
            for row in rows:
                status_text = "Occupied" if row.duration else "Available"
                guest_text = f" by {row.guest_name}" if row.guest_name else ""
                print(f"{row.RoomId}: {status_text}{guest_text}")
        
        elif status is not None:
            if status == True:
                self.cursor.execute("SELECT * FROM RoomStatus WHERE duration is null")
                text = 'is Available'
            else:
                self.cursor.execute("SELECT * FROM RoomStatus WHERE duration is not null")
                text = 'Occupied'
            rows = self.cursor.fetchall()
            for row in rows:
                print(f'{row.RoomId} {text}')
        else:
            self.cursor.execute("SELECT * FROM RoomStatus WHERE RoomID = ?", room)
            row = self.cursor.fetchone()
            if row:
                status_text = "Occupied" if row.duration else "Available"
                guest_text = f" by {row.guest_name}" if row.guest_name else ""
                print(f"{row.RoomId}: {status_text}{guest_text}")
            else:
                print(f"{room} does not exist.")
    
    def show_history(self,guest_name = None):
        if guest_name is None:
            self.cursor.execute("select * from Booking_History")
            rows = self.cursor.fetchall()
            for row in rows:
                print(f'RentId: {row.RentId} | Room: {row.RoomId} | Guest: {row.guest_name} | Field: {row.field} | date: {row.booking_str} | start: {row.start_str} | end: {row.end_str} | duration: {row.duration}')
        else:
            self.cursor.execute("""select * from Booking_History
                                where guest_name = ?""", guest_name)
            rows = self.cursor.fetchall()
            for row in rows:
                print(f'RentId: {row.RentId} | Room: {row.RoomId} | Guest: {row.guest_name} | Field: {row.field} | date: {row.booking_str} | start: {row.start_str} | end: {row.end_str} | duration: {row.duration}')
    def rent(self, room, guest_name, field, Activity, Role, booking_date, start_time, end_time):
        try:
            # แปลงค่าสตริงให้เป็น datetime object
            booking_dt = datetime.strptime(booking_date, '%d-%m-%Y')
            start_dt = datetime.strptime(f"{booking_date} {start_time}", '%d-%m-%Y %H.%M')
            end_dt = datetime.strptime(f"{booking_date} {end_time}", '%d-%m-%Y %H.%M')
        except ValueError as e:
            print(f"Invalid datetime format: {e}")
            return False

        now = datetime.now()
        if start_dt < now:
            print("Start time must be in the future.")
            return False
        if end_dt <= start_dt:
            print("End time must be later than start time.")
            return False

        duration_seconds = int((end_dt - start_dt).total_seconds())
        duration_minutes = duration_seconds // 60

        try:
            # ตรวจสอบสถานะห้องในฐานข้อมูล
            self.cursor.execute("SELECT duration FROM RoomStatus WHERE RoomID = ?", room)
            row = self.cursor.fetchone()
            
            if row and row.duration is not None:
                print(f"{room} is already occupied.")
                return False

            # อัปเดตฐานข้อมูล
            self.cursor.execute(
                """
                UPDATE RoomStatus
                SET guest_name = ?, field = ?, booking_str = ?, start_str = ?, end_str = ?, duration = ?, Activity = ?, Role = ?
                WHERE RoomID = ?
                """,
                guest_name, field, booking_date, start_time, end_time, duration_minutes, Activity, Role, room
            )
            self.conn.commit()

            # อัปเดตสถานะในโปรแกรม
            self.status[room]['status'] = True
            self.status[room]['guest'] = guest_name

            # บันทึกประวัติ
            self._update_history(room, guest_name, field, booking_date, start_time, end_time, duration_minutes, Activity, Role)
            
            print(f"Setting release timer for {room} ({duration_seconds} seconds)")
            time_to_release = (end_dt - datetime.now()).total_seconds()
            if time_to_release > 0:
                threading.Timer(time_to_release, self._release_room, args=(room,)).start()
            
            return True

        except Exception as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def _release_room(self, room):
        """ปล่อยห้องเมื่อเวลาหมด"""
        print(f"Releasing {room}...")

        # อัปเดตสถานะในโปรแกรม
        self.status[room]['status'] = False
        self.status[room]['guest'] = None

        # อัปเดตฐานข้อมูล (คืนค่าการจอง)
        self.cursor.execute(
            """
            UPDATE RoomStatus
            SET guest_name = NULL, field = NULL, booking_str = NULL, start_str = NULL, end_str = NULL, duration = NULL, Activity = NULL, Role = NULL
            WHERE RoomID = ?
            """,
            room
        )
        self.conn.commit()

        print(f"{room} is now available.")
    
    def clear_booking(self):
        self.cursor.execute(
            """
            UPDATE RoomStatus
            SET guest_name = NULL, field = NULL, booking_str = NULL, start_str = NULL, end_str = NULL, duration = NULL, Activity = NULL, Role = NULL       
        """)
        self.cursor.commit()
    
    def delete_booking(self,guest_name,room,booking_str,start_time):
        
        self.cursor.execute(
            """
            DELETE FROM Booking_History
            where guest_name = ? and RoomId = ? and booking_str = ? and start_str = ?
            """,guest_name,room,booking_str,start_time
            )
        self.conn.commit()

        if room in self.status:
            self.cursor.execute(
                """
                UPDATE RoomStatus
                SET guest_name = NULL, field = NULL, booking_str = NULL, start_str = NULL, end_str = NULL, duration = NULL
                where RoomID = ?
                """,room
                )
            self.conn.commit()
        print("Your booking was deleted!!")
    
    def _update_history(self,room,guest_name,field,booking_str ,start_str, end_str,duration,Activity,Role):
        self.cursor.execute(
            """
            INSERT INTO Booking_History(RoomID, guest_name, field,booking_str, start_str, end_str,duration, Activity, Role)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            room,guest_name,field,booking_str ,start_str, end_str,duration,Activity,Role
        )
        self.conn.commit()

    def close_connection(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        self.conn.close()