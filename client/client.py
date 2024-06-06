from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QMessageBox, \
    QTableWidget, QTableWidgetItem
import socket
import json


class InventoryClient(QWidget):


    def __init__(self):
        super().__init__()

        self.initUI()
        self.selected_item_id = None

    def initUI(self):
        self.setWindowTitle('Система Учета Запчастей автомастерской')

        layout = QVBoxLayout()

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["артикул", "Название запчасти", "Количество", "№ Склада", "Производитель"])
        layout.addWidget(self.table)

        self.table.cellClicked.connect(self.select_item)

        self.product_name = QLineEdit(self)
        self.product_name.setPlaceholderText('Название запчасти')
        layout.addWidget(self.product_name)

        self.quantity = QLineEdit(self)
        self.quantity.setPlaceholderText('Количество')
        layout.addWidget(self.quantity)

        self.location = QLineEdit(self)
        self.location.setPlaceholderText('№ Склада')
        layout.addWidget(self.location)

        self.supplier_name = QLineEdit(self)
        self.supplier_name.setPlaceholderText('Производитель')
        layout.addWidget(self.supplier_name)

        self.product_name.textChanged.connect(self.on_text_changed)
        self.quantity.textChanged.connect(self.on_text_changed)
        self.location.textChanged.connect(self.on_text_changed)
        self.supplier_name.textChanged.connect(self.on_text_changed)

        self.save_button = QPushButton('Сохранить изменения', self)
        self.save_button.clicked.connect(self.save_item)
        self.save_button.hide()
        layout.addWidget(self.save_button)

        self.add_button = QPushButton('Добавить Товар', self)
        self.add_button.clicked.connect(self.add_item)
        layout.addWidget(self.add_button)

        self.get_button = QPushButton('Показать Товары', self)
        self.get_button.clicked.connect(self.get_items)
        layout.addWidget(self.get_button)

        self.edit_button = QPushButton('Редактировать Товар', self)
        self.edit_button.clicked.connect(self.edit_item)
        layout.addWidget(self.edit_button)

        self.delete_button = QPushButton('Удалить Товар', self)
        self.delete_button.clicked.connect(self.delete_item)
        layout.addWidget(self.delete_button)

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText('Найти товар по его названию')
        layout.addWidget(self.search_field)

        self.search_button = QPushButton('Поиск', self)
        self.search_button.clicked.connect(self.search_item)
        layout.addWidget(self.search_button)

        self.result_area = QTextEdit(self)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def on_text_changed(self):
        if self.selected_item_id is not None:
            self.save_button.show()

    def select_item(self, row, column):
        self.selected_item_id = self.table.item(row, 0).text()
        self.product_name.setText(self.table.item(row, 1).text())
        self.quantity.setText(self.table.item(row, 2).text())
        self.location.setText(self.table.item(row, 3).text())
        self.supplier_name.setText(self.table.item(row, 4).text())
        self.save_button.hide()

    def send_request(self, data):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("localhost", 9999))
            client.send(json.dumps(data).encode())
            response = client.recv(4096).decode()
            client.close()
            return json.loads(response)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_item(self):
        product_name = self.product_name.text()
        quantity = self.quantity.text()
        location = self.location.text()
        supplier_name = self.supplier_name.text()

        if not product_name or not quantity or not location or not supplier_name:
            QMessageBox.critical(self, "Ошибка", "Все поля обязательны для заполнения")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Данные о количестве должны быть в виде числа")
            return

        data = {
            "action": "add_item",
            "product_name": product_name,
            "quantity": quantity,
            "location": location,
            "supplier_name": supplier_name
        }

        response = self.send_request(data)

        if response["status"] == "success":
            self.result_area.setPlainText("Товар успешно добавлен")
            self.get_items()
            self.clear_inputs()
        else:
            self.result_area.setPlainText(f"Error: {response['message']}")

    def get_items(self):
        data = {"action": "get_items"}
        response = self.send_request(data)

        if response["status"] == "success":
            items = response["items"]
            self.table.setRowCount(0)
            for item in items:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for i, value in enumerate(item):
                    self.table.setItem(row_position, i, QTableWidgetItem(str(value)))
        else:
            self.result_area.setPlainText(f"Error: {response['message']}")

    def edit_item(self):
        if self.selected_item_id is None:
            QMessageBox.critical(self, "Ошибка", "Товар не выбран")
            return

        self.product_name.setEnabled(True)
        self.quantity.setEnabled(True)
        self.location.setEnabled(True)
        self.supplier_name.setEnabled(True)

    def save_item(self):
        if self.selected_item_id is None:
            QMessageBox.critical(self, "Ошибка", "Товар не выбран")
            return

        product_name = self.product_name.text()
        quantity = self.quantity.text()
        location = self.location.text()
        supplier_name = self.supplier_name.text()

        if not product_name or not quantity or not location or not supplier_name:
            QMessageBox.critical(self, "Ошибка", "Все поля обязательны для заполнения")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Данные о количестве должны быть в виде числа")
            return

        data = {
            "action": "update_item",
            "inventory_id": int(self.selected_item_id),
            "product_name": product_name,
            "quantity": quantity,
            "location": location,
            "supplier_name": supplier_name
        }

        response = self.send_request(data)

        if response["status"] == "success":
            self.result_area.setPlainText("Данные о товаре успешно обновленны")
            self.get_items()
            self.clear_inputs()
        else:
            self.result_area.setPlainText(f"Error: {response['message']}")

    def delete_item(self):
        if self.selected_item_id is None:
            QMessageBox.critical(self, "Ошибка", "Товар не выбран")
            return

        data = {
            "action": "delete_item",
            "inventory_id": int(self.selected_item_id)
        }

        response = self.send_request(data)

        if response["status"] == "success":
            self.result_area.setPlainText("Товар успешно удален")
            self.get_items()  # Refresh the table
            self.clear_inputs()
        else:
            self.result_area.setPlainText(f"Error: {response['message']}")

    def search_item(self):
        search_query = self.search_field.text()

        if not search_query:
            QMessageBox.critical(self, "Ошибка", "Поисковое поле пустое")
            return

        data = {
            "action": "search_item",
            "search_query": search_query
        }

        response = self.send_request(data)

        if response["status"] == "success":
            items = response["items"]
            self.table.setRowCount(0)
            for item in items:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for i, value in enumerate(item):
                    self.table.setItem(row_position, i, QTableWidgetItem(str(value)))
            self.result_area.setPlainText("Поиск прошел успешно")
        else:
            self.result_area.setPlainText(f"Error: {response['message']}")

    def clear_inputs(self):
        self.selected_item_id = None
        self.product_name.clear()
        self.quantity.clear()
        self.location.clear()
        self.supplier_name.clear()
        self.product_name.setEnabled(False)
        self.quantity.setEnabled(False)
        self.location.setEnabled(False)
        self.supplier_name.setEnabled(False)
        self.save_button.hide()

