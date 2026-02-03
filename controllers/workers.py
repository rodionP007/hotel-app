
from PyQt5 import QtWidgets, QtCore
from dialogs import WorkerDialog


class WorkerController:
    def __init__(self, window, table_widget, db):
        """
        window — главное окно (HotelApp)
        """
        self.window = window
        self.table = table_widget
        self.db = db

        # Настраиваем таблицу: 5 колонок, последняя — скрытая для ID
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ФИО", "Контакты", "График", "Должность", "ID"])
        self.table.setColumnHidden(4, True)

        self._connect_signals()
        self.load_workers()

    def _connect_signals(self):
        # Кнопки
        self.window.pushButtonAddPersonal.clicked.connect(self.add_worker)
        self.window.pushButtonEditPersonal.clicked.connect(self.edit_worker)
        self.window.pushButtonRemovePersonal.clicked.connect(self.remove_worker)

        # Мгновенный поиск при вводе
        self.window.lineEdit_FIOWorker.textChanged.connect(self.search_workers)
        self.window.lineEdit_Worker.textChanged.connect(self.search_workers)        # должность
        self.window.lineEdit_WorkerContact.textChanged.connect(self.search_workers)  # контакты

    # =================== Добавление сотрудника ===================
    def add_worker(self):
        dialog = WorkerDialog(self.window)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        data = dialog.get_data()

        if not data["fio"].strip():
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Введите ФИО сотрудника!")
            return
        if not data["position"].strip():
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Укажите должность!")
            return

        self.db.add(
            fio=data["fio"],
            position=data["position"],
            contacts=data["contacts"],
            schedule=data["schedule"] or "Пн-Пт 9:00-18:00"
        )

        self.load_workers()
        QtWidgets.QMessageBox.information(self.window, "Успех", "Сотрудник добавлен!")

    # =================== Редактирование сотрудника ===================
    def edit_worker(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self.window, "Редактирование", "Выберите сотрудника для редактирования")
            return

        worker_id = int(self.table.item(row, 4).text())

        # Получаем текущие данные
        fio = self.table.item(row, 0).text()
        contacts = self.table.item(row, 1).text()
        schedule = self.table.item(row, 2).text()
        position = self.table.item(row, 3).text()

        # Открываем диалог
        dialog = WorkerDialog(self.window)
        dialog.setWindowTitle("Редактировать сотрудника")
        dialog.set_data(fio, position, contacts, schedule)

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        new_data = dialog.get_data()

        if not new_data["fio"].strip() or not new_data["position"].strip():
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "ФИО и должность обязательны!")
            return

        self.db.update(
            worker_id=worker_id,
            fio=new_data["fio"],
            position=new_data["position"],
            contacts=new_data["contacts"],
            schedule=new_data["schedule"] or "Пн-Пт 9:00-18:00"
        )

        self.load_workers()
        QtWidgets.QMessageBox.information(self.window, "Успех", "Данные сотрудника обновлены!")

    # =================== Удаление сотрудника ===================
    def remove_worker(self):
        # Получаем все выделенные строки (даже если выделены не все ячейки в строке)
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)

        if not selected_rows:
            QtWidgets.QMessageBox.warning(self.window, "Удаление", "Выберите хотя бы одного сотрудника для удаления")
            return

        count = len(selected_rows)

        if count == 1:
            message = "Удалить выбранного сотрудника навсегда?"
        else:
            message = f"Удалить {count} сотрудников навсегда?\n\nЭто действие нельзя отменить!"

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
            id_item = self.table.item(row, 4)
            if id_item:
                worker_id = int(id_item.text())
                try:
                    self.db.delete(worker_id)
                    deleted_count += 1
                except Exception as e:
                    QtWidgets.QMessageBox.warning(f"Ошибка при удалении ID {worker_id}: {e}")


        self.load_workers()

        # Красивое сообщение об успехе
        if deleted_count == count:
            QtWidgets.QMessageBox.information(
                self.window,
                "Успешно удалено",
                f"Удалено сотрудников: {deleted_count}"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Частичное удаление",
                f"Удалено: {deleted_count} из {count}\n"
                "Некоторые записи не удалось удалить."
            )

    # =================== Поиск ===================
    def search_workers(self):
        search_fio = self.window.lineEdit_FIOWorker.text().strip().lower()
        search_position = self.window.lineEdit_Worker.text().strip()
        search_contacts = self.window.lineEdit_WorkerContact.text().strip()

        all_workers = self.db.get_all()

        results = []
        for worker in all_workers:
            fio_match = not search_fio or search_fio in worker.fio.lower()
            pos_match = not search_position or search_position.lower() in worker.position.lower()
            cont_match = not search_contacts or search_contacts in (worker.contacts or "").lower()

            if fio_match and pos_match and cont_match:
                results.append(worker)

        self.table.setRowCount(0)
        for worker in results:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(worker.fio))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(worker.contacts or "—"))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(worker.schedule))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(worker.position))

            id_item = QtWidgets.QTableWidgetItem(str(worker.id))
            id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 4, id_item)

        self.window.statusbar.showMessage(f"Найдено сотрудников: {len(results)}", 3000)

    # =================== Загрузка всех ===================
    def load_workers(self):
        """Загружает всех сотрудников из БД"""
        self.table.setRowCount(0)
        workers = self.db.get_all()

        for worker in workers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(worker.fio))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(worker.contacts or "—"))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(worker.schedule))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(worker.position))

            id_item = QtWidgets.QTableWidgetItem(str(worker.id))
            id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 4, id_item)

        self.window.statusbar.showMessage(f"Загружено сотрудников: {len(workers)}", 2000)