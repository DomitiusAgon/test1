""" Это клиентская часть чат-приложения. Данный модуль содержит все необходимые классы и функции для работы клиента.

Классы:

ChatClient - основной класс, отвечающий за подклю чение к серверу, обмен сообщениями и обработку команд.

Функции:

init(host, port) - конструктор класса, который устанавливает адрес и порт сервера.
connect() - функция, устанавливающая соединение с сервером.
get _username() - функция, по��учающая имя пользователя от пользователя.
listen_to_server() - функция, прослушивающая сообщения от сервера.
send_messages() - функция, отправляющая сообщения на сервер.
run() - функция, запускающая клиентское приложение. """


# Импорт модулей
import os  # Модуль для работы с файловой системой
import socket # Модуль для работы с сокетами. Сетевые функции
import argparse # Модуль для работы с аргументами командной строки
import threading # Модуль для работы с потоками
from colorama import init, Fore, Style # Модуль для работы с цветом в консоли

init(autoreset=True) # Инициализация цвета в консоли

class ChatClient:
    def __init__(self, host, port):
        self.host = host # Адрес сервера
        self.port = port # Порт сервера
        self.client_socket = None # Сокет для подключения к серверу
        self.username = None # Имя пользователя
        self.message_lock = threading.Lock() # Блокировка для обеспечения безопасности обмена сообщениями между потоками

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создание сокета
            self.client_socket.connect((self.host, self.port)) # Подключение к серверу
        except ConnectionRefusedError as e: # Обработка ошибки подключения
            if e.errno == 111: # Ошибка 111 - невозможно подключиться к серверу
                print("Соединение разорвано :()") # Вывод сообщения об ошибке
            else:
                print(f"Возникла неизвестная ошибка... {e}")
            return False
        return True

    def get_username(self): # Метод получения имени пользователя
        username_prompt = self.client_socket.recv(1024).decode('utf-8') # Получение имени пользователя
        print(Fore.CYAN + username_prompt, end="") # Вывод имени пользователя в консоль
        username = input() # Получение имени пользователя ввода
        self.client_socket.send(username.encode('utf-8')) # Отправка имени пользователя на сервер
        response = self.client_socket.recv(1024).decode('utf-8') # Получение ответа сервера
        if "Пожалуйста введите другое имя пользователя." in response: # Обработка ошибки
            print(Fore.RED + response) # Вывод сообщения об ошибке
            return False
        self.username = username # Сохранение имени пользователя
        print(Fore.BLUE + "Меню помощи:") # Вывод меню помощи
        print("\t/help       -> Меню помощи")
        return True

    def listen_to_server(self): # Метод прослушивания сервера
        while True:
            data = self.client_socket.recv(1024).decode('utf-8') # Получение данных от сервера
            if not data:
                break

            if data.strip() == "/clear": # Обработка команды /clear
                os.system('cls' if os.name == 'nt' else 'clear') # Очистка консоли
                print(f"{Fore.GREEN}\n\t/help       -> Меню помощи\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} ////: {Style.RESET_ALL}",end='') # Вывод сообщения об успешном выполнении команды
                continue

            with self.message_lock: # Блокировка доступа к списку сообщений
                if "Имя изменено... " in data: # Обработка команды /nick
                    self.username = data.split("Имя изменено... ")[1].rstrip(".") # Получение нового имени пользователя
                    print(f"{Fore.GREEN}\n{data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} ////: {Style.RESET_ALL}", end='') # Вывод сообщения об успешном выполнении команды
                else:
                    print(f"{Fore.GREEN}\n{data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} ////: {Style.RESET_ALL}", end='') # Вывод сообщения об успешном выполнении команды

    def send_messages(self): # Отправка сообщений пользователя
        while True:
            try:
                print(f"{self.username}: {Fore.YELLOW}////: {Style.RESET_ALL}", end='') # Вывод сообщения об успешном выполнении команды
                message = input()
                if message == "/exit": # Обработка команды /exit
                    self.client_socket.send(message.encode('utf-8')) # Отправка сообщения пользователю
                    break
                self.client_socket.send(message.encode('utf-8'))

            except ConnectionRefusedError as e: # Обработка ошибки подключения
                if e.errno == 111:
                    print("Соединение разорвано") # Вывод сообщения об ошибке подключения
                else:
                    print(f"Возникла неизвестная ошибка... {e}")

            except KeyboardInterrupt: # Обработка ошибки отключения
                print(Fore.RED + "\nПодключение закрыто...") 
                self.client_socket.send("/exit".encode('utf-8')) # Отправка сообщения пользователю
                break

    def run(self): # Запуск программы
        if self.connect(): # Подключение к серверу
            if self.get_username(): # Получение имени пользователя
                threading.Thread(target=self.listen_to_server, daemon=True).start() # Обработка сообщений от сервера
                self.send_messages() # Отправка сообщений пользователя
        self.client_socket.close() # Закрытие соединения с сервером


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Подключение к серверу...") # Парсер командной строки
    parser.add_argument("--host", default="127.0.0.1", help="Айпи адрес сервера.") # Айпи адрес сервера
    parser.add_argument("--port", type=int, default=12345, help="Порт сервера.") # Порт сервера
    args = parser.parse_args() # Получение аргументов командной строки

    client = ChatClient(args.host, args.port) # Создание объекта класса ChatClient
    client.run() # Запуск программы
