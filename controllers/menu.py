from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal


class MenuSignals(QObject):
    csv_imported_clients = pyqtSignal()
    csv_imported_rooms = pyqtSignal()
    csv_imported_workers = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

class MenuController:
    """
    Отвечает только за:
    - Меню "Файл" (открыть/сохранить CSV и XML)
    - Меню "Вид" (полноэкранный режим)
    - Меню "Справка" (Помощь, контакты)
    """
    def __init__(self, window, csv_service, export, db_client, db_room, db_worker):
        self.window = window
        self.csv = csv_service
        self.export = export
        self.db_client = db_client
        self.db_room = db_room
        self.db_worker = db_worker
        self.signals = MenuSignals()
        self._connect_signals()

    def _connect_signals(self):
        # Меню Файл
        self.window.open_action.triggered.connect(self.open_csv)
        self.window.save_action.triggered.connect(self.save_csv)
        self.window.exit_action.triggered.connect(self.window.close)
        self.window.export_PDF_action.triggered.connect(self.export_pdf)
        self.window.export_HTML_action.triggered.connect(self.export_html)

        # Меню Вид
        self.window.fullscreen_action.triggered.connect(self.toggle_fullscreen)

        # Справка
        self.window.about_action.triggered.connect(self.show_help)

    def _get_current_table(self):
        index = self.window.tabWidget.currentIndex()
        if index == 0:
            return self.window.tableWidgetClients
        elif index == 1:
            return self.window.tableWidget_Rooms
        elif index == 2:
            return self.window.tableWidget_Workers
        elif index == 3:
            return self.window.tableView_Report
        return None

    # =================== Файл ===================
    def open_csv(self):
        index = self.window.tabWidget.currentIndex()
        if index not in (0, 1, 2):
            QtWidgets.QMessageBox.warning(
                self.window,
                "Внимание",
                "Импорт CSV доступен только на вкладках: Клиенты, Номера, Сотрудники"
            )
            return

        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window, "Открыть CSV", "", "CSV файлы (*.csv)"
        )
        if not path:
            return

        try:
            if index == 0:
                result = self.db_client.import_from_csv(path)
                self.signals.csv_imported_clients.emit()
            elif index == 1:
                result = self.db_room.import_from_csv(path)
                self.signals.csv_imported_rooms.emit()
            elif index == 2:
                result = self.db_worker.import_from_csv(path)
                self.signals.csv_imported_workers.emit()

            # Показ сообщения
            msg = f"Импорт завершён!\nДобавлено: {result.get('added', 0)}"
            if result.get('errors'):
                msg += f"\nОшибок: {len(result['errors'])}\n" + "\n".join(result['errors'][:10])
            QtWidgets.QMessageBox.information(self.window, "Импорт CSV", msg)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Ошибка импорта", str(e))

    def save_csv(self):
        table = self._get_current_table()
        if not table:
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Нет активной таблицы для сохранения")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window, "Сохранить CSV", "data.csv", "CSV файлы (*.csv)"
        )
        if not path:
            return

        try:
            self.csv.save_table_to_csv(table, path)
            QtWidgets.QMessageBox.information(self.window, "Успех", "Данные сохранены в CSV")
        except Exception:
            QtWidgets.QMessageBox.warning(self.window, "Ошибка", "Невозможно сохранить файл")

    # =================== Экспорт ===================
    def export_pdf(self):
        table = self._get_current_table()
        current_index = self.window.tabWidget.currentIndex()

        # Проверка для вкладки "Отчёт"
        if current_index == 3:
            model = table.model()
            if model is None or model.rowCount() == 0:
                QtWidgets.QMessageBox.warning(
                    self.window,
                    "Отчёт пуст",
                    "Сначала создайте отчёт, выбрав месяц и нажав «Создать отчёт»."
                )
                return
        else:
            # Проверка наличия таблицы для остальных вкладок
            if not table or table.rowCount() == 0:
                QtWidgets.QMessageBox.warning(
                    self.window,
                    "Нет данных",
                    "Нет активной таблицы для экспорта. Перейдите на нужную вкладку."
                )
                return

        # Диалог выбора пути
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Сохранить отчёт как PDF",
            "Отчёт.pdf",
            "PDF файлы (*.pdf)"
        )
        if not path:
            return  # Пользователь отменил

        # Экспорт
        if current_index == 3:
            month_name = self.window.comboBox_MonthYear.currentText()
            success = self.export.export_tableview_to_pdf(table, path, month_name)
        else:
            tab_name = self.window.tabWidget.tabText(current_index)
            if tab_name.lower().startswith("клиент"):
                title = "Справка о жильцах гостиницы"
            elif tab_name.lower().startswith("номер"):
                title = "Список номеров гостиницы"
            elif tab_name.lower().startswith("персонал"):
                title = "Персонал гостиницы"
            else:
                title = tab_name
            success = self.export.export_table_to_pdf(table, path, title)

        if success:
            QtWidgets.QMessageBox.information(self.window, "Успех", f"PDF сохранён:\n{path}")
        else:
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", "Не удалось сохранить PDF")

    def export_html(self):
        table = self._get_current_table()
        current_index = self.window.tabWidget.currentIndex()

        # Проверка наличия таблицы
        if not table:
            QtWidgets.QMessageBox.warning(
                self.window,
                "Нет данных",
                "Нет активной таблицы для экспорта. Перейдите на нужную вкладку."
            )
            return

        # Дополнительная проверка для вкладки "Отчёт"
        if current_index == 3:
            model = table.model()
            if model is None or model.rowCount() == 0:
                QtWidgets.QMessageBox.warning(
                    self.window,
                    "Отчёт пуст",
                    "Сначала создайте отчёт, выбрав месяц и нажав «Сформировать отчёт»."
                )
                return

        # Диалог выбора пути
        default_name = "Отчёт.html"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Сохранить отчёт как HTML",
            default_name,
            "HTML файлы (*.html)"
        )
        if not path:
            return  # Пользователь отменил

        # Экспорт
        if current_index == 3:
            month_name = self.window.comboBox_MonthYear.currentText()
            success = self.export.export_tableview_to_html(table, path, month_name)
        else:
            success = self.export.export_table_to_html(table, path)

        if success:
            QtWidgets.QMessageBox.information(
                self.window,
                "Успех",
                f"HTML-отчёт сохранён!\n\n{path}\n\n"
            )
        else:
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", "Не удалось сохранить HTML")

    # =================== Вид ===================
    def toggle_fullscreen(self):
        if self.window.isFullScreen():
            self.window.showNormal()
        else:
            self.window.showFullScreen()

    # =================== Справка ===================
    def show_help(self):
        # Временно закомментируйте создание HelpWindow
        # HELP_TEXT = "..."
        # win = HelpWindow(self.window, HELP_TEXT)
        # win.exec_()

        # Простое сообщение для теста
        QtWidgets.QMessageBox.information(
            self.window,
            "Справка",
            "Тест: окно справки работает"
        )
