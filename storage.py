import csv
from PyQt5 import QtCore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class FileCSVService:
    """Загрузка и сохранение CSV."""

    def save_table_to_csv(self, table, filepath=None, delimiter=";"):
        """
        Универсальное сохранение любой таблицы в CSV
        Сохраняет ВСЁ как есть: статусы, даты, цвета (только текст)
        """
        try:
            if filepath is None:
                return False

            row_count = table.rowCount()
            col_count = table.columnCount()

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=delimiter)

                # Заголовки
                headers = []
                for i in range(col_count):
                    header_item = table.horizontalHeaderItem(i)
                    if header_item:
                        headers.append(header_item.text())
                    else:
                        headers.append(f"Колонка {i + 1}")
                writer.writerow(headers)

                # Строки данных
                for row in range(row_count):
                    row_data = []
                    for col in range(col_count):
                        item = table.item(row, col)
                        if item and item.text():
                            row_data.append(item.text().strip())
                        else:
                            row_data.append("")
                    writer.writerow(row_data)

            return True

        except Exception as e:
            print(f"Ошибка сохранения CSV: {e}")
            return False




class FileExportService:
    """PDF + HTML экспорт."""

    def export_table_to_html(self, table, path):
        try:
            html = "<html><head><meta charset='utf-8'></head><body>"
            html += "<table border='1' cellspacing='0' cellpadding='4'>"

            # --------- Заголовок ---------
            html += "<tr>"
            for c in range(table.columnCount()):
                if table.isColumnHidden(c):
                    continue

                header_item = table.horizontalHeaderItem(c)
                header_text = header_item.text() if header_item else f"Column {c}"

                html += f"<th>{header_text}</th>"
            html += "</tr>"

            # --------- Строки ---------
            for r in range(table.rowCount()):
                html += "<tr>"
                for c in range(table.columnCount()):
                    if table.isColumnHidden(c):
                        continue

                    item = table.item(r, c)
                    cell_text = item.text() if item else ""
                    html += f"<td>{cell_text}</td>"
                html += "</tr>"

            html += "</table></body></html>"

            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

            return True

        except Exception as e:
            print("Ошибка HTML:", e)
            return False

    def export_table_to_pdf(self, table, path, title):
        try:
            # Регистрируем шрифт с поддержкой кириллицы
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))

            doc = SimpleDocTemplate(path, pagesize=A4, topMargin=40, bottomMargin=40)
            elements = []

            # Стили
            styles = getSampleStyleSheet()
            if 'MyPDFTitle' not in styles:
                styles.add(ParagraphStyle(
                    name='MyPDFTitle',
                    fontName='Arial-Bold',
                    fontSize=18,
                    alignment=1,  # центр
                    spaceAfter=20
                ))

            elements.append(Paragraph(title, styles['MyPDFTitle']))
            elements.append(Spacer(1, 12))

            # Собираем данные
            data = []
            headers = []
            visible_columns = []

            for c in range(table.columnCount()):
                if table.isColumnHidden(c):
                    continue
                visible_columns.append(c)
                header_item = table.horizontalHeaderItem(c)
                header_text = header_item.text() if header_item else f"Колонка {c}"
                headers.append(Paragraph(header_text, ParagraphStyle(
                    name='Header', fontName='Arial-Bold', fontSize=10
                )))
            data.append(headers)

            # Строки с переносом текста
            for r in range(table.rowCount()):
                row = []
                for c in visible_columns:
                    item = table.item(r, c)
                    text = item.text() if item else ""
                    para = Paragraph(text, ParagraphStyle(
                        name='Cell',
                        fontName='Arial',
                        fontSize=9,
                        leading=11,
                        alignment=0,
                        wordWrap='CJK'
                    ))
                    row.append(para)
                data.append(row)

            col_count = len(visible_columns)
            page_width = doc.width - 40
            base_width = page_width / col_count
            col_widths = [base_width * 1.8 if i == 0 else base_width * 0.9 for i in range(col_count)]

            # Создаём таблицуяя
            pdf_table = Table(data, colWidths=col_widths, repeatRows=1)
            pdf_table.hAlign = 'CENTER'

            table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEADING', (0, 0), (-1, -1), 11),

                # Заголовки
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dddddd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),

                # Сетка
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),

                # Зебра
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f3f5')]),

                # Выравнивание и перенос
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # ФИО — по левому краю
            ])

            pdf_table.setStyle(table_style)
            elements.append(pdf_table)

            doc.build(elements)
            return True

        except Exception as e:
            print(f"Ошибка экспорта PDF: {e}")
            return False

    def export_tableview_to_pdf(self, tableview, path, title=""):
        try:
            model = tableview.model()
            if model is None or model.rowCount() == 0:
                return False

            # Подключаем шрифт
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))

            doc = SimpleDocTemplate(
                path,
                pagesize=A4,
                topMargin=40, bottomMargin=40,
                leftMargin=25, rightMargin=25
            )

            styles = getSampleStyleSheet()

            # ---------- Стили ----------
            if "MainTitle" not in styles:
                styles.add(ParagraphStyle(
                    name="MainTitle",
                    fontName="Arial",
                    fontSize=20,
                    alignment=1,  # центр
                    textColor=colors.black,
                    spaceAfter=20
                ))

            if "SubTitle" not in styles:
                styles.add(ParagraphStyle(
                    name="SubTitle",
                    fontName="Arial",
                    fontSize=14,
                    alignment=1,
                    spaceAfter=25
                ))

            if "TableText" not in styles:
                styles.add(ParagraphStyle(
                    name="TableText",
                    fontName="Arial",
                    fontSize=10,
                    alignment=1
                ))

            elements = []

            # ======== ОГЛАВЛЕНИЕ ========
            elements.append(Paragraph("Отчёт по загрузке номеров гостиницы", styles["MainTitle"]))

            if title:
                elements.append(Paragraph(title, styles["SubTitle"]))

            # ------------------------------------
            #            ДАННЫЕ ТАБЛИЦЫ
            # ------------------------------------
            data = []

            # Заголовки
            headers = []
            for col in range(model.columnCount()):
                header = model.headerData(col, QtCore.Qt.Horizontal)
                header_para = Paragraph(f"<b>{header}</b>", ParagraphStyle(
                    name='HeaderCell',
                    parent=styles["TableText"],
                    alignment=1
                ))
                headers.append(header_para)
            data.append(headers)

            # Строки
            for row in range(model.rowCount() - 1):  # последняя — итог
                row_items = []
                for col in range(model.columnCount()):
                    item = model.item(row, col)
                    text = item.text() if item else ""
                    para_style = ParagraphStyle(
                        name='CellText',
                        parent=styles["TableText"],
                        alignment=0,
                        leading=12
                    )
                    row_items.append(Paragraph(text, para_style))
                data.append(row_items)

            # Итоговая строка
            summary_item = model.item(model.rowCount() - 1, 0)
            summary_text = summary_item.text() if summary_item else "ИТОГО"

            col_count = model.columnCount()
            data.append(
                [Paragraph(f"<b>{summary_text}</b>", styles["TableText"])] +
                [""] * (col_count - 1)
            )

            # Таблица
            base_width = doc.width / (col_count + 1)

            col_widths = []
            for i in range(col_count):
                if i == 1:
                    col_widths.append(base_width * 2)
                else:
                    col_widths.append(base_width)

            table = Table(data, colWidths=col_widths, repeatRows=1)

            style = TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Arial"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),

                # Заголовок — жирный, чёрный текст, серая заливка
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Arial"),

                # Все ячейки по центру
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                # Тонкая сетка
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

                # Жирный шрифт для итоговой строки
                ("FONTNAME", (0, -1), (-1, -1), "Arial"),
                ("FONTSIZE", (0, -1), (-1, -1), 11),
            ])

            for i in range(1, len(data) - 1):
                if i % 2 == 1:
                    style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f9f9f9"))

            last_row = len(data) - 1
            style.add("SPAN", (0, last_row), (col_count - 1, last_row))
            style.add("BACKGROUND", (0, last_row), (col_count - 1, last_row), colors.HexColor("#cccccc"))
            style.add("TEXTCOLOR", (0, last_row), (col_count - 1, last_row), colors.black)

            table.setStyle(style)

            elements.append(table)
            doc.build(elements)

            return True

        except Exception as e:
            return False

    def export_tableview_to_html(self, tableview, path, title=""):
        """
        Красивый экспорт QTableView → HTML
        + Оглавление (заголовок)
        """
        try:
            model = tableview.model()
            if model is None or model.rowCount() == 0:
                return False

            visible_columns = [c for c in range(model.columnCount())
                               if not tableview.isColumnHidden(c)]

            col_count = len(visible_columns)
            col_width = 100 / col_count

            # HTML
            html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                    }}
                    .title {{
                        text-align: center;
                        font-size: 22px;
                        font-weight: bold;
                        margin-bottom: 20px;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    th {{
                        background: #0078d7;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                        text-align: center;
                    }}
                    td {{
                        padding: 8px;
                        text-align: center;
                        border: 1px solid #444;
                    }}
                    .summary {{
                        background: #0078d7;
                        color: white;
                        font-weight: bold;
                        text-align: center;
                        padding: 10px;
                    }}
                </style>
            </head>
            <body>

            <div class="title">Отчёт по загрузке за {title}</div>

            <table>
            """

            # -------- заголовки --------
            html += "<tr>"
            for col in visible_columns:
                header = model.headerData(col, QtCore.Qt.Horizontal)
                html += f"<th style='width:{col_width}%'>{header}</th>"
            html += "</tr>"

            # -------- строки данных --------
            for row in range(model.rowCount() - 1):
                html += "<tr>"
                for col in visible_columns:
                    item = model.item(row, col)
                    text = item.text() if item else ""
                    html += f"<td>{text}</td>"
                html += "</tr>"

            # -------- итоговая строка --------
            summary_item = model.item(model.rowCount() - 1, 0)
            summary_text = summary_item.text() if summary_item else "ИТОГО"

            html += f"""
            <tr>
                <td colspan="{col_count}" class="summary">{summary_text}</td>
            </tr>
            """

            html += "</table></body></html>"

            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

            return True

        except Exception as e:
            print("HTML ERROR:", e)
            return False


