import sys
import paramiko
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QComboBox, QLabel, QLineEdit, QDialog, QFileDialog, QPlainTextEdit
from PyQt5.QtCore import pyqtSignal
from qtermwidget import QTermWidget

class RemoteServerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
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
        self.command_input = QPlainTextEdit()
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
        self.add_server_button = QPushButton('Добавить сервер')
        self.add_server_button.clicked.connect(self.add_server)
        self.layout.addWidget(self.add_server_button)
        self.edit_server_button = QPushButton('Редактировать сервер')
        self.edit_server_button.clicked.connect(self.edit_server)
        self.layout.addWidget(self.edit_server_button)
        self.remove_server_button = QPushButton('Удалить сервер')
        self.remove_server_button.clicked.connect(self.remove_server)
        self.layout.addWidget(self.remove_server_button)
        self.terminal_widget = QTermWidget()
        self.layout.addWidget(self.terminal_widget)
        self.terminal_widget.set_cwd('~')
        self.central_widget.setLayout(self.layout)
        self.ssh_client = None
        self.servers = []

    def update_connection_details(self):
        selected_server = self.servers[self.server_combo.currentIndex()]
        self.host = selected_server['host']
        self.port = selected_server['port']
        self.username = selected_server['username']
        self.password = selected_server['password']
        self.private_key_path = selected_server.get('private_key_path', None)

    def load_servers(self):
        try:
            with open('servers.json', 'r') as file:
                self.servers = json.load(file)
                self.server_combo.clear()
                for server in self.servers:
                    self.server_combo.addItem(server['name'])
        except FileNotFoundError:
            self.servers = []

    def save_servers(self):
        with open('servers.json', 'w') as file:
            json.dump(self.servers, file, indent=4)

    def connect_to_server(self):
        if not self.host or not self.username:
            self.output_text.append('Выберите сервер и введите имя пользователя.')
            return
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.private_key_path:
                private_key = paramiko.RSAKey(filename=self.private_key_path)
                self.ssh_client.connect(self.host, self.port, self.username, pkey=private_key)
            else:
                self.ssh_client.connect(self.host, self.port, self.username, self.password)
        except paramiko.AuthenticationException:
            self.output_text.append('Ошибка аутентификации. Проверьте учетные данные.')
            self.ssh_client.close()
            self.ssh_client = None

    def execute_command(self):
        if not self.ssh_client:
            self.output_text.append('Сначала подключитесь к серверу.')
            return
        command = self.command_input.toPlainText()
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        self.output_text.append(stdout.read().decode('utf-8'))
        self.output_text.append(stderr.read().decode('utf-8'))

    def add_server(self):
        dialog = ServerDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            server_data = {
                'name': dialog.name_line.text(),
                'host': dialog.host_line.text(),
                'port': int(dialog.port_line.text()),
                'username': dialog.username_line.text(),
                'password': dialog.password_line.text(),
                'private_key_path': dialog.private_key_line.text()
            }
            self.servers.append(server_data)
            self.server_combo.addItem(server_data['name'])
            self.save_servers()

    def edit_server(self):
        if self.server_combo.currentIndex() == -1:
            self.output_text.append('Выберите сервер для редактирования.')
            return
        dialog = ServerDialog(self)
        selected_server = self.servers[self.server_combo.currentIndex()]
        dialog.name_line.setText(selected_server['name'])
        dialog.host_line.setText(selected_server['host'])
        dialog.port_line.setText(str(selected_server['port']))
        dialog.username_line.setText(selected_server['username'])
        dialog.password_line.setText(selected_server['password'])
        dialog.private_key_line.setText(selected_server['private_key_path'])
        result = dialog.exec_()
        if result == QDialog.Accepted:
            server_data = {
                'name': dialog.name_line.text(),
                'host': dialog.host_line.text(),
                'port': int(dialog.port_line.text()),
                'username': dialog.username_line.text(),
                'password': dialog.password_line.text(),
                'private_key_path': dialog.private_key_line.text()
            }
            self.servers[self.server_combo.currentIndex()] = server_data
            self.save_servers()

    def remove_server(self):
        if self.server_combo.currentIndex() == -1:
            self.output_text.append('Выберите сервер для удаления.')
            return
        selected_index = self.server_combo.currentIndex()
        del self.servers[selected_index]
        self.server_combo.removeItem(selected_index)
        self.save_servers()

class ServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Добавить сервер')
        self.setGeometry(100, 100, 400, 250)
        layout = QVBoxLayout()
        self.name_label = QLabel('Имя сервера:')
        self.name_line = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_line)
        self.host_label = QLabel('Адрес сервера:')
        self.host_line = QLineEdit()
        layout.addWidget(self.host_label)
        layout.addWidget(self.host_line)
        self.port_label = QLabel('Порт:')
        self.port_line = QLineEdit()
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_line)
        self.username_label = QLabel('Имя пользователя:')
        self.username_line = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_line)
        self.password_label = QLabel('Пароль:')
        self.password_line = QLineEdit()
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_line)
        self.private_key_label = QLabel('Путь к ключу SSH:')
        self.private_key_line = QLineEdit()
        layout.addWidget(self.private_key_label)
        layout.addWidget(self.private_key_line)
        self.browse_button = QPushButton('Обзор')
        self.browse_button.clicked.connect(self.browse_private_key)
        layout.addWidget(self.browse_button)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def browse_private_key(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, 'Выберите ключ SSH', '', 'All Files (*);;Private Key Files (*.pem;*.ppk)', options=options)
        if file_name:
            self.private_key_line.setText(file_name)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RemoteServerApp()
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle('Удаленное управление сервером')
    window.show()
    sys.exit(app.exec())
