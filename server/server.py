import sqlite3
import socket
import threading
import json


class InventoryServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", 5252))
        self.server.listen(5)
        print("Сервер прослушивает порт 5252")

        self.conn = sqlite3.connect('bakery_inventory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Suppliers (
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT NOT NULL UNIQUE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                supplier_id INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT NOT NULL UNIQUE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Inventory (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                location_id INTEGER,
                FOREIGN KEY (product_id) REFERENCES Products(product_id),
                FOREIGN KEY (location_id) REFERENCES Locations(location_id)
            )
        """)

        self.conn.commit()

    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode()
            data = json.loads(request)

            if data["action"] == "add_item":
                product_name = data["product_name"]
                quantity = data["quantity"]
                location = data["location"]
                supplier_name = data["supplier_name"]

                self.cursor.execute("INSERT OR IGNORE INTO Suppliers (supplier_name) VALUES (?)", (supplier_name,))
                self.conn.commit()
                self.cursor.execute("SELECT supplier_id FROM Suppliers WHERE supplier_name = ?", (supplier_name,))
                supplier_id = self.cursor.fetchone()[0]

                self.cursor.execute("INSERT INTO Products (product_name, supplier_id) VALUES (?, ?)",
                                    (product_name, supplier_id))
                self.conn.commit()
                self.cursor.execute("SELECT product_id FROM Products WHERE product_name = ?", (product_name,))
                product_id = self.cursor.fetchone()[0]

                self.cursor.execute("INSERT OR IGNORE INTO Locations (location_name) VALUES (?)", (location,))
                self.conn.commit()
                self.cursor.execute("SELECT location_id FROM Locations WHERE location_name = ?", (location,))
                location_id = self.cursor.fetchone()[0]

                self.cursor.execute("INSERT INTO Inventory (product_id, quantity, location_id) VALUES (?, ?, ?)",
                                    (product_id, quantity, location_id))
                self.conn.commit()
                response = {"status": "success"}

            elif data["action"] == "get_items":
                self.cursor.execute("""
                    SELECT Inventory.inventory_id, Products.product_name, Inventory.quantity, Locations.location_name, Suppliers.supplier_name
                    FROM Inventory
                    JOIN Products ON Inventory.product_id = Products.product_id
                    JOIN Locations ON Inventory.location_id = Locations.location_id
                    JOIN Suppliers ON Products.supplier_id = Suppliers.supplier_id
                """)
                items = self.cursor.fetchall()
                response = {"status": "success", "items": items}

            elif data["action"] == "update_item":
                inventory_id = data["inventory_id"]
                product_name = data["product_name"]
                quantity = data["quantity"]
                location = data["location"]
                supplier_name = data["supplier_name"]

                self.cursor.execute("SELECT supplier_id FROM Suppliers WHERE supplier_name = ?", (supplier_name,))
                supplier_id = self.cursor.fetchone()
                if not supplier_id:
                    self.cursor.execute("INSERT INTO Suppliers (supplier_name) VALUES (?)", (supplier_name,))
                    self.conn.commit()
                    supplier_id = self.cursor.lastrowid
                else:
                    supplier_id = supplier_id[0]

                self.cursor.execute("SELECT product_id FROM Products WHERE product_name = ?", (product_name,))
                product_id = self.cursor.fetchone()
                if not product_id:
                    self.cursor.execute("INSERT INTO Products (product_name, supplier_id) VALUES (?, ?)",
                                        (product_name, supplier_id))
                    self.conn.commit()
                    product_id = self.cursor.lastrowid
                else:
                    product_id = product_id[0]

                self.cursor.execute("SELECT location_id FROM Locations WHERE location_name = ?", (location,))
                location_id = self.cursor.fetchone()
                if not location_id:
                    self.cursor.execute("INSERT INTO Locations (location_name) VALUES (?)", (location,))
                    self.conn.commit()
                    location_id = self.cursor.lastrowid
                else:
                    location_id = location_id[0]

                self.cursor.execute(
                    "UPDATE Inventory SET product_id = ?, quantity = ?, location_id = ? WHERE inventory_id = ?",
                    (product_id, quantity, location_id, inventory_id))
                self.conn.commit()
                response = {"status": "success"}

            elif data["action"] == "delete_item":
                inventory_id = data["inventory_id"]
                self.cursor.execute("DELETE FROM Inventory WHERE inventory_id = ?", (inventory_id,))
                self.conn.commit()
                response = {"status": "success"}

            elif data["action"] == "search_item":
                search_query = data["search_query"]
                self.cursor.execute("""
                    SELECT Inventory.inventory_id, Products.product_name, Inventory.quantity, Locations.location_name, Suppliers.supplier_name
                    FROM Inventory
                    JOIN Products ON Inventory.product_id = Products.product_id
                    JOIN Locations ON Inventory.location_id = Locations.location_id
                    JOIN Suppliers ON Products.supplier_id = Suppliers.supplier_id
                    WHERE Products.product_name LIKE ?
                """, ('%' + search_query + '%',))
                items = self.cursor.fetchall()
                response = {"status": "success", "items": items}

            else:
                response = {"status": "error", "message": "Invalid action"}

        except Exception as e:
            response = {"status": "error", "message": str(e)}

        client_socket.send(json.dumps(response).encode())
        client_socket.close()

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            print(f"Принято соединение от {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()