from PyQt5 import QtWidgets, QtCore
from dialogs import AddGuestsDialog, EditClientDialog
from PyQt5.QtCore import QObject, pyqtSignal

class ClientController(QObject):
    clients_changed = pyqtSignal()

    def __init__(self, window, table_widget, room_db, client_db):
        super().__init__()
        self.window = window
        self.table = table_widget
        self.client_db = client_db
        self.room_db = room_db

        self._load_room_search_combobox()

        self._connect_signals()
        self.load_clients_from_db()

    def _load_room_search_combobox(self):
        """Заполняет QComboBox для поиска по номеру комнаты."""
        self.window.comboRoomSearch.clear()
        self.window.comboRoomSearch.addItem("Все номера", None)
        for room in self.room_db.get_all():
            text = f"{room.number} — {room.room_type} ({room.capacity} чел.)"
            self.window.comboRoomSearch.addItem(text, room.id)
    def _connect_signals(self):
        self.window.pushButtonAddClients.clicked.connect(self.add_client)
        self.window.pushButtonEditClients.clicked.connect(self.edit_client)
        self.window.pushButtonRemoveClients.clicked.connect(self.remove_client)

        # Поиск
        self.window.lineFIO_clientEdit.textChanged.connect(self.search_clients)
        self.window.comboRoomSearch.currentTextChanged.connect(self.search_clients)

    def _fill_clients_table(self, clients):
        self.table.setRowCount(0)

        for client_id, fio, room_number, room_type, date_start, date_end, _ in clients:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(fio))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(room_number)))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(date_start))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(date_end))

            id_item = QtWidgets.QTableWidgetItem(str(client_id))
            id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 4, id_item)

    def load_clients_from_db(self):
        clients = self.client_db.get_all_with_room_info()
        self._fill_clients_table(clients)
        self.window.statusbar.showMessage(f"Загружено клиентов: {len(clients)}", 3000)

    def search_clients(self):
        fio_text = self.window.lineFIO_clientEdit.text().strip().lower()
        selected_room_id = self.window.comboRoomSearch.currentData()

        all_clients = self.client_db.get_all_with_room_info()

        results = []

        for client in all_clients:
            client_id, fio, room_number, room_type, date_start, date_end, room_id = client
            fio_lower = fio.lower()

            if fio_text and fio_text not in fio_lower:
                continue

            # Поиск по номеру комнаты
            if selected_room_id is not None and room_id != selected_room_id:
                continue

            results.append(client)
        self._fill_clients_table(results)

        self.window.statusbar.showMessage(f"Найдено: {len(results)} клиентов", 3000)

    def add_client(self):
        dialog = AddGuestsDialog(self.client_db, self.window)

        for room in self.room_db.get_all():
            text = f"{room.number} — {room.room_type} ({room.capacity} чел.)"
            dialog.combo_room.addItem(text, room.id)

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        data = dialog.get_data()
        guests = data["guests"]
        room_id = data["room_id"]
        date_start = data["date_start"].toString("dd.MM.yyyy")
        date_end = data["date_end"].toString("dd.MM.yyyy")

        try:
            for guest in guests:
                self.client_db.add_client(
                    fio=guest["fio"],
                    room_id=room_id,
                    date_start=date_start,
                    date_end=date_end
                )

            # Обновляем интерфейс
            self.load_clients_from_db()

            # Переключаемся на вкладку с номерами, чтобы было видно обновление
            self.clients_changed.emit()

            QtWidgets.QMessageBox.information(
                self.window,
                "Успех",
                f"Успешно добавлено гостей: {len(guests)} в номер {dialog.combo_room.currentText().split(' — ')[0]}\n"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(e))
            return

    def edit_client(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Выберите клиента!")
            return

        client_id = int(self.table.item(row, 4).text())
        current_fio = self.table.item(row, 0).text()

        dialog = EditClientDialog(self.client_db, self.room_db, self.window)
        dialog.setWindowTitle("Редактировать клиента")
        dialog.lineFIO.setText(current_fio)

        dialog.dateStart.setDate(QtCore.QDate.fromString(self.table.item(row, 2).text(), "dd.MM.yyyy"))
        dialog.dateEnd.setDate(QtCore.QDate.fromString(self.table.item(row, 3).text(), "dd.MM.yyyy"))

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        data = dialog.get_data()

        try:
            self.client_db.update_client(
                client_id=client_id,
                fio=data["fio"].strip(),
                room_id=data["room_id"],
                date_start=data["date_start"].toString("dd.MM.yyyy"),
                date_end=data["date_end"].toString("dd.MM.yyyy")
            )

            self.load_clients_from_db()

            self.clients_changed.emit()

            QtWidgets.QMessageBox.information(self.window, "Успех", "Клиент обновлён!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(e))

    def remove_client(self):
        rows = sorted(
            {index.row() for index in self.table.selectedIndexes()},
            reverse=True
        )

        if not rows:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Удаление",
                "Выберите клиента(ов)"
            )
            return

        count = len(rows)
        message = (
            "Удалить выбранного клиента навсегда?"
            if count == 1
            else f"Удалить {count} клиентов навсегда?\n\nЭто действие нельзя отменить!"
        )

        msg = QtWidgets.QMessageBox(self.window)
        msg.setWindowTitle("Подтверждение удаления")
        msg.setText(message)
        msg.setIcon(QtWidgets.QMessageBox.Question)

        btn_yes = msg.addButton("Да", QtWidgets.QMessageBox.YesRole)
        msg.addButton("Нет", QtWidgets.QMessageBox.NoRole)

        msg.exec_()

        if msg.clickedButton() != btn_yes:
            return
        client_ids = [
            int(self.table.item(row, 4).text())
            for row in rows
        ]

        try:
            self.client_db.delete_clients(client_ids)

            self.load_clients_from_db()

            self.clients_changed.emit()

            QtWidgets.QMessageBox.information(
                self.window,
                "Успех",
                "Клиенты удалены"
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.window,
                "Ошибка",
                str(e)
            )


