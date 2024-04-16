"""
Это серверная часть чата. Данный модуль содержит все необходимые классы и функции для работы сервера.

Классы:

- **ClientHandler** - класс для обработки подключений клиентов
- **Server** - класс для запуска и управления сервером

Функции:

- **log_setup(loglevel, logfile)** - настраивает логирование
- **start_server(host, port)** - запускает сервер на указанном хосте и порту

Сервер использует сокеты для приема и отправки сообщений клиентам.
 Когда клиент подключается к серверу, создается объект ClientHandler для обработки этого подключения.
Объект ClientHandler запускается как отдельный поток и обрабатывает сообщения от клиента.
"""

# Импорт модулей

import os # для работы с файловой системой
import platform # для определения ОС
import socket # для определения IP адреса
import logging # для логирования
import argparse # для работы с аргументами командной строки
import threading # для работы с потоками
from datetime import datetime # для работы с датой и временем
from colorama import init, Fore, Style # для работы с цветом в консоли

clients = {}  # словарь с клиентами
clients_lock = threading.Lock() # блокировка для клиентов

def log_setup(loglevel, logfile): # настройка логирования
    numeric_level = getattr(logging, loglevel.upper(), None) # получение уровня логирования
    if not isinstance(numeric_level, int): # проверка на корректность уровня логирования
        raise ValueError(f"Неверный уровень логирования: {loglevel}") # если некорректно, вывод сообщения об ошибке

    logging.basicConfig(level=numeric_level, # настройка уровня логирования
                        format="%(asctime)s [%(levelname)s] - %(message)s", # формат логирования
                        handlers=[logging.FileHandler(logfile), # запись логов в файл
                                  logging.StreamHandler()]) # запись логов в консоль

class ClientHandler(threading.Thread): # класс для обработки клиентов
    def __init__(self, client_socket): # инициализация класса
        threading.Thread.__init__(self) # инициализация базового класса
        self.client_socket = client_socket # сохранение сокета клиента
        self.username = None # сохранение имени пользователя

    def run(self): # функция для работы потока
        global clients # глобальная переменная с клиентами
        logging.info(f"Новый пользователь подключен!: {self.client_socket.getpeername()}")  # запись в лог


        # Спросить и подтвердить имя пользователя
        while True:
            try:
                self.client_socket.send("Введите имя пользователя //: ".encode('utf-8')) # отправка сообщения
                username = self.client_socket.recv(1024).decode('utf-8').strip() # получение сообщения
                with clients_lock: # блокировка
                    if username in clients or not username: # проверка на существование пользователя
                        self.client_socket.send( # отправка сообщения об ошибке
                            "Это имя пользователя уже занято. Пожалуйста введите другое.".encode('utf-8'))
                        continue  # После отправки ошибочного сообщения, вернуть в начало
                    else:
                        self.username = username # сохранение имени пользователя
                        clients[self.username] = self.client_socket # сохранение сокета клиента
                        self.client_socket.send("Имя установлено успешно.".encode('utf-8')) # отправка сообщения об успехе
                        break

            except BrokenPipeError as e: # обработка ошибки
                if e.errno == 32: # ошибка закрытия сокета
                    pass
                else:
                    print(f"Возникла неизвестная ошибка: {e}")
                    logging.info(f"Возникла неизвестная ошибка: {e}")
                return
        # Процесс сообщений
        try:
            while True:
                message = self.client_socket.recv(1024).decode('utf-8') # получение сообщения
                if message == "/userlist": # получение списка пользователей
                    with clients_lock:
                        userlist = "\n".join([f"\t{i + 1}) {user}" for i, user in enumerate(clients.keys())]) # формирование списка пользователей
                        response = f"Подключенные пользователи:\n{userlist}" # формирование ответа
                        self.client_socket.send(response.encode('utf-8')) # отправка ответа
                        continue
                if message == "/help": # получение меню помощи
                    response = Fore.BLUE + "Меню помощи:\n" \
                                           "\t/help                           -> Меню помощи\n" \
                                           "\t/exit                           -> Выйти из чата.\n" \
                                           "\t/clear                          -> Отчистить чат.\n" \
                                           "\t/userlist                       -> Посмотреть подключенных пользователей.\n" \
                                           "\t/dm [user] [message]            -> Отправить сообщение в директ пользователю.\n" \
                                           "\t/changeuser [new_username]      -> Сменить имя пользователя.\n"
                    self.client_socket.send(response.encode('utf-8')) # отправка ответа
                    continue

                if message.startswith("/changeuser "): # получение команды сменить имя пользователя
                    _, new_username = message.split() # разбиение сообщения на части
                    with clients_lock:
                        if new_username in clients: # проверка на существование пользователя
                            self.client_socket.send(
                                "Это имя пользователя уже занято. Пожалуйста в ведите другое.".encode('utf-8'))
                        else:
                            # Удалить старое имя пользователя и добавить
                            del clients[self.username] # удаление старого имени пользователя
                            self.username = new_username # установка нового имени пользователя
                            clients[self.username] = self.client_socket # добавление нового имени пользователя
                            self.client_socket.send(f"Имя изменено... {new_username}.".encode('utf-8')) # отправка ответа
                    continue

                if message.startswith("/dm "): # получение команды отправить сообщение в директ пользователю
                    _, recipient, *dm_msg_parts = message.split() # разбиение сообщения на части
                    dm_message = " ".join(dm_msg_parts) # объединение частей сообщения
                    with clients_lock:
                        if recipient in clients: # проверка на существование пользователя
                            clients[recipient].send(f"[Директ от {self.username}] {dm_message}".encode('utf-8')) # отправка сообщения
                            self.client_socket.send(f"[Директ куда {recipient}] {dm_message}".encode('utf-8'))
                        else:
                            self.client_socket.send("Такой пользователь не найден.".encode('utf-8'))
                    continue

                if message == "/clear": # получение команды очистить чат
                    self.client_socket.send("/clear".encode('utf-8')) # отправка ответа
                    continue

                if not message or message == "/exit": # получение команды выйти из чата
                    break
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # получение текущей даты и времени
                broadcast_message = f"[{current_time}] {self.username}: {message}" # формирование сообщения
                with clients_lock:
                    for usr, client in clients.items(): # отправка сообщения всем клиентам
                        if usr != self.username: # отправка сообщения только клиентам, кроме самого пользователя
                            client.send(broadcast_message.encode('utf-8')) # отправка сообщения
        except:
            pass

        # Отчистить после выхода клиента
        with clients_lock: # блокировка доступа к списку клиентов
            del clients[self.username] # удаление пользователя из списка клиентов
            logging.info(f"Пользователь покинул...: {username}")
        self.client_socket.close() # закрытие сокета

def start_server(host, port): # функция запуска сервера
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # создание сокета
        server_socket.bind((host, port)) # привязка сокета к адресу и порту
        host_ip, host_port = server_socket.getsockname() # получение информации о сокете
        server_socket.listen(5) # запуск сервера
        print("Сервер запущен. Ждем поключений...")
        print(f"{Fore.YELLOW}Информация о Хосте: {Style.RESET_ALL}{host_ip}:{host_port}") # Лог информация о хосте
        logging.info(f"Сервер запущен на {host_ip}:{host_port}")  # Лог информация о хосте
        while True:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # получение текущей даты и времени
            client_socket, client_address = server_socket.accept() # получение подключения от клиента
            print(f"[{current_time}] {client_address} Подключается.") # Лог подключение
            logging.info(f"Ждем подключения от {client_address}")  # Лог подключение
            handler = ClientHandler(client_socket) # создание обработчика клиента
            handler.start() # запуск обработчика клиента

    except OSError as e: # Обработка ошибок
        if e.errno == 98: # Адрес занят
            print("Такой адрес уже используется, you wild thing :D")
            logging.error("Такой адрес уже используется")  # Лог ошибка
        else:
            print(f"Возникла непредвиденная ошибка при старте сервера: {e}")
            logging.error(f"Возникла ошибка: {e}")  # Лог ошибка
    except KeyboardInterrupt:
        print("Программа завершена.....")
        logging.info("Работа сервера завершилась с ошибкой")  # Лог информация о завершении сервера


if __name__ == "__main__": # Запуск сервера
    parser = argparse.ArgumentParser(description="Старт сервера.") # Парсер
    parser.add_argument("--host", default="0.0.0.0", help="Айпи адрес привязанный к серверу. (По-умолчанию: 0.0.0.0)") # Адрес
    parser.add_argument("--port", type=int, default=12345, help="Порт заданный серверу. (По-умолчанию: 12345)") # Порт
    parser.add_argument("--loglevel", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],help="Set the logging level (Default: INFO)") # Уровень логирования
    parser.add_argument("--logfile", default="server.log", help="Задать имя лог файла. (По-умолчанию: server.log") # Файл логирования
    args = parser.parse_args() # Парсинг аргументов

    log_setup(args.loglevel, args.logfile)  # Настройка логирования

    start_server(args.host, args.port) # Запуск сервера
