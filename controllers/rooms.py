from PyQt5 import QtWidgets, QtCore, QtGui
from dialogs import AddRoomDialog


class RoomController:
    def __init__(self, window, table_widget, repo):
        self.window = window
        self.table = table_widget
        self.repo = repo
        self.rooms_cache = self.repo.get_all()
        self._connect_signals()
        self.load_rooms()

    def _connect_signals(self):
        self.window.pushButtonAddRooms.clicked.connect(self.add_room)
        self.window.pushButtonEditRooms.clicked.connect(self.edit_room)
        self.window.pushButtonRemoveRooms.clicked.connect(self.remove_room)
        self.window.comboBoxCapacityRooms.currentTextChanged.connect(self.search_rooms)
        self.window.comboBoxRoomType.currentTextChanged.connect(self.search_rooms)
        self.window.comboBox_StatusRooms.currentTextChanged.connect(self.search_rooms)

    def _fill_rooms_table(self, rooms):
        self.table.setRowCount(0)

        # Получаем статусы всех комнат сразу
        room_statuses = self.repo.get_all_room_statuses()  # {room_id: (status, status_text, color)}

        for room in rooms:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Берём статус из словаря
            status, status_text, color = room_statuses.get(room.id, ("free", "Свободен", "#28a745"))

            # Заполняем таблицу
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(room.number)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(room.room_type))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(room.capacity)))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{room.price} ₽"))

            status_item = QtWidgets.QTableWidgetItem(status_text)
            status_item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
            status_item.setTextAlignment(QtCore.Qt.AlignCenter)
            status_item.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            self.table.setItem(row, 4, status_item)

            id_item = QtWidgets.QTableWidgetItem(str(room.id))
            id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 5, id_item)

        self.table.setColumnWidth(4, 280)

    def update_room_combobox(self):
        self.window.comboRoomSearch.clear()
        self.window.comboRoomSearch.addItem("Все номера", None)
        for room in self.rooms_cache:
            text = f"{room.number} — {room.room_type} ({room.capacity} чел.)"
            self.window.comboRoomSearch.addItem(text, room.id)
    def load_rooms(self):
        self.rooms_cache = self.repo.get_all()  # обновляем кэш
        self._fill_rooms_table(self.rooms_cache)  # заполняем таблицу
        self.update_room_combobox()

    def add_room(self):
        dialog = AddRoomDialog(self.window)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        data = dialog.get_data()

        try:
            self.repo.add(
                number=data["number"],
                room_type=data["type"],
                capacity=data["capacity"],
                price=data["price"]
            )
            self.load_rooms()
            QtWidgets.QMessageBox.information(
                self.window,
                "Успех",
                f"Номер {data['number']} успешно добавлен!"
            )

        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Ошибка добавления",
                str(e)
            )

    def edit_room(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Выберите номер!")
            return
        room_id = int(self.table.item(row, 5).text())

        dialog = AddRoomDialog(self.window)
        dialog.setWindowTitle("Редактировать номер")
        dialog.spinNumber.setValue(int(self.table.item(row, 0).text()))
        dialog.comboType.setCurrentText(self.table.item(row, 1).text())
        dialog.spinCapacity.setValue(int(self.table.item(row, 2).text()))
        dialog.spinPrice.setValue(int(self.table.item(row, 3).text().replace(" ₽", "")))

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.repo.update(
                    room_id=room_id,
                    number=data["number"],
                    room_type=data["type"],
                    capacity=data["capacity"],
                    price=data["price"]
                )
                self.load_rooms()
                self.window.clients_ctrl.load_clients_from_db()

                QtWidgets.QMessageBox.information(
                    self.window,
                    "Успех",
                    f"Номер {data['number']} успешно обновлён!"
                )

            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    self.window,
                    "Не удалось сохранить",
                    f"Ошибка:\n{str(e)}\n\n"
                    "Проверьте, не занят ли этот номер другим номером."
                )

    def remove_room(self):
        selected_rows = sorted(
            set(index.row() for index in self.table.selectedIndexes()),
            reverse=True
        )

        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Удаление",
                "Выберите хотя бы один номер для удаления"
            )
            return

        count = len(selected_rows)

        # Красивое сообщение
        if count == 1:
            message = "Удалить выбранный номер навсегда?"
        else:
            message = f"Удалить {count} номеров навсегда?\n\nЭто действие нельзя отменить!"

        msg = QtWidgets.QMessageBox(self.window)
        msg.setWindowTitle("Подтверждение удаления")
        msg.setText(message)
        msg.setIcon(QtWidgets.QMessageBox.Question)

        btn_yes = msg.addButton("Да", QtWidgets.QMessageBox.YesRole)
        btn_no = msg.addButton("Нет", QtWidgets.QMessageBox.NoRole)

        msg.exec_()

        if msg.clickedButton() != btn_yes:
            return

        deleted_count = 0
        for row in selected_rows:
            id_item = self.table.item(row, 5)  # колонка 5 — скрытая с ID
            if id_item:
                room_id = int(id_item.text())
                try:
                    self.repo.delete(room_id)
                    deleted_count += 1
                except ValueError as e:
                    QtWidgets.QMessageBox.warning(self.window, "Ошибка удаления", str(e))
                except Exception as e:
                    QtWidgets.QMessageBox.warning(f"Ошибка удаления номера ID {room_id}: {e}")

        # Обновляем таблицу
        self.load_rooms()

        # Сообщение об успехе
        if deleted_count == count:
            QtWidgets.QMessageBox.information(
                self.window,
                "Успешно",
                f"Удалено номеров: {deleted_count}"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Частичное удаление",
                f"Удалено: {deleted_count} из {count}\n"
                "Проверьте, не заняты ли номера клиентами."
            )

    def search_rooms(self):
        capacity = self.window.comboBoxCapacityRooms.currentText()
        room_type = self.window.comboBoxRoomType.currentText()
        status_filter = self.window.comboBox_StatusRooms.currentText()

        rooms = self.rooms_cache
        room_statuses = self.repo.get_all_room_statuses()

        if capacity != "Все":
            if capacity == "5+":
                rooms = [r for r in rooms if r.capacity >= 5]
            else:
                rooms = [r for r in rooms if r.capacity == int(capacity)]

            # Фильтруем по типу
        if room_type != "Все":
            rooms = [r for r in rooms if r.room_type == room_type]

            # Фильтруем по статусу
        if status_filter != "Все":
            if status_filter == "Свободен":
                rooms = [r for r in rooms if room_statuses[r.id][0] == "free"]
            elif status_filter == "Занят":
                rooms = [r for r in rooms if room_statuses[r.id][0] == "busy"]
        # Очищаем таблицу
        self.table.setRowCount(0)

        for room in rooms:
            row = self.table.rowCount()
            self.table.insertRow(row)
            room_status, status_text, color = room_statuses[room.id]
            # Заполняем таблицу
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(room.number)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(room.room_type))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(room.capacity)))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{room.price} ₽"))

            status_item = QtWidgets.QTableWidgetItem(status_text)
            status_item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
            status_item.setTextAlignment(QtCore.Qt.AlignCenter)
            status_item.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            self.table.setItem(row, 4, status_item)

            id_item = QtWidgets.QTableWidgetItem(str(room.id))
            id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 5, id_item)

        self.table.setColumnWidth(4, 280)

