from PyQt5 import QtCore
import xml.etree.ElementTree as ET
import time
import os
class LoadDataThread(QtCore.QThread):
    """
    Асинхронно загружает XML-файл и передаёт корневой элемент в основной поток.

    Используется для предотвращения зависания GUI при чтении больших XML-файлов.

    Signals:
        finished(object): Эмитируется после завершения.
            - ``xml.etree.ElementTree.Element`` — корень XML при успехе.
            - ``None`` — при ошибке парсинга.

    """
    finished = QtCore.pyqtSignal(object)  # xml_root: Element | None

    def __init__(self, path: str):
        """
        Инициализирует поток загрузки XML.

        Args:
            path (str): Путь к XML-файлу для загрузки.
        """
        super().__init__()
        self.path = path

    def run(self):
        """
        Выполняет загрузку и парсинг XML-файла в отдельном потоке.

        Примечание:
            Добавлена искусственная задержка (1 сек) для имитации долгой загрузки.
            В реальном приложении её можно убрать.
        """
        time.sleep(1)
        try:
            tree = ET.parse(self.path)
            root = tree.getroot()
            self.finished.emit(root)
        except Exception as e:
            self.finished.emit(None)


class EditDataThread(QtCore.QThread):
    """
    Асинхронно обновляет статус всех клиентов в XML-файле на ``checked``.

    Редактирует **исходный файл на месте**, не создавая копий.

    Signals:
        finished(str): Путь к обновлённому файлу или пустая строка при ошибке.

    """
    finished = QtCore.pyqtSignal(str)

    def __init__(self, xml_root, file_path: str):
        """
        Инициализирует поток редактирования.

        Args:
            xml_root (xml.etree.ElementTree.Element): Корневой элемент XML.
            file_path (str): Путь к файлу для сохранения изменений.
        """
        super().__init__()
        self.xml_root = xml_root
        self.file_path = file_path

    def run(self):
        """
        Обновляет атрибут ``status="checked"`` у всех ``<client>`` и сохраняет файл.

        Логирует каждое изменение в консоль.
        """
        if self.xml_root is None:
            self.finished.emit("")
            return
        for client in self.xml_root.findall(".//client"):
            if client.get("status") != "checked":
                client.set("status", "checked")

        try:
            tree = ET.ElementTree(self.xml_root)
            tree.write(
                self.file_path,
                encoding="utf-8",
                xml_declaration=True
            )
            self.finished.emit(self.file_path)
        except Exception as e:
            self.finished.emit("")


class HTMLReportThread(QtCore.QThread):
    """
    Асинхронно генерирует красивый HTML-отчёт на основе XML-файла.

    Создаёт адаптивную таблицу с данными клиентов и статусом заезда.

    Signals:
        finished(str): Путь к созданному HTML-файлу или пустая строка при ошибке.

    """
    finished = QtCore.pyqtSignal(str)

    def __init__(self, xml_path: str):
        """
        Инициализирует поток генерации отчёта.

        Args:
            xml_path (str): Путь к XML-файлу с данными.
        """
        super().__init__()
        self.xml_path = xml_path

    def run(self):
        """
        Читает XML, формирует HTML-страницу и сохраняет как ``report_beautiful.html``.

        Использует встроенные CSS-стили для красивого оформления.
        """
        if not self.xml_path or not os.path.exists(self.xml_path):
            self.finished.emit("")
            return

        time.sleep(1)  # Имитация долгой обработки

        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()

            # Собираем данные
            clients = []
            for client in root.findall(".//client"):
                fio = client.findtext("fio", "—")
                room = client.findtext("room_type", client.findtext("room", "—"))
                start = client.findtext("date_start", "—")
                end = client.findtext("date_end", "—")
                status = client.get("status", "pending")
                status_text = "Заезд подтверждён" if status == "checked" else "Ожидает"
                clients.append((fio, room, start, end, status_text))

            # Генерируем HTML
            html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Отчёт по клиентам гостиницы</title>
    <style>
        body {{font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f9f9fb; color: #2c3e50;}}
        h1 {{text-align: center; color: #0078d7; border-bottom: 3px solid #0078d7; padding-bottom: 10px;}}
        table {{width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 14pt; box-shadow: 0 0 20px rgba(0,0,0,0.1);}}
        th {{background-color: #0078d7; color: white; padding: 12px 15px; text-align: center; font-weight: bold;}}
        td {{padding: 10px 15px; text-align: center; border-bottom: 1px solid #ddd;}}
        tr:nth-child(even) {{background-color: #f8f9fa;}}
        tr:hover {{background-color: #e3f2fd;}}
        .footer {{text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 12pt;}}
        @media (max-width: 768px) {{table, th, td {{font-size: 12pt;}}}}
    </style>
</head>
<body>
    <h1>Отчёт по клиентам гостиницы</h1>
    <p style="text-align:center;"><strong>Обработано:</strong> {len(clients)} записей</p>

    <table>
        <tr>
            <th>ФИО</th>
            <th>Номер комнаты</th>
            <th>Дата заезда</th>
            <th>Дата выезда</th>
            <th>Статус</th>
        </tr>"""

            for fio, room, start, end, status in clients:
                status_icon = "Заезд подтверждён" if "подтверждён" in status else "Ожидание"
                html += f"""
        <tr>
            <td>{fio}</td>
            <td>{room}</td>
            <td>{start}</td>
            <td>{end}</td>
            <td><strong>{status_icon}</strong></td>
        </tr>"""

            html += f"""
    </table>

    <div class="footer">
        Отчёт сформирован: {time.strftime("%d.%m.%Y %H:%M")}
        <br>Панель администратора гостиницы © 2025
    </div>
</body>
</html>"""

            # Сохраняем
            html_path = "report_beautiful.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self.finished.emit(html_path)

        except Exception as e:
            print("Ошибка при создании HTML:", e)
            self.finished.emit("")