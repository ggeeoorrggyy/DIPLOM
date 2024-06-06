
from server.server import InventoryServer
from client.client import InventoryClient, QApplication
from threading import Thread
import sys


def main():
    server = InventoryServer()
    server_thread = Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)
    client = InventoryClient()
    client.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
