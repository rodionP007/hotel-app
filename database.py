import sqlite3
import bcrypt
from PyQt5 import QtCore
import csv
from datetime import datetime
import calendar

def _connect(db_path: str = "hotel5.db"):
    return sqlite3.connect(db_path)


class ClientRepository:
    def __init__(self, room_repo, db_path: str = "hotel5.db"):
        self.db_path = db_path
        self.room_repo = room_repo
        self._create_table()

    def _create_table(self):
        with _connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fio TEXT NOT NULL,
                    room_id INTEGER NOT NULL,
                    date_start TEXT NOT NULL,
                    date_end TEXT NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE RESTRICT
                )
            """)
            conn.commit()

    def get_room_id_by_client(self, client_id: int) -> int | None:
        """
        Возвращает room_id клиента по его id (источник истины — БД)
        """
        with _connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT room_id FROM clients WHERE id = ?",
                (client_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None
    def import_from_csv(self, csv_path: str):
        """
        Импортирует клиентов из CSV файла
        Формат CSV (обязательно с заголовками):
        ФИО;Номер комнаты;Заезд;Выезд
        Иванов Иван Иванович;101;27.11.2025;30.11.2025
        Петрова Анна Сергеевна;202;01.12.2025;05.12.2025
        """

        added_count = 0
        errors = []

        try:
            with open(csv_path, encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')

                for row_num, row in enumerate(reader, start=2):  # start=2 — пропускаем заголовок
                    try:
                        fio = row["ФИО"].strip()
                        room_number = row["Номер комнаты"].strip()
                        date_start = row["Заезд"].strip()
                        date_end = row["Выезд"].strip()

                        if not all([fio, room_number, date_start, date_end]):
                            errors.append(f"Строка {row_num}: пустые поля")
                            continue

                        # Находим room_id по номеру комнаты
                        room = None
                        for r in self.room_repo.get_all():
                            if str(r.number) == room_number:
                                room = r
                                break
                        if not room:
                            errors.append(f"Строка {row_num}: номер {room_number} не найден")
                            continue

                        # Проверка формата дат
                        try:
                            datetime.strptime(date_start, "%d.%m.%Y")
                            datetime.strptime(date_end, "%d.%m.%Y")
                        except ValueError:
                            errors.append(f"Строка {row_num}: неверный формат даты (нужен ДД.ММ.ГГГГ)")
                            continue

                        # Проверка пересечения дат
                        if not self.is_room_available(room.id, date_start, date_end):
                            errors.append(f"Строка {row_num}: номер {room_number} занят на {date_start}–{date_end}")
                            continue

                        # Проверка вместимости (по 1 человеку на запись)
                        current = self.get_current_occupancy(room.id, date_start, date_end)
                        if current + 1 > room.capacity:
                            errors.append(f"Строка {row_num}: в номере {room_number} нет мест")
                            continue

                        # Добавляем клиента
                        self.add_client(
                            fio=fio,
                            room_id=room.id,
                            date_start=date_start,
                            date_end=date_end
                        )
                        added_count += 1


                    except Exception as e:
                        errors.append(f"Строка {row_num}: ошибка — {str(e)}")


            return {
                "added": added_count,
                "errors": errors
            }


        except Exception as e:
            return {
                "added": added_count,
                "errors": [f"Ошибка чтения файла: {str(e)}"]
            }

    def add_client(self, fio: str, room_id: int, date_start: str, date_end: str) -> int:
        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                INSERT INTO clients (fio, room_id, date_start, date_end)
                VALUES (?, ?, ?, ?)
            """, (fio, room_id, date_start, date_end))
            conn.commit()
            client_id = cur.lastrowid
        self.room_repo.update_room_status(room_id)

        return client_id

    def get_all_with_room_info(self):
        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT c.id, c.fio, r.number, r.room_type, c.date_start, c.date_end, r.id AS room_id
                FROM clients c
                JOIN rooms r ON c.room_id = r.id
                ORDER BY c.date_start DESC
            """)
            return cur.fetchall()

    def update_client(self, client_id: int, fio: str, room_id: int, date_start: str, date_end: str):
        old_room_id = self.get_room_id_by_client(client_id)

        with _connect(self.db_path) as conn:
            conn.execute("""
                UPDATE clients 
                SET fio=?, room_id=?, date_start=?, date_end=?
                WHERE id=?
            """, (fio, room_id, date_start, date_end, client_id))
            conn.commit()
        if old_room_id is not None:
            self.room_repo.update_room_status(old_room_id)

        if old_room_id != room_id:
            self.room_repo.update_room_status(room_id)

    def delete_clients(self, client_ids: list[int]):
        room_ids = set()

        for client_id in client_ids:
            room_id = self.get_room_id_by_client(client_id)
            if room_id:
                room_ids.add(room_id)

            with _connect(self.db_path) as conn:
                conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))

        for room_id in room_ids:
            self.room_repo.update_room_status(room_id)

    def get_bookings_by_month(self, year: int, month: int):
        start = f"01.{month:02d}.{year}"
        end = f"{calendar.monthrange(year, month)[1]:02d}.{month:02d}.{year}"

        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT r.room_type, c.date_start, c.date_end, r.price
                FROM clients c
                JOIN rooms r ON c.room_id = r.id
                WHERE c.date_start <= ? AND c.date_end >= ?
            """, (end, start))
            return [{'room_type': r[0], 'date_start': r[1], 'date_end': r[2], 'price': r[3]} for r in cur.fetchall()]

    def get_bookings_by_room_and_month(self, room_id: int, year: int, month: int):
        """
        Возвращает все брони конкретного номера за конкретный месяц (пересекающие)
        """
        start_date = f"01.{month:02d}.{year}"
        end_date = f"{calendar.monthrange(year, month)[1]:02d}.{month:02d}.{year}"

        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT date_start, date_end FROM clients
                WHERE room_id = ?
                  AND date_start <= ?
                  AND date_end >= ?
            """, (room_id, end_date, start_date))
            return cur.fetchall()
    def normalize(self, date_str: str) -> str:
        return f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"

    def get_room_by_id(self, room_id):
        return self.room_repo.get_by_id(room_id)

    def is_room_available(self, room_id: int, date_start: str, date_end: str) -> bool:
        """
        Возвращает True, если номер свободен на указанные даты.
        Исправлено: сравнение дат происходит правильно, а не как строк.
        """
        start = self.normalize(date_start)
        end = self.normalize(date_end)

        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT 1 FROM clients
                WHERE room_id = ?

                -- Проверка пересечения интервалов
                  AND (
                        (substr(date_start, 7, 4) || '-' || substr(date_start, 4, 2) || '-' || substr(date_start, 1, 2)) <= ?
                    AND (substr(date_end,   7, 4) || '-' || substr(date_end,   4, 2) || '-' || substr(date_end,   1, 2)) >= ?
                  )

                LIMIT 1
            """, (room_id, end, start))

            return cur.fetchone() is None

    def get_current_occupancy(self, room_id: int, date_start: str, date_end: str) -> int:
        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT COUNT(*) FROM clients
                WHERE room_id = ?
                  AND date_start <= ?
                  AND date_end >= ?
            """, (room_id, date_end, date_start))
            return cur.fetchone()[0]

class UserRepository:
    def __init__(self):
        self._create_table()
        self._create_default_admin_if_not_exists()

    def _create_table(self):
        with _connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'admin'
                )
            """)
            conn.commit()

    def _create_default_admin_if_not_exists(self):
        """Создаёт админа admin:admin123 при первом запуске"""
        with _connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            if count == 0:
                hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                             ("admin", hashed))
                conn.commit()

    def check_credentials(self, username: str, password: str) -> bool:
        with _connect() as conn:
            cursor = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and bcrypt.checkpw(password.encode('utf-8'), row[0]):
                return True
            return False

class RoomRepository:
    def __init__(self, db_path: str = "hotel5.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
            with _connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        number INTEGER UNIQUE NOT NULL,
                        room_type TEXT NOT NULL,
                        capacity INTEGER NOT NULL,
                        price INTEGER NOT NULL,
                        status TEXT DEFAULT 'free'
                    )
                """)

                conn.commit()

    def get_all(self):
        with _connect(self.db_path) as conn:
            cur = conn.execute("SELECT id, number, room_type, capacity, price, status FROM rooms ORDER BY number")
            return [self._row_to_room(row) for row in cur.fetchall()]

    def get_by_id(self, room_id: int):
        with _connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, number, room_type, capacity, price, status FROM rooms WHERE id = ?",
                (room_id,)
            )
            row = cur.fetchone()
            return self._row_to_room(row) if row else None

    def import_from_csv(self, csv_path: str):
        """
        Импортирует номера из CSV.
        Полностью совместим с «красивым» экспортом (статусы типа "Занят до 30.11").
        """
        added = 0
        updated = 0
        skipped = 0
        errors = []

        try:
            with open(csv_path, encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                # Проверяем обязательные колонки
                required = {"№", "Тип", "Вместимость", "Цена в сутки", "Статус", "ID"}
                if not required.issubset(set(reader.fieldnames or [])):
                    missing = required - set(reader.fieldnames or [])
                    errors.append(f"Отсутствуют обязательные колонки: {', '.join(missing)}")
                    return {"added": added, "updated": updated, "skipped": skipped, "errors": errors}

            with _connect(self.db_path) as conn:
                    for row_num, row in enumerate(reader, start=2):  # start=2 — пропускаем заголовок
                        try:
                            # Читаем и чистим все поля
                            number = row["№"].strip()
                            room_type = row["Тип"].strip()
                            capacity_str = row["Вместимость"].strip()
                            price_str = row["Цена в сутки"].strip()
                            raw_status = row["Статус"].strip()
                            id_str = row["ID"].strip()

                            # Проверка на пустые обязательные поля
                            if not all([number, room_type, capacity_str, price_str, id_str]):
                                errors.append(f"Строка {row_num}: пустые обязательные поля")
                                skipped += 1
                                continue


                            try:
                                room_id = int(id_str)
                                capacity = int(capacity_str)

                                # Убираем пробелы, ₽, запятые и т.п.
                                price_clean = price_str.replace(' ', '').replace('₽', '').replace(',', '.')
                                price = float(price_clean)

                                if room_id <= 0 or capacity < 1 or price < 0:
                                    raise ValueError("Недопустимые значения (ID>0, вместимость≥1, цена≥0)")

                            except ValueError as ve:
                                errors.append(
                                    f"Строка {row_num}: неверные числа — "
                                    f"ID='{id_str}', Вместимость='{capacity_str}', Цена='{price_str}'"
                                )
                                skipped += 1
                                continue


                            status = "busy" if "занят" in raw_status.lower() else "free"
                            cur = conn.execute("SELECT id FROM rooms WHERE id = ?", (room_id,))
                            if cur.fetchone():  # номер уже существует → обновляем
                                conn.execute("""
                                    UPDATE rooms 
                                    SET number=?, room_type=?, capacity=?, price=?, status=?
                                    WHERE id=?
                                """, (number, room_type, capacity, price, status, room_id))
                                updated += 1
                            else:  # новый номер → вставляем
                                conn.execute("""
                                    INSERT INTO rooms (id, number, room_type, capacity, price, status)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (room_id, number, room_type, capacity, price, status))
                                added += 1

                        except Exception as e:
                            errors.append(f"Строка {row_num}: неожиданная ошибка — {str(e)}")
                            skipped += 1

                    conn.commit()

            return {
                "added": added,
                "updated": updated,
                "skipped": skipped,
                "errors": errors
            }

        except Exception as e:
            return {
                "added": added,
                "updated": updated,
                "skipped": skipped,
                "errors": [f"Ошибка чтения файла: {str(e)}"]
            }

    def add(self, number: int, room_type: str, capacity: int, price: int):
        with _connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO rooms (number, room_type, capacity, price, status)
                    VALUES (?, ?, ?, ?, 'free')
                """, (number, room_type, capacity, price))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(f"Номер {number} уже существует!")

    def update(self, room_id: int, number: int, room_type: str, capacity: int, price: int):
        with _connect(self.db_path) as conn:
            try:
                conn.execute("""
                    UPDATE rooms SET number=?, room_type=?, capacity=?, price=?
                    WHERE id=?
                """, (number, room_type, capacity, price, room_id))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(f"Номер {number} уже занят другим!")

    def delete(self, room_id: int):
        with _connect(self.db_path) as conn:
            # Проверяем, есть ли клиенты в номере
            cur = conn.execute("SELECT COUNT(*) FROM clients WHERE room_id = ?", (room_id,))
            if cur.fetchone()[0] > 0:
                raise ValueError("Невозможно удалить номер: в нём есть клиенты!")

            # Если нет клиентов — удаляем
            conn.execute("DELETE FROM rooms WHERE id=?", (room_id,))
            conn.commit()



    def _row_to_room(self, row):
        return type('Room', (), {
            'id': row[0],
            'number': row[1],
            'room_type': row[2],
            'capacity': row[3],
            'price': row[4],
            'status': row[5]
        })()

    def get_all_room_statuses(self):
        """
        Возвращает словарь {room_id: (status, status_text, color)}
        Статусы вычисляются для всех комнат за один раз.
        """
        today_str = QtCore.QDate.currentDate().toString("dd.MM.yyyy")
        today_iso = self._normalize_date(today_str)

        with _connect(self.db_path) as conn:
            # Берём все комнаты
            rooms = conn.execute("SELECT id, number FROM rooms").fetchall()

            # Берём все текущие брони на сегодня
            cur_bookings = conn.execute(f"""
                SELECT room_id, date_end FROM clients
                WHERE (substr(date_start, 7,4) || '-' || substr(date_start, 4,2) || '-' || substr(date_start, 1,2)) <= ?
                  AND (substr(date_end,   7,4) || '-' || substr(date_end,   4,2) || '-' || substr(date_end,   1,2)) >= ?
            """, (today_iso, today_iso)).fetchall()
            current_dict = {r[0]: r[1] for r in cur_bookings}  # {room_id: date_end}

            # Берём ближайшие брони после сегодня
            next_bookings = conn.execute(f"""
                SELECT room_id, date_start FROM clients
                WHERE (substr(date_start, 7,4) || '-' || substr(date_start, 4,2) || '-' || substr(date_start, 1,2)) > ?
                ORDER BY room_id, (substr(date_start, 7,4) || substr(date_start, 4,2) || substr(date_start, 1,2))
            """, (today_iso,)).fetchall()
            next_dict = {}
            for room_id, date_start in next_bookings:
                if room_id not in next_dict:
                    next_dict[room_id] = date_start

            # Формируем итоговый словарь
            statuses = {}
            for room_id, number in rooms:
                if room_id in current_dict:
                    end_date = QtCore.QDate.fromString(current_dict[room_id], "dd.MM.yyyy")
                    statuses[room_id] = ("busy", f"Занят до {end_date.toString('dd.MM')}", "#dc3545")
                elif room_id in next_dict:
                    next_start = QtCore.QDate.fromString(next_dict[room_id], "dd.MM.yyyy")
                    statuses[room_id] = ("free", f"Свободен до {next_start.toString('dd.MM')}", "#28a745")
                else:
                    statuses[room_id] = ("free", "Свободен", "#28a745")
        return statuses
    def update_all_room_statuses(self):
        rooms = self.get_all()
        for room in rooms:
            self.update_room_status(room.id)

    def update_room_status(self, room_id: int):
        """Автоматически меняет статус номера: free / busy"""
        with _connect(self.db_path) as conn:
            # Проверяем, есть ли активные брони на этот номер
            today = QtCore.QDate.currentDate().toString("dd.MM.yyyy")
            cur = conn.execute("""
                SELECT COUNT(*) FROM clients 
                WHERE room_id = ? 
                AND date_start <= ? 
                AND date_end >= ?
            """, (room_id, today, today))

            is_busy = cur.fetchone()[0] > 0
            status = 'busy' if is_busy else 'free'

            conn.execute("UPDATE rooms SET status = ? WHERE id = ?", (status, room_id))
            conn.commit()
    def normalize(self, date_str: str) -> str:
        return f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"

    def _normalize_date(self, date_str: str) -> str:
        """
        '15.03.2025' → '2025-03-15'
        Вынесено в отдельный метод — используется везде
        """
        if not date_str or len(date_str) != 10:
            return "9999-99-99"  # защита
        return f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"

    def is_room_available(self, room_id: int, date_start: str, date_end: str) -> bool:
        """
        Проверяет, свободен ли номер в указанный период.
        """
        start_iso = self._normalize_date(date_start)
        end_iso = self._normalize_date(date_end)

        with _connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT 1 FROM clients
                WHERE room_id = ?
                  AND (
                        -- существующая бронь начинается до конца новой
                        (substr(date_start, 7,4) || '-' || substr(date_start, 4,2) || '-' || substr(date_start, 1,2)) <= ?
                    AND
                        -- существующая бронь заканчивается после начала новой
                        (substr(date_end,   7,4) || '-' || substr(date_end,   4,2) || '-' || substr(date_end,   1,2)) >= ?
                  )
                LIMIT 1
            """, (room_id, end_iso, start_iso))

            return cur.fetchone() is None  # True = свободен


class WorkerRepository:
    def __init__(self, db_path: str = "hotel5.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with _connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fio TEXT NOT NULL,
                    position TEXT NOT NULL,
                    contacts TEXT,
                    schedule TEXT DEFAULT 'Пн-Пт 9:00-18:00'
                )
            """)
            conn.commit()

    def import_from_csv(self, csv_path: str):

        added = 0
        skipped = 0
        errors = []

        try:
            with open(csv_path, encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                # Проверяем нужные колонки
                required = {"ФИО", "Контакты", "График", "Должность"}
                if not required.issubset(set(reader.fieldnames or [])):
                    missing = required - set(reader.fieldnames or [])
                    errors.append(f"Отсутствуют колонки: {', '.join(missing)}")
                    return {"added": added, "skipped": skipped, "errors": errors}

                with _connect(self.db_path) as conn:
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            fio = row["ФИО"].strip()
                            contacts = row["Контакты"].strip()
                            schedule = row["График"].strip()
                            position = row["Должность"].strip()

                            if not fio or not position:
                                errors.append(f"Строка {row_num}: не заполнены ФИО или Должность")
                                skipped += 1
                                continue

                            # Проверяем дубли по ФИО (чтобы не было повторов)
                            cur = conn.execute("SELECT id FROM workers WHERE fio = ?", (fio,))
                            if cur.fetchone():
                                skipped += 1
                                continue  # или можно обновлять — но пока просто пропускаем

                            conn.execute("""
                                INSERT INTO workers (fio, position, contacts, schedule)
                                VALUES (?, ?, ?, ?)
                            """, (fio, position, contacts or None, schedule or "5/2"))

                            added += 1

                        except Exception as e:
                            errors.append(f"Строка {row_num}: {str(e)}")
                            skipped += 1

                    conn.commit()

            return {"added": added, "skipped": skipped, "errors": errors}

        except Exception as e:
            return {"added": added, "skipped": skipped, "errors": [f"Ошибка чтения файла: {e}"]}
    def get_all(self):
        with _connect(self.db_path) as conn:
            cur = conn.execute("SELECT id, fio, contacts, schedule, position FROM workers ORDER BY fio")
            return [self._row_to_worker(row) for row in cur.fetchall()]

    def add(self, fio: str, position: str, contacts: str = "", schedule: str = "Пн-Пт 9:00-18:00"):
        with _connect(self.db_path) as conn:
            conn.execute("INSERT INTO workers (fio, position, contacts, schedule) VALUES (?, ?, ?, ?)",
                         (fio, position, contacts, schedule))
            conn.commit()

    def update(self, worker_id: int, fio: str, position: str, contacts: str, schedule: str):
        with _connect(self.db_path) as conn:
            conn.execute("""
                UPDATE workers SET fio=?, position=?, contacts=?, schedule=?
                WHERE id=?
            """, (fio, position, contacts, schedule, worker_id))
            conn.commit()

    def delete(self, worker_id: int):
        with _connect(self.db_path) as conn:
            conn.execute("DELETE FROM workers WHERE id=?", (worker_id,))
            conn.commit()

    def _row_to_worker(self, row):
        return type('Worker', (), {
            'id': row[0],
            'fio': row[1],
            'contacts': row[2] or "—",
            'schedule': row[3],
            'position': row[4]
        })()