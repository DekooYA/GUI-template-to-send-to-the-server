import sys
import paramiko
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QComboBox, QLabel

class RemoteServerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

        # Загрузка данных о серверах из файла
        self.load_servers()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.server_label = QLabel('Выберите сервер:')
        self.server_combo = QComboBox()
        self.server_combo.currentIndexChanged.connect(self.update_connection_details)

        self.connect_button = QPushButton('Подключиться к серверу')
        self.connect_button.clicked.connect(self.connect_to_server)

        self.command_input = QTextEdit()
        self.execute_button = QPushButton('Выполнить команду')
        self.execute_button.clicked.connect(self.execute_command)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.layout.addWidget(self.server_label)
        self.layout.addWidget(self.server_combo)
        self.layout.addWidget(self.connect_button)
        self.layout.addWidget(self.command_input)
        self.layout.addWidget(self.execute_button)
        self.layout.addWidget(self.output_text)

        self.central_widget.setLayout(self.layout)

        self.ssh_client = None

        self.servers = []

        # Добавление серверов (эти данные можно загружать из файла, базы данных и т.д.)
        self.servers = [
            {
                'name': 'Сервер 1',
                'host': 'your_remote_server1_address',
                'port': 22,
                'username': 'your_username1',
                'password': 'your_password1'
            },
            {
                'name': 'Сервер 2',
                'host': 'your_remote_server2_address',
                'port': 22,
                'username': 'your_username2',
                'password': 'your_password2'
            }
        ]

        # Заполнение выпадающего списка серверов
        for server in self.servers:
            self.server_combo.addItem(server['name'])

    def update_connection_details(self):
        # Обновление полей для подключения на основе выбранного сервера
        selected_server = self.servers[self.server_combo.currentIndex()]
        self.host = selected_server['host']
        self.port = selected_server['port']
        self.username = selected_server['username']
        self.password = selected_server['password']

    def load_servers(self):
        # Загрузка данных о серверах из файла (или базы данных)
        try:
            with open('servers.json', 'r') as file:
                self.servers = json.load(file)
                self.server_combo.clear()
                for server in self.servers:
                    self.server_combo.addItem(server['name'])
        except FileNotFoundError:
            # Если файл не найден, создайте пустой список
            self.servers = []

    def save_servers(self):
        # Сохранение данных о серверах в файл (или базу данных)
        with open('servers.json', 'w') as file:
            json.dump(self.servers, file, indent=4)

    def connect_to_server(self):
        if not self.host or not self.username or not self.password:
            self.output_text.append('Выберите сервер для подключения.')
            return

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.ssh_client.connect(self.host, self.port, self.username, self.password)
            self.output_text.append('Подключение к серверу выполнено успешно.')
        except Exception as e:
            self.output_text.append(f'Ошибка подключения: {str(e)}')

    def execute_command(self):
        if not self.ssh_client:
            self.output_text.append('Сначала подключитесь к серверу.')
            return

        command = self.command_input.toPlainText()
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if error:
            self.output_text.append(f'Ошибка выполнения команды: {error}')
        else:
            self.output_text.append(f'Результат выполнения команды:\n{output}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RemoteServerApp()
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle('Удаленное управление сервером')
    window.show()
    sys.exit(app.exec_())