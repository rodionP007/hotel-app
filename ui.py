
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QHeaderView


class UI_Hotel_App():
    """
    Класс для создания и настройки главного окна приложения
    "Панель администратора гостиницы".
    """
    def setupUi(self, Hotel_App):
        self.window = Hotel_App
        Hotel_App.setObjectName("Hotel_App")
        Hotel_App.resize(1200, 800)
        Hotel_App.setStyleSheet("""
        QWidget {
            background-color: #f8f9fa;
            color: #2c3e50;
            font-family: "Segoe UI";
            font-size: 11pt;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            border-radius: 6px;
            padding: 8px 14px;
        }
        QPushButton:hover {
            background-color: #005fa3;
        }
        QLineEdit, QComboBox, QDateEdit {
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 4px;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f2f2f2;
            gridline-color: #dee2e6;
        }
        QHeaderView::section {
            background-color: #e9ecef;
            padding: 6px;
            border: none;
            font-weight: bold;
        }
        QTabBar::tab {
            background: #e9ecef;
            border-radius: 6px;
            padding: 6px 12px;
            margin: 2px;
        }
        QTabBar::tab:selected {
            background: #0078d7;
            color: white;
        }
        """)

        # ---------- central widget and main layout ----------
        self.centralwidget = QtWidgets.QWidget(Hotel_App)
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(12)

        # ---------- Header ----------
        self.label = QtWidgets.QLabel("Панель администратора", self.centralwidget)
        font = QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFixedHeight(56)
        self.label.setStyleSheet("""
            background-color: #0078d7;
            color: white;
            font-size: 18pt;
            font-weight: bold;
            padding: 10px;
            border-radius: 8px;
        """)
        self.mainLayout.addWidget(self.label)

        # ---------- TabWidget ----------
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.tabWidget)

        # ----------------- Вкладка: Клиенты -----------------
        self._setup_clients_tab()

        # ----------------- Вкладка: Номера -----------------
        self._setup_rooms_tab()

        # ----------------- Вкладка: Персонал -----------------
        self._setup_workers_tab()

        # ----------------- Вкладка: Отчёты -----------------
        self._setup_reports_tab()

        # Устанавливаем central widget
        Hotel_App.setCentralWidget(self.centralwidget)

        # Меню (с полноэкранным переключателем)
        self._setup_menus(Hotel_App)

        # Статус бар
        self.statusbar = QtWidgets.QStatusBar(Hotel_App)
        Hotel_App.setStatusBar(self.statusbar)

        self.retranslate(Hotel_App)
        QtCore.QMetaObject.connectSlotsByName(Hotel_App)

        self.deleted_clients = []


    # ------------------ setup tab builders ------------------
    def _setup_clients_tab(self):
        self.tab = QtWidgets.QWidget()
        self.tabClientsLayout = QtWidgets.QVBoxLayout(self.tab)
        self.tabClientsLayout.setContentsMargins(6, 6, 6, 6)
        self.tabClientsLayout.setSpacing(8)

        # форма сверху
        formFrame = QtWidgets.QWidget(self.tab)
        formLayout = QtWidgets.QFormLayout(formFrame)
        formLayout.setContentsMargins(0, 0, 0, 0)
        formLayout.setSpacing(8)

        self.FIO_Client = QtWidgets.QLabel(formFrame)
        font = QtGui.QFont("Segoe UI", 12)
        self.FIO_Client.setFont(font)
        formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.FIO_Client)

        self.lineFIO_clientEdit = QtWidgets.QLineEdit(formFrame)
        formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineFIO_clientEdit)

        # === Номер комнаты — теперь ComboBox! ===
        self.label_RoomNumber = QtWidgets.QLabel("Комната", formFrame)
        self.label_RoomNumber.setFont(font)
        formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_RoomNumber)

        self.comboRoomSearch = QtWidgets.QComboBox(formFrame)
        self.comboRoomSearch.setMinimumWidth(300)
        self.comboRoomSearch.setFont(font)
        self.comboRoomSearch.addItem("Все номера", None)  # ← это будет "любой номер"
        formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.comboRoomSearch)

        self.tabClientsLayout.addWidget(formFrame)

        # таблица клиентов
        self.tableWidgetClients = QtWidgets.QTableWidget(self.tab)

        self.tableWidgetClients.setColumnCount(5)
        self.tableWidgetClients.setHorizontalHeaderLabels(["ФИО", "Номер комнаты", "Заезд", "Выезд", "ID"])
        self.tableWidgetClients.setColumnHidden(4, True)  # скрываем ID
        self.tableWidgetClients.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.tableWidgetClients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidgetClients.setAlternatingRowColors(True)
        self.tableWidgetClients.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tabClientsLayout.addWidget(self.tableWidgetClients)

        # нижняя панель кнопок
        bottomWidget = QtWidgets.QWidget(self.tab)
        bottomLayout = QtWidgets.QHBoxLayout(bottomWidget)
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButtonAddClients = QtWidgets.QPushButton("Добавить", bottomWidget)
        self.pushButtonEditClients = QtWidgets.QPushButton("Изменить", bottomWidget)
        self.pushButtonRemoveClients = QtWidgets.QPushButton("Удалить", bottomWidget)
        bottomLayout.addWidget(self.pushButtonAddClients, 1)
        bottomLayout.addWidget(self.pushButtonEditClients, 1)
        bottomLayout.addWidget(self.pushButtonRemoveClients, 1)
        self.tabClientsLayout.addWidget(bottomWidget)
        # добавить вкладку
        self.tabWidget.addTab(self.tab, "")
    def _setup_rooms_tab(self):
        self.tab_2 = QtWidgets.QWidget()
        self.tabRoomsLayout = QtWidgets.QVBoxLayout(self.tab_2)
        self.tabRoomsLayout.setContentsMargins(6, 6, 6, 6)
        self.tabRoomsLayout.setSpacing(8)

        # форма поиска — с понятными метками
        formFrame2 = QtWidgets.QWidget(self.tab_2)
        formLayout2 = QtWidgets.QFormLayout(formFrame2)
        formLayout2.setContentsMargins(0, 0, 0, 0)
        formLayout2.setSpacing(8)

        # Метка и комбобокс для поиска по вместимости
        self.labelCapacityRooms = QtWidgets.QLabel("Вместимость", formFrame2)
        font = QtGui.QFont("Segoe UI", 12)
        self.labelCapacityRooms.setFont(font)
        formLayout2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.labelCapacityRooms)

        self.comboBoxCapacityRooms = QtWidgets.QComboBox(formFrame2)

        self.comboBoxCapacityRooms.addItems(["Все", "1", "2", "3", "4", "5+"])
        self.comboBoxCapacityRooms.setToolTip("Выберите вместимость для фильтрации")
        formLayout2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comboBoxCapacityRooms)

        # Метка и поле для поиска по типу номера
        self.labelRoomType = QtWidgets.QLabel("Тип номера ", formFrame2)
        self.labelRoomType.setFont(font)
        formLayout2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.labelRoomType)

        self.comboBoxRoomType = QtWidgets.QComboBox(formFrame2)
        self.comboBoxRoomType.addItems(["Все", "Люкс", "Эконом", "Премиум-люкс", "Президентский"])
        self.comboBoxRoomType.setToolTip("Выберите тип номера для фильтрации")
        formLayout2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.comboBoxRoomType)

        # Метка и комбобокс для статуса
        self.label_StatusRooms = QtWidgets.QLabel("Искать по статусу", formFrame2)
        self.label_StatusRooms.setFont(font)
        formLayout2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_StatusRooms)

        self.comboBox_StatusRooms = QtWidgets.QComboBox(formFrame2)
        self.comboBox_StatusRooms.addItems(["Все", "Свободен", "Занят"])
        self.comboBox_StatusRooms.setToolTip("Фильтр по статусу номера")
        formLayout2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.comboBox_StatusRooms)

        self.tabRoomsLayout.addWidget(formFrame2)

        # таблица номеров
        self.tableWidget_Rooms = QtWidgets.QTableWidget(self.tab_2)
        self.tableWidget_Rooms.setColumnCount(6)
        self.tableWidget_Rooms.setHorizontalHeaderLabels(["№", "Тип", "Вместимость", "Цена за день", "Статус", "ID"])
        self.tableWidget_Rooms.setColumnHidden(5, True)
        self.tableWidget_Rooms.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_Rooms.setAlternatingRowColors(True)
        self.tableWidget_Rooms.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tabRoomsLayout.addWidget(self.tableWidget_Rooms)

        # нижняя панель кнопок
        bottomWidget2 = QtWidgets.QWidget(self.tab_2)
        bottomLayout2 = QtWidgets.QHBoxLayout(bottomWidget2)
        bottomLayout2.setContentsMargins(0, 0, 0, 0)
        self.pushButtonAddRooms = QtWidgets.QPushButton("Добавить", bottomWidget2)
        self.pushButtonEditRooms = QtWidgets.QPushButton("Изменить", bottomWidget2)
        self.pushButtonRemoveRooms = QtWidgets.QPushButton("Удалить", bottomWidget2)
        bottomLayout2.addWidget(self.pushButtonAddRooms, 1)
        bottomLayout2.addWidget(self.pushButtonEditRooms, 1)
        bottomLayout2.addWidget(self.pushButtonRemoveRooms, 1)
        self.tabRoomsLayout.addWidget(bottomWidget2)

        self.tabWidget.addTab(self.tab_2, "")

    def _setup_workers_tab(self):
        self.tab_3 = QtWidgets.QWidget()
        self.tabWorkersLayout = QtWidgets.QVBoxLayout(self.tab_3)
        self.tabWorkersLayout.setContentsMargins(6, 6, 6, 6)
        self.tabWorkersLayout.setSpacing(8)

        # форма поиска сотрудников с понятными метками
        formFrame3 = QtWidgets.QWidget(self.tab_3)
        formLayout3 = QtWidgets.QFormLayout(formFrame3)
        formLayout3.setContentsMargins(0, 0, 0, 0)
        formLayout3.setSpacing(8)

        self.label_FIOWorker = QtWidgets.QLabel("Искать по ФИО сотрудника", formFrame3)
        font = QtGui.QFont("Segoe UI", 12)
        self.label_FIOWorker.setFont(font)
        formLayout3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_FIOWorker)

        self.lineEdit_FIOWorker = QtWidgets.QLineEdit(formFrame3)
        self.lineEdit_FIOWorker.setPlaceholderText("Фамилия Имя (или часть ФИО)")
        formLayout3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_FIOWorker)

        self.label_Worker = QtWidgets.QLabel("Искать по должности", formFrame3)
        self.label_Worker.setFont(font)
        formLayout3.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_Worker)

        self.lineEdit_Worker = QtWidgets.QLineEdit(formFrame3)
        self.lineEdit_Worker.setPlaceholderText("Должность (например: Администратор)")
        formLayout3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_Worker)

        # Доп. поле: контакт
        self.label_WorkerContact = QtWidgets.QLabel("Контакт (телефон)", formFrame3)
        self.label_WorkerContact.setFont(font)
        formLayout3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_WorkerContact)

        self.lineEdit_WorkerContact = QtWidgets.QLineEdit(formFrame3)
        self.lineEdit_WorkerContact.setPlaceholderText("Телефон")
        formLayout3.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lineEdit_WorkerContact)

        self.tabWorkersLayout.addWidget(formFrame3)

        # таблица работников
        self.tableWidget_Workers = QtWidgets.QTableWidget(self.tab_3)
        self.tableWidget_Workers.setColumnCount(4)
        self.tableWidget_Workers.setHorizontalHeaderLabels(["ФИО", "Контакты", "График", "Должность"])
        self.tableWidget_Workers.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_Workers.setAlternatingRowColors(True)
        self.tableWidget_Workers.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.tabWorkersLayout.addWidget(self.tableWidget_Workers)

        # кнопки
        bottomWidget3 = QtWidgets.QWidget(self.tab_3)
        bottomLayout3 = QtWidgets.QHBoxLayout(bottomWidget3)
        bottomLayout3.setContentsMargins(0, 0, 0, 0)
        self.pushButtonAddPersonal = QtWidgets.QPushButton("Добавить", bottomWidget3)
        self.pushButtonEditPersonal = QtWidgets.QPushButton("Изменить", bottomWidget3)
        self.pushButtonRemovePersonal = QtWidgets.QPushButton("Удалить", bottomWidget3)
        bottomLayout3.addWidget(self.pushButtonAddPersonal, 1)
        bottomLayout3.addWidget(self.pushButtonEditPersonal, 1)
        bottomLayout3.addWidget(self.pushButtonRemovePersonal, 1)
        self.tabWorkersLayout.addWidget(bottomWidget3)

        # сигнал поиска

        self.tabWidget.addTab(self.tab_3, "")

    def _setup_reports_tab(self):
        self.tab_4 = QtWidgets.QWidget()
        self.tabReportsLayout = QtWidgets.QVBoxLayout(self.tab_4)
        self.tabReportsLayout.setContentsMargins(10, 10, 10, 10)
        self.tabReportsLayout.setSpacing(12)

        # === Группа "Отчёт за месяц" с ComboBox ===
        self.groupBox_Report = QtWidgets.QGroupBox("Отчёт за месяц", self.tab_4)
        self.groupBox_Report.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)

        group_layout = QtWidgets.QHBoxLayout(self.groupBox_Report)
        group_layout.setContentsMargins(15, 15, 15, 15)
        group_layout.setSpacing(15)

        label_month = QtWidgets.QLabel("Выберите месяц:")
        label_month.setFixedWidth(150)

        # Красивый ComboBox с месяцами и годами
        self.comboBox_MonthYear = QtWidgets.QComboBox()
        self.comboBox_MonthYear.setFixedHeight(36)
        self.comboBox_MonthYear.setMinimumWidth(220)
        font_combo = QtGui.QFont("Segoe UI", 10)
        self.comboBox_MonthYear.setFont(font_combo)

        # Заполняем: 3 года назад → 2 года вперёд
        current_date = QtCore.QDate.currentDate()
        current_year = current_date.year()
        current_month = current_date.month()

        months_ru = [
            "Январь", "Февраль", "Март", "Апрель",
            "Май", "Июнь", "Июль", "Август",
            "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]

        selected_index = 0
        for year in range(current_year - 3, current_year + 3):
            for month_idx, month_name in enumerate(months_ru, 1):
                date = QtCore.QDate(year, month_idx, 1)
                display_text = f"{month_name} {year}"
                self.comboBox_MonthYear.addItem(display_text, date)

                # Выбираем текущий месяц по умолчанию
                if year == current_year and month_idx == current_month:
                    selected_index = self.comboBox_MonthYear.count() - 1

        self.comboBox_MonthYear.setCurrentIndex(selected_index)

        # Кнопка формирования отчёта
        self.pushButtonCreateReport = QtWidgets.QPushButton("Сформировать отчёт")
        self.pushButtonCreateReport.setFixedHeight(36)
        self.pushButtonCreateReport.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
        """)

        group_layout.addWidget(label_month)
        group_layout.addWidget(self.comboBox_MonthYear)
        group_layout.addStretch()
        group_layout.addWidget(self.pushButtonCreateReport)

        self.tabReportsLayout.addWidget(self.groupBox_Report)

        # === Таблица отчёта (только просмотр) ===
        self.tableView_Report = QtWidgets.QTableView(self.tab_4)
        self.tableView_Report.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableView_Report.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tableView_Report.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tableView_Report.verticalHeader().setVisible(False)
        self.tableView_Report.horizontalHeader().setStretchLastSection(True)
        self.tableView_Report.setShowGrid(True)
        self.tableView_Report.setAlternatingRowColors(True)
        self.tableView_Report.setStyleSheet("""
            QTableView {
                gridline-color: #d0d0d0;
                background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #0078d7;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        self.tabReportsLayout.addWidget(self.tableView_Report, 1)  # растягивается

        self.tabWidget.addTab(self.tab_4, "Отчёты")
    # ------------------ меню ------------------
    def _setup_menus(self, Hotel_App):
        self.menubar = QtWidgets.QMenuBar(Hotel_App)
        Hotel_App.setMenuBar(self.menubar)

        file_menu = self.menubar.addMenu("Файл")
        view_menu = self.menubar.addMenu("Вид")
        help_menu = self.menubar.addMenu("Справка")

        self.open_action = QtWidgets.QAction("Открыть", Hotel_App)
        self.save_action = QtWidgets.QAction("Сохранить в файл", Hotel_App)
        self.export_PDF_action = QtWidgets.QAction("Экспорт в PDF", Hotel_App)
        self.export_HTML_action = QtWidgets.QAction("Экспорт в HTML", Hotel_App)
        self.exit_action = QtWidgets.QAction("Выход", Hotel_App)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.export_PDF_action)
        file_menu.addAction(self.export_HTML_action)
        file_menu.addAction(self.exit_action)
        # fullscreen toggle
        self.fullscreen_action = QtWidgets.QAction("Полноэкранный режим", Hotel_App)
        self.fullscreen_action.setCheckable(True)
        view_menu.addAction(self.fullscreen_action)

        def toggle_fullscreen(checked):
            if checked:
                Hotel_App.showFullScreen()
            else:
                Hotel_App.showMaximized()


        self.about_action = QtWidgets.QAction("Справка о программе", Hotel_App)
        help_menu.addAction(self.about_action)


    # ------------------ UI texts ------------------
    def retranslate(self, Hotel_App):
        _translate = QtCore.QCoreApplication.translate
        Hotel_App.setWindowTitle(_translate("Hotel_App", "Панель администратора гостиницы"))
        self.FIO_Client.setText(_translate("Hotel_App", "ФИО клиента"))
        self.label_RoomNumber.setText(_translate("Hotel_App", "Комната"))

        # tab titles and headers already set, but set tab texts:
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Hotel_App", "Клиенты"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Hotel_App", "Номера"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("Hotel_App", "Персонал"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("Hotel_App", "Отчёты"))

