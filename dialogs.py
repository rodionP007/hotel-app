from PyQt5 import QtGui
from PyQt5 import QtWidgets, QtCore
import re
class AddGuestsDialog(QtWidgets.QDialog):
    def __init__(self, client_db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить гостей в номер")
        self.resize(600, 500)
        self.client_db = client_db
        layout = QtWidgets.QVBoxLayout(self)

        # Номер
        layout.addWidget(QtWidgets.QLabel("Номер:"))
        self.combo_room = QtWidgets.QComboBox()
        layout.addWidget(self.combo_room)
        today = QtCore.QDate.currentDate()
        # Даты
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Заезд:"))
        self.date_start = QtWidgets.QDateEdit()
        self.date_start.setDate(QtCore.QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        hbox.addWidget(self.date_start)
        hbox.addWidget(QtWidgets.QLabel("Выезд:"))
        self.date_end = QtWidgets.QDateEdit()
        self.date_end.setDate(QtCore.QDate.currentDate().addDays(1))
        self.date_end.setCalendarPopup(True)
        self.date_end.setMinimumDate(today.addDays(0))
        hbox.addWidget(self.date_end)
        layout.addLayout(hbox)

        self.date_start.dateChanged.connect(self.on_start_date_changed)
        self.on_start_date_changed(today)
        # Список гостей
        layout.addWidget(QtWidgets.QLabel("Гости:"))
        self.guests_list = QtWidgets.QListWidget()
        self.guests_list.setMinimumHeight(220)
        self.guests_list.setStyleSheet("font-size: 11pt; padding: 5px;")
        layout.addWidget(self.guests_list)

        btn_add = QtWidgets.QPushButton("Добавить гостя")
        btn_add.setStyleSheet("padding: 10px; font-size: 11pt;")
        btn_add.clicked.connect(self.add_guest_row)
        layout.addWidget(btn_add)

        # Кнопки
        buttons = QtWidgets.QDialogButtonBox()
        ok_button = buttons.addButton("OK", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("Отмена", QtWidgets.QDialogButtonBox.RejectRole)

        # Подключаем сигналы
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.guest_widgets = []

    def validate(self) -> bool:

        # 1. Выбор номера
        if self.combo_room.currentIndex() == -1:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите номер комнаты!")
            return False

        room_id = self.combo_room.currentData()
        if not room_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось получить номер комнаты!")
            return False

        # 2. Даты
        start_qdate = self.date_start.date()
        end_qdate = self.date_end.date()

        if start_qdate > end_qdate:
            QtWidgets.QMessageBox.warning(self, "Неверные даты", "Дата выезда должна быть позже заезда!")
            return False

        date_start_str = start_qdate.toString("dd.MM.yyyy")
        date_end_str = end_qdate.toString("dd.MM.yyyy")
        # 3. Проверка: номер свободен?
        if not self.client_db.is_room_available(room_id, date_start_str, date_end_str):
            QtWidgets.QMessageBox.warning(
                self,
                "Номер занят!",
                f"Номер уже забронирован на период:\n{date_start_str} — {date_end_str}\n\n"
                "Выберите другие даты или другой номер."
            )
            return False

        # 4. Проверка количества мест
        room = self.client_db.get_room_by_id(room_id)
        if not room:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Номер не найден в базе!")
            return False

        current_occupancy = self.client_db.get_current_occupancy(room_id, date_start_str, date_end_str)
        new_guests = len([w for w in self.guest_widgets if w[0].text().strip()])

        if current_occupancy + new_guests > room.capacity:
            QtWidgets.QMessageBox.warning(
                self,
                "Нет мест!",
                f"В номере {room.number} только {room.capacity} мест(а)\n"
                f"Сейчас занято: {current_occupancy}, вы добавляете: {new_guests}\n"
                f"Недостаточно мест!"
            )
            return False

        # 5. Минимум один гость
        if new_guests == 0:
            QtWidgets.QMessageBox.warning(self, "Нет гостей", "Добавьте хотя бы одного гостя!")
            return False


        for i, (fio_edit, child_cb) in enumerate(self.guest_widgets, start=1):
            fio = fio_edit.text().strip()
            if not fio:
                QtWidgets.QMessageBox.warning(self, "Пустое ФИО", f"Гость {i}: укажите ФИО!")
                fio_edit.setFocus()
                return False

            parts = fio.split()
            if len(parts) < 2:
                QtWidgets.QMessageBox.warning(self, "ФИО", f"Гость {i}: укажите фамилию и имя!")
                fio_edit.setFocus()
                return False

            for word in parts:
                if len(word) < 2:
                    QtWidgets.QMessageBox.warning(self, "Короткое", f"Гость {i}: «{word}» — минимум 2 буквы!")
                    fio_edit.setFocus()
                    return False

                # Запрет на ВСЁ КАПСОМ (ИВАНОВ, ПЕТРОВ и т.д.)
                if word.isupper() and len(word) > 1:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Недопустимый ввод",
                        f"Гость {i}: слово «{word}» написано полностью заглавными буквами!\n\n"
                        "Пишите нормально: Иванов Иван, а не ИВАНОВ ИВАН"
                    )
                    fio_edit.setFocus()
                    return False

                # Запрет на "лесенку" и странный регистр (ИваНов, иВан, ИвАнов и т.п.)
                if len(word) > 2:  # только для слов длиннее 2 букв
                    has_ladder = False
                    for j in range(len(word) - 1):
                        if word[j].islower() and word[j + 1].isupper():
                            has_ladder = True
                            break
                    if has_ladder or (word[0].islower()) or (
                            sum(1 for c in word[1:] if c.isupper()) > 0 and word != word.capitalize()):
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Неправильный регистр",
                            f"Гость {i}: слово «{word}» написано неправильно (лесенка, ошибка регистра).\n\n"
                            "Пишите: Иванов, Петрова-Сидорова\n"
                            "Нельзя: ИваНов, иВАН, ИвАнов"
                        )
                        fio_edit.setFocus()
                        return False

                # Остальные проверки
                if not all(ch.isalpha() or ch == '-' for ch in word):
                    QtWidgets.QMessageBox.warning(self, "Символы", f"Гость {i}: в «{word}» только буквы и дефис!")
                    fio_edit.setFocus()
                    return False

                if word.startswith('-') or word.endswith('-') or '--' in word:
                    QtWidgets.QMessageBox.warning(self, "Дефис", f"Гость {i}: ошибка в написании «{word}»!")
                    fio_edit.setFocus()
                    return False

                if not word[0].isupper():
                    QtWidgets.QMessageBox.warning(self, "Регистр",
                                                  f"Гость {i}: «{word}» должно начинаться с заглавной буквы!")
                    fio_edit.setFocus()
                    return False

        return True

    def add_guest_row(self):
        row = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(row)
        hbox.setContentsMargins(8, 8, 8, 8)
        hbox.setSpacing(12)

        fio = QtWidgets.QLineEdit()
        fio.setPlaceholderText("ФИО гостя (Иванов Иван Иванович)")
        fio.setStyleSheet("padding: 10px; font-size: 11pt;")

        child = QtWidgets.QCheckBox("Ребёнок")
        child.setStyleSheet("font-size: 10pt;")

        # Растягиваем поле ФИО, чекбокс прижат вправо
        hbox.addWidget(fio, stretch=1)
        hbox.addWidget(child)

        item = QtWidgets.QListWidgetItem()
        self.guests_list.addItem(item)
        self.guests_list.setItemWidget(item, row)
        item.setSizeHint(row.sizeHint())  # важно!

        # ← ВОЗВРАЩАЕМ ПАРУ (fio, child_cb)
        self.guest_widgets.append((fio, child))

    def get_data(self):
        room_id = self.combo_room.currentData()
        guests = []
        for fio_edit, child_cb in self.guest_widgets:
            fio = fio_edit.text().strip()
            if fio:
                guests.append({
                    "fio": fio,
                    "is_child": child_cb.isChecked()
                })
        return {
            "room_id": room_id,
            "date_start": self.date_start.date(),
            "date_end": self.date_end.date(),
            "guests": guests
        }

    def on_start_date_changed(self, new_start_date):
        """
        Когда меняется заезд — выезд не может быть раньше заезда
        """
        current_end = self.date_end.date()

        # Устанавливаем минимальную дату выезда = заезд + 1
        min_end_date = new_start_date.addDays(0)
        self.date_end.setMinimumDate(min_end_date)

        if current_end <= min_end_date:
            self.date_end.setDate(min_end_date)

    def accept(self):
        if self.validate():
            super().accept()
class EditClientDialog(QtWidgets.QDialog):
    def __init__(self, client_db, room_repo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить клиента")
        self.setMinimumWidth(420)

        self.client_db = client_db
        self.room_repo = room_repo
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        # ФИО
        self.lineFIO = QtWidgets.QLineEdit()
        self.lineFIO.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:", self.lineFIO)

        self.combo_room = QtWidgets.QComboBox()
        self.combo_room.setMinimumWidth(300)
        self.combo_room.setPlaceholderText("Выберите номер")
        self._fill_rooms_combo()
        form.addRow("Номер комнаты:", self.combo_room)

        # Даты
        today = QtCore.QDate.currentDate()
        self.dateStart = QtWidgets.QDateEdit()
        self.dateStart.setDate(QtCore.QDate.currentDate())
        self.dateStart.setCalendarPopup(True)
        form.addRow("Заезд:", self.dateStart)

        self.dateEnd = QtWidgets.QDateEdit()
        self.dateEnd.setDate(QtCore.QDate.currentDate().addDays(1))
        self.dateEnd.setCalendarPopup(True)
        form.addRow("Выезд:", self.dateEnd)

        # Кнопки
        buttons = QtWidgets.QDialogButtonBox()
        ok_button = buttons.addButton("OK", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("Отмена", QtWidgets.QDialogButtonBox.RejectRole)

        # Подключаем сигналы
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def validate(self) -> bool:
        """Валидация всех полей. Возвращает True только если всё идеально."""
        fio = self.lineFIO.text().strip()
        if not fio:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите ФИО клиента!")
            self.lineFIO.setFocus()
            return False
        room_id = self.combo_room.currentData()
        if not room_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось получить номер комнаты!")
            return False
        start_qdate = self.dateStart.date()
        end_qdate = self.dateEnd.date()
        if start_qdate > end_qdate:
            QtWidgets.QMessageBox.warning(self, "Неверные даты", "Дата выезда должна быть позже заезда!")
            return False
        date_start_str = start_qdate.toString("dd.MM.yyyy")
        date_end_str = end_qdate.toString("dd.MM.yyyy")
        # 3. Проверка: номер свободен?
        if not self.client_db.is_room_available(room_id, date_start_str, date_end_str):
            QtWidgets.QMessageBox.warning(
                self,
                "Номер занят!",
                f"Номер уже забронирован на период:\n{date_start_str} — {date_end_str}\n\n"
                "Выберите другие даты или другой номер."
            )
            return False
        parts = fio.split()
        if len(parts) < 2:
            QtWidgets.QMessageBox.warning(
                self, "Неверный формат ФИО",
                "Укажите хотя бы фамилию и имя!\n\nПример: Иванов Иван"
            )
            self.lineFIO.setFocus()
            return False

        for word in parts:
            # 1. Минимум 2 буквы
            if len(word) < 2:
                QtWidgets.QMessageBox.warning(
                    self, "Короткое слово",
                    f"Слово «{word}» слишком короткое!\nДолжно быть минимум 2 буквы."
                )
                self.lineFIO.setFocus()
                return False

            # 2. Запрет на ВСЁ КАПСОМ (ИВАНОВ, ПЕТРОВ)
            if word.isupper() and len(word) > 1:
                QtWidgets.QMessageBox.warning(
                    self, "КАПС ЗАПРЕЩЁН",
                    f"Слово «{word}» написано полностью заглавными буквами!\n\n"
                    "Пишите нормально: Иванов Иван\nНельзя: ИВАНОВ ИВАН"
                )
                self.lineFIO.setFocus()
                return False

            # 3. Запрет на "лесенку" и странный регистр (ИваНов, иВан, ИвАнов)
            if len(word) > 2:
                # Проверяем перепады регистра внутри слова
                has_ladder = any(word[j].islower() and word[j + 1].isupper() for j in range(len(word) - 1))
                # Или больше одной заглавной (кроме первой) — тоже подозрительно
                extra_caps = sum(1 for c in word[1:] if c.isupper()) > 0
                if has_ladder or (word[0].islower()) or extra_caps:
                    QtWidgets.QMessageBox.warning(
                        self, "Неправильный регистр",
                        f"Слово «{word}» написано странно!\n\n"
                        "Пишите: Иванов, Петрова-Сидорова\n"
                        "Нельзя: ИваНов, иВан, ИвАнов, иванов"
                    )
                    self.lineFIO.setFocus()
                    return False

            # 4. Только буквы и дефис
            if not all(ch.isalpha() or ch == '-' for ch in word):
                QtWidgets.QMessageBox.warning(
                    self, "Запрещённые символы",
                    f"В слове «{word}» есть цифры, пробелы или запрещённые знаки!\n"
                    "Разрешены только буквы и дефис."
                )
                self.lineFIO.setFocus()
                return False

            # 5. Дефисы — корректно
            if word.startswith('-') or word.endswith('-'):
                QtWidgets.QMessageBox.warning(
                    self, "Неверный дефис",
                    f"Слово «{word}» не может начинаться или заканчиваться дефисом!"
                )
                self.lineFIO.setFocus()
                return False

            if '--' in word:
                QtWidgets.QMessageBox.warning(
                    self, "Двойной дефис",
                    f"В слове «{word}» нельзя использовать два дефиса подряд!"
                )
                self.lineFIO.setFocus()
                return False

            # 6. Обязательно с заглавной буквы
            if not word[0].isupper():
                QtWidgets.QMessageBox.warning(
                    self, "Регистр",
                    f"Слово «{word}» должно начинаться с заглавной буквы!"
                )
                self.lineFIO.setFocus()
                return False

        return True

    def accept(self):
        """ОК работает только после полной валидации"""
        if self.validate():
            super().accept()
    def _fill_rooms_combo(self):
        """Заполняет комбобокс номерами"""
        self.combo_room.clear()
        rooms = self.room_repo.get_all()
        for room in rooms:
            text = f"{room.number} — {room.room_type} ({room.capacity} чел., {room.price:,} ₽/сутки)"
            self.combo_room.addItem(text, userData=room.id)

        if rooms:
            self.combo_room.setCurrentIndex(0)

    def get_data(self):
        """Возвращает данные, включая room_id"""
        room_id = self.combo_room.currentData()  # ← вот тут берём ID!
        if room_id is None:
            room_id = -1  # защита от пустого

        return {
            "fio": self.lineFIO.text().strip(),
            "room_id": room_id,
            "date_start": self.dateStart.date(),
            "date_end": self.dateEnd.date()
        }
    def set_room_by_id(self, room_id: int):
        index = self.combo_room.findData(room_id)
        if index >= 0:
            self.combo_room.setCurrentIndex(index)
class LoginDialog(QtWidgets.QDialog):
    """
    Окно входа в систему.
    Появляется при запуске программы.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(600, 500)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)

        # Основной layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Заголовок
        title = QtWidgets.QLabel("Панель администратора гостиницы")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title_font = QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel("Войдите в систему")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6c757d; font-size: 11pt;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Поле логина
        self.edit_login = QtWidgets.QLineEdit()
        self.edit_login.setPlaceholderText("Логин")
        self.edit_login.setText("admin")  # для удобства тестирования
        self.edit_login.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 8px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #0078d7;
            }
        """)
        layout.addWidget(self.edit_login)

        # Поле пароля
        self.edit_password = QtWidgets.QLineEdit()
        self.edit_password.setPlaceholderText("Пароль")
        self.edit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.edit_password.setText("admin123")  # для удобства
        self.edit_password.setStyleSheet(self.edit_login.styleSheet())
        layout.addWidget(self.edit_password)

        layout.addSpacing(10)

        # Чекбокс "Показать пароль"
        self.show_password_cb = QtWidgets.QCheckBox("Показать пароль")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        layout.addSpacing(20)

        # Кнопка входа
        self.btn_login = QtWidgets.QPushButton("Войти")
        self.btn_login.setDefault(True)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004c87;
            }
        """)
        layout.addWidget(self.btn_login)

        # Информация о первом запуске
        info = QtWidgets.QLabel("При первом запуске:\nЛогин: admin\nПароль: admin123")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #6c757d; font-size: 9pt;")
        layout.addWidget(info)

        # Подключим Enter
        self.btn_login.clicked.connect(self.accept)
        self.edit_password.returnPressed.connect(self.accept)
        self.edit_login.returnPressed.connect(self.edit_password.setFocus)

    def toggle_password_visibility(self, checked):
        if checked:
            self.edit_password.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.edit_password.setEchoMode(QtWidgets.QLineEdit.Password)

    def get_credentials(self):
        return self.edit_login.text().strip(), self.edit_password.text()


class AddRoomDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить номер")
        self.resize(500, 250)

        layout = QtWidgets.QFormLayout(self)

        self.spinNumber = QtWidgets.QSpinBox()
        self.spinNumber.setRange(1, 999)
        self.spinNumber.setValue(101)

        self.comboType = QtWidgets.QComboBox()
        self.comboType.addItems(["Люкс", "Эконом", "Премиум-люкс", "Президентский"])

        self.spinCapacity = QtWidgets.QSpinBox()
        self.spinCapacity.setRange(1, 10)
        self.spinCapacity.setValue(2)

        self.spinPrice = QtWidgets.QSpinBox()
        self.spinPrice.setRange(1000, 100000)
        self.spinPrice.setValue(8000)
        self.spinPrice.setSuffix(" ₽")

        buttons = QtWidgets.QDialogButtonBox()
        ok_button = buttons.addButton("OK", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("Отмена", QtWidgets.QDialogButtonBox.RejectRole)

        # Подключаем сигналы
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        layout.addRow("Номер:", self.spinNumber)
        layout.addRow("Тип:", self.comboType)
        layout.addRow("Вместимость:", self.spinCapacity)
        layout.addRow("Цена в сутки:", self.spinPrice)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "number": self.spinNumber.value(),
            "type": self.comboType.currentText(),
            "capacity": self.spinCapacity.value(),
            "price": self.spinPrice.value()
        }

class WorkerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить сотрудника")
        self.resize(500, 300)

        layout = QtWidgets.QFormLayout(self)

        self.lineFIO = QtWidgets.QLineEdit()
        self.lineFIO.setPlaceholderText("Иванов Иван Иванович")

        self.linePosition = QtWidgets.QLineEdit()
        self.linePosition.setPlaceholderText("Администратор, горничная и т.д.")

        self.lineContacts = QtWidgets.QLineEdit()
        self.lineContacts.setPlaceholderText("+7 (999) 123-45-67")
        self.lineSchedule = QtWidgets.QLineEdit()
        self.lineSchedule.setPlaceholderText("Например: Пн–Пт 10:00–19:00")
        self.comboSchedule = QtWidgets.QComboBox()
        self.comboSchedule.addItems([
            "Пн–Пт 9:00–18:00",
            "Пн–Пт 8:00–17:00",
            "Пн–Вс 2/2 9:00–21:00",
            "Сменный 2/2",
            "Гибкий график",
            "Кастомный..."
        ])
        self.comboSchedule.currentTextChanged.connect(self.schedule_from_combo)

        layout.addRow("ФИО:", self.lineFIO)
        layout.addRow("Должность:", self.linePosition)
        layout.addRow("Контакты:", self.lineContacts)
        layout.addRow("График:", self.comboSchedule)
        layout.addRow("Описание:", self.lineSchedule)

        buttons = QtWidgets.QDialogButtonBox()
        ok_button = buttons.addButton("OK", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton("Отмена", QtWidgets.QDialogButtonBox.RejectRole)

        # Подключаем сигналы
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def schedule_from_combo(self, text):
        if text == "Кастомный...":
            self.lineSchedule.setText("")
            self.lineSchedule.setFocus()
        else:
            self.lineSchedule.setText(text)

    def validate_fio(self):
        fio = self.lineFIO.text().strip()

        if not fio:
            self.error("Введите ФИО сотрудника!", self.lineFIO)
            return False

        parts = fio.split()
        if len(parts) < 2:
            self.error("Укажите хотя бы фамилию и имя!\nПример: Иванов Иван", self.lineFIO)
            return False

        for word in parts:
            # 1. Минимум 2 буквы
            if len(word) < 2:
                self.error(f"Слово «{word}» слишком короткое! Минимум 2 буквы.", self.lineFIO)
                return False

            # 2. ЗАПРЕТ НА КАПС (ИВАНОВ, ПЕТРОВ и т.д.)
            if word.isupper() and len(word) > 1:
                self.error(f"Слово «{word}» написано ВСЁ КАПСОМ!\nПишите нормально: Иванов Иван", self.lineFIO)
                return False

            # 3. Запрет на "лесенку" и странный регистр (ИваНов, иВан, ИвАнов)
            if len(word) > 2:
                has_ladder = any(word[j].islower() and word[j + 1].isupper() for j in range(len(word) - 1))
                extra_caps = sum(1 for c in word[1:] if c.isupper()) > 0
                if has_ladder or word[0].islower() or extra_caps:
                    self.error(
                        f"Слово «{word}» написано неправильно!\n"
                        "Пишите: Иванов, Петрова-Сидорова\n"
                        "Нельзя: ИваНов, иВан, ИвАнов, иванов",
                        self.lineFIO
                    )
                    return False

            # 4. Только буквы и дефис
            if not all(ch.isalpha() or ch == '-' for ch in word):
                self.error(f"В слове «{word}» запрещённые символы!\nРазрешены только буквы и дефис.", self.lineFIO)
                return False

            # 5. Дефисы корректно
            if word.startswith('-') or word.endswith('-'):
                self.error(f"Слово «{word}» не должно начинаться или заканчиваться дефисом!", self.lineFIO)
                return False
            if '--' in word:
                self.error(f"В слове «{word}» нельзя использовать два дефиса подряд!", self.lineFIO)
                return False

            # 6. Обязательно с заглавной
            if not word[0].isupper():
                self.error(f"Слово «{word}» должно начинаться с заглавной буквы!", self.lineFIO)
                return False

        return True

    def validate_position(self):
        pos = self.linePosition.text().strip()
        if not pos:
            self.error("Введите должность сотрудника!", self.linePosition)
            return False

        if len(pos) < 2:
            self.error("Название должности слишком короткое! Минимум 2 буквы.", self.linePosition)
            return False

        # 1. ЗАПРЕТ НА КАПС
        if pos.isupper():
            self.error("Должность написана ВСЁ КАПСОМ!\nПишите нормально: Старший администратор", self.linePosition)
            return False

        # 2. Запрет на лесенку и странный регистр
        if len(pos) > 3:
            has_ladder = any(pos[j].islower() and pos[j + 1].isupper() for j in range(len(pos) - 1))
            if has_ladder or pos[0].islower():
                self.error(
                    "Должность написана странно (лесенка или маленькая буква в начале)!\n"
                    "Пишите: Главный бухгалтер, Старший менеджер",
                    self.linePosition
                )
                return False

        # 3. Только разрешённые символы
        if not all(ch.isalpha() or ch in " -." for ch in pos):
            self.error("Должность может содержать только буквы, пробелы, точки и дефисы.", self.linePosition)
            return False

        # 4. Обязательно с заглавной
        if not pos[0].isupper():
            self.error("Должность должна начинаться с заглавной буквы!", self.linePosition)
            return False

        return True

    def validate_contacts(self):
        contacts = self.lineContacts.text().strip()

        if not contacts:
            self.error("Введите телефон!", self.lineContacts)
            return False

        raw = contacts

        # ---- Запрещённые крайние символы ----
        if raw[0] in "-()" or raw[-1] in "-()":
            self.error("Некорректный ввод", self.lineContacts)
            return False

        # ---- Запрет двойных дефисов и пробелов ----
        if "--" in raw or "  " in raw:
            self.error("Телефон содержит некорректные подряд идущие символы.", self.lineContacts)
            return False

        # ---- Разрешённые символы ----
        for ch in raw:
            if not (ch.isdigit() or ch in "+-() "):
                self.error("Некорректный ввод телефона", self.lineContacts)
                return False

        # ---- Проверка расположения знака + ----
        if "+" in raw and not raw.startswith("+"):
            self.error("Знак '+' может быть только в начале номера.", self.lineContacts)
            return False

        # ---- Нормализуем: убираем все нецифры ----
        digits = "".join(ch for ch in raw if ch.isdigit())

        # ---- Проверяем количество цифр ----
        if len(digits) != 11:
            self.error("Номер должен содержать 11 цифр (например, +7 999 123-45-67).", self.lineContacts)
            return False

        # ---- Проверяем код страны ----
        if not (digits.startswith("7") or digits.startswith("8")):
            self.error("Телефон должен начинаться с +7 или 8.", self.lineContacts)
            return False

        return True

    def validate_schedule(self):
        schedule = self.lineSchedule.text().strip()

        if not schedule:
            self.error("Введите график работы или выберите из списка.", self.lineSchedule)
            return False

        # Проверка на формат времени (минимальная)
        time_pattern = r"(\d{1,2}[:.]\d{2})"

        # Если в графике нет времени — не обязательно ошибка
        # Например: "Сменный 2/2"
        if not re.search(time_pattern, schedule):
            # Но если это кастомный, просим уточнить
            if self.comboSchedule.currentText() == "Кастомный...":
                self.error("Укажите время работы, например: 9:00–18:00", self.lineSchedule)
                return False
            return True

        # График должен содержать 2 времени: начало и конец
        times = re.findall(time_pattern, schedule)
        if len(times) < 1:
            self.error("График должен содержать время, например: 9:00–18:00", self.lineSchedule)
            return False

        return True

    def validate(self):
        return (
            self.validate_fio() and
            self.validate_position() and
            self.validate_contacts() and
            self.validate_schedule()
        )

    def error(self, msg, widget):
        QtWidgets.QMessageBox.warning(self, "Ошибка", msg)
        widget.setFocus()

    def accept(self):
        """ОК работает только после полной валидации"""
        if self.validate():
            super().accept()
    def get_data(self):
        return {
            "fio": self.lineFIO.text().strip(),
            "position": self.linePosition.text().strip(),
            "contacts": self.lineContacts.text().strip(),
            "schedule": self.lineSchedule.text().strip()
        }

    def set_data(self, fio="", position="", contacts="", schedule=""):
        self.lineFIO.setText(fio)
        self.linePosition.setText(position)
        self.lineContacts.setText(contacts)
        self.lineSchedule.setText(schedule)

class HelpWindow(QtWidgets.QDialog):
    def __init__(self, parent=None, text=""):
        super().__init__(parent)

        self.setWindowTitle("Справка")
        self.resize(700, 600)

        layout = QtWidgets.QVBoxLayout(self)

        # Текстовое поле со скроллом (только чтение)
        text_box = QtWidgets.QTextBrowser(self)
        text_box.setPlainText(text)
        text_box.setOpenExternalLinks(False)

        layout.addWidget(text_box)

        # Кнопка закрытия
        btn_close = QtWidgets.QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)