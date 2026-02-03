from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta
import calendar
class ReportController:
    def __init__(self, window, client_repo, room_repo):
        self.window = window
        self.client_repo = client_repo
        self.room_repo = room_repo
        self.model = QStandardItemModel()
        self.window.tableView_Report.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self._connect_signals()

    def _connect_signals(self):
        self.window.pushButtonCreateReport.clicked.connect(self.generate_hotel_performance_report)

    def generate_hotel_performance_report(self):

        selected_date = self.window.comboBox_MonthYear.currentData()
        if not selected_date.isValid():
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Выберите месяц!")
            return

        year = selected_date.year()
        month = selected_date.month()
        days_in_month = calendar.monthrange(year, month)[1]
        month_name = selected_date.toString("MMMM yyyy")

        rooms = self.room_repo.get_all()
        if not rooms:
            QtWidgets.QMessageBox.warning(self.window, "Нет данных", "В базе нет номеров!")
            return

        # Статистика по номерам
        room_stats = {
            r.id: {
                "number": r.number,
                "type": r.room_type,
                "price": r.price,
                "occupied_days": 0,
                "unique_bookings": set(),
                "nights": 0
            } for r in rooms
        }

        # Все брони
        bookings = self.client_repo.get_all_with_room_info()  # (id, fio, room_num, type, start, end)

        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, days_in_month).date()

        # Карта: (room_id, date) занято ли в этот день
        occupancy_map = {}  # (room_id, date) → True

        for client_id, fio, room_number, _, date_start_str, date_end_str in bookings:
            try:
                start = datetime.strptime(date_start_str, "%d.%m.%Y").date()
                end = datetime.strptime(date_end_str, "%d.%m.%Y").date()

                room_id = next((r.id for r in rooms if str(r.number) == str(room_number)), None)
                if not room_id:
                    continue

                # Проверяем пересечение с месяцем
                if end < first_day or start > last_day:
                    continue

                stay_start = max(start, first_day)
                stay_end = min(end, last_day)  # включая день выезда

                current = stay_start
                while current <= stay_end and current.month == month:
                    key = (room_id, current)
                    occupancy_map[key] = True  # ← номер занят в этот день
                    current += timedelta(days=1)
                # Добавляем уникальную бронь по client_id (гарантированно уникально!)
                room_stats[room_id]["unique_bookings"].add(client_id)

            except ValueError:
                continue

        # === СЧИТАЕМ ДНИ И ГОСТЕЙ ===
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            "Номер", "Тип", "Цена за день", "Занят, дней", "Свободен, дней", "Загрузка", "Число клиентов", "Доход"
        ])
        self.window.tableView_Report.setModel(model)

        total_income = total_occupied_days = total_guests = 0

        for room_id, s in room_stats.items():
            # Считаем, сколько уникальных дней был занят номер
            occupied_days = sum(1 for (rid, date) in occupancy_map.keys() if rid == room_id)
            free_days = days_in_month - occupied_days
            load = round(occupied_days / days_in_month * 100, 1) if days_in_month else 0

            guests = len(s["unique_bookings"])
            nights = occupied_days
            income = nights * s["price"]
            total_income += income
            total_occupied_days += occupied_days
            total_guests += guests

            row = [
                QStandardItem(str(s["number"])),
                QStandardItem(s["type"]),
                QStandardItem(f"{s['price']:,} ₽".replace(",", " ")),
                QStandardItem(str(occupied_days)),
                QStandardItem(str(free_days)),
                QStandardItem(f"{load}%"),
                QStandardItem(str(guests)),
                QStandardItem(f"{income:,} ₽".replace(",", " "))
            ]

            # Цвет загрузки
            color = "#d4edda" if load >= 90 else "#fff3cd" if load >= 70 else "#f8d7da"
            row[5].setBackground(QBrush(QColor(color)))
            row[7].setFont(QFont("Segoe UI", 10, QFont.Bold))
            for item in row:
                item.setTextAlignment(Qt.AlignCenter)

            model.appendRow(row)

        # === ИТОГО ===
        avg_load = round(total_occupied_days / (len(rooms) * days_in_month) * 100, 1) if rooms else 0

        summary_text = (
            f"ИТОГО за {month_name}: "
            f"Номеров: {len(rooms)} │ "
            f"Доход {total_income:,} ₽ │ "
            f"Число клиентов: {total_guests} │ "
            f"Средняя загрузка: {avg_load}%"
        ).replace(",", " ")

        summary = QStandardItem(summary_text)
        summary.setBackground(QBrush(QColor("#0078d7")))
        summary.setForeground(QBrush(QColor("white")))
        summary.setFont(QFont("Segoe UI", 12, QFont.Bold))
        summary.setTextAlignment(Qt.AlignCenter)

        model.appendRow([summary] + [QStandardItem("") for _ in range(7)])
        self.window.tableView_Report.setSpan(model.rowCount() - 1, 0, 1, 8)

        self.window.statusbar.showMessage(f"Отчёт по номерам за {month_name} готов!", 8000)
