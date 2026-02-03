from PyQt5 import QtWidgets

from ui import UI_Hotel_App
from storage import FileCSVService, FileExportService
from controllers.clients import ClientController
from controllers.menu import MenuController
from controllers.rooms import RoomController
from controllers.workers import WorkerController
from controllers.report import ReportController
import sys
from database import UserRepository, ClientRepository, RoomRepository, WorkerRepository
from dialogs import LoginDialog


class HotelApp(QtWidgets.QMainWindow, UI_Hotel_App):
    def __init__(self):
        super().__init__()
        self.room_repo = RoomRepository()
        self.client_repo = ClientRepository(self.room_repo)
        self.worker_repo = WorkerRepository()
        self.setupUi(self)
        self.csv = FileCSVService()
        self.export = FileExportService()
        self.clients_ctrl = ClientController(self, self.tableWidgetClients, self.room_repo, self.client_repo)
        self.room_ctrl = RoomController(self, self.tableWidget_Rooms, self.room_repo)
        self.work_ctrl = WorkerController(self, self.tableWidget_Workers, self.worker_repo)
        self.report_ctrl = ReportController(self, self.client_repo, self.room_repo)
        self.menu_ctrl = MenuController(self, self.csv, self.export, self.client_repo, self.room_repo, self.worker_repo)

        self.clients_ctrl.clients_changed.connect(self.room_ctrl.load_rooms)

        self.menu_ctrl.signals.csv_imported_clients.connect(self.clients_ctrl.load_clients_from_db)
        self.menu_ctrl.signals.csv_imported_rooms.connect(self.room_ctrl.load_rooms)
        self.menu_ctrl.signals.csv_imported_workers.connect(self.work_ctrl.load_workers)
def main():
    app = QtWidgets.QApplication(sys.argv)

    UserRepository()

    # Окно входа
    login_dialog = LoginDialog()
    if login_dialog.exec_() != QtWidgets.QDialog.Accepted:
        sys.exit(0)

    username, password = login_dialog.get_credentials()

    user_repo = UserRepository()
    if not user_repo.check_credentials(username, password):
        QtWidgets.QMessageBox.critical(
            None,
            "Ошибка входа",
            "Неверный логин или пароль!\n\nПодсказка: admin / admin123"
        )
        sys.exit(0)

    # УСПЕШНЫЙ ВХОД
    window = HotelApp()
    window.showMaximized()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
