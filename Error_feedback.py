# Библиотеки для отправки ошибки
# import email.mime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from json import loads
from os import getenv
# import sys
# import re
from re import finditer, IGNORECASE
# import smtplib
from smtplib import SMTP_SSL
# import ssl
from ssl import create_default_context

# Библиотеки, чтобы скрыть важные данные
from dotenv import load_dotenv
# import telebot
from telebot import TeleBot

from File_helper import FileHelper

# Подгрузка токена бота и его создание
load_dotenv()


# Функция скрытия пароля
def mask_passwords(text: str) -> str:
    """
    Заменяет все пароли в тексте на маску *PASSWORD*
    Обрабатывает команды и текстовый вывод в различных форматах:

    Командные форматы:
    -p"12345" -> -p"*PASSWORD*"
    -p "12345" -> -p "*PASSWORD*"
    --password "12345" -> --password "*PASSWORD*"
    --password"12345" -> --password"*PASSWORD*"
    -p '12345' -> -p '*PASSWORD*'
    --password=12345 -> --password=*PASSWORD*
    /p"12345" -> /p"*PASSWORD*"

    Текстовые форматы:
    Password   : 12345678 -> Password   : *PASSWORD*
    Password: 12345678 -> Password: *PASSWORD*
    Password = 12345678 -> Password = *PASSWORD*
    """

    # Паттерны для поиска паролей в командах
    command_patterns = [
        # -p"password" или -p'password' (без пробела)
        r'(-p\s*["\'])([^"\']*)(["\'])',
        # -p "password" или -p 'password' (с пробелом)
        r'(-p\s+["\'])([^"\']*)(["\'])',
        # --password"password" или --password'password' (без пробела)
        r'(--password\s*["\'])([^"\']*)(["\'])',
        # --password "password" или --password 'password' (с пробелом)
        r'(--password\s+["\'])([^"\']*)(["\'])',
        # --password=password
        r'(--password=)([^\s]*)',
        # -p password (без кавычек)
        r'(-p\s+)([^\s"]+)',
        # --password password (без кавычек)
        r'(--password\s+)([^\s"]+)',
        # /p"password" (для некоторых утилит)
        r'(/p\s*["\'])([^"\']*)(["\'])',
        # /password password
        r'(/password\s+)([^\s"]+)'
    ]

    # Паттерны для поиска паролей в текстовом выводе
    text_patterns = [
        # Password: value (с разными разделителями)
        r'(Password\s*[:=]\s*)([^\s"]+)',
        # Password: "value" (в кавычках)
        r'(Password\s*[:=]\s*["\'])([^"\']*)(["\'])',
        # Password   : value (с множественными пробелами)
        r'(Password\s+[:=]\s*)([^\s"]+)'
    ]

    masked_text = text

    # Обрабатываем командные паттерны
    for pattern in command_patterns:
        matches = list(finditer(pattern, masked_text, IGNORECASE))
        for match in matches:
            full_match = match.group(0)
            groups = match.groups()

            if len(groups) == 3:  # Паттерны с кавычками
                prefix, password, suffix = groups
                if password and password != "*PASSWORD*":
                    masked_version = f'{prefix}*PASSWORD*{suffix}'
                    masked_text = masked_text.replace(full_match, masked_version, 1)
            else:  # Паттерны без кавычек (2 группы)
                prefix, password = groups
                if password and password != "*PASSWORD*":
                    masked_version = f'{prefix}*PASSWORD*'
                    masked_text = masked_text.replace(full_match, masked_version, 1)

    # Обрабатываем текстовые паттерны
    for pattern in text_patterns:
        matches = list(finditer(pattern, masked_text, IGNORECASE))
        for match in matches:
            full_match = match.group(0)
            groups = match.groups()

            if len(groups) == 3:  # Паттерны с кавычками
                prefix, password, suffix = groups
                if password and password != "*PASSWORD*":
                    masked_version = f'{prefix}*PASSWORD*{suffix}'
                    masked_text = masked_text.replace(full_match, masked_version, 1)
            else:  # Паттерны без кавычек (2 группы)
                prefix, password = groups
                if password and password != "*PASSWORD*":
                    masked_version = f'{prefix}*PASSWORD*'
                    masked_text = masked_text.replace(full_match, masked_version, 1)

    return masked_text


class ErrorFeedback:
    def __init__(self, computer_name: str, error_logs: list, name_paths_error_log: list) -> None:
        self.computer_name = computer_name
        self.error_logs = error_logs

        # Гарантируем одинаковую длину списков
        while len(name_paths_error_log) < len(error_logs):
            name_paths_error_log.append(None)

        # Формируем текст сообщения с ошибками
        self.error_log_txt = f'Errors from {self.computer_name}: \n'
        for ind, er in enumerate(error_logs):
            self.error_log_txt += f'{ind + 1}) path name: {name_paths_error_log[ind]}:\n{mask_passwords(er)}\n'

    # Отправляем ошибки
    def send_error(self):
        self.email_error()
        self.tg_error()
        self.file_error(FileHelper())

    # Отправляем ошибку по почте
    def email_error(self):
        file = FileHelper()
        try:
            # Создаем безопасное соединение
            context = create_default_context()

            # Используем контекстный менеджер для автоматического закрытия соединения
            with SMTP_SSL("smtp.yandex.com", 465, context=context) as server:
                # Аутентификация
                server.login(getenv('MAIL_FROM'), getenv('MAIL_PASSWORD'))

                # Формируем сообщение
                msg = MIMEMultipart()
                msg["From"] = getenv('MAIL_FROM')

                # Рабочий
                # msg["To"] = getenv('MAIL_TO')
                # Тестирование
                msg["To"] = getenv('MAIL_TO_TEST')

                msg["Subject"] = f'Backup Errors: {self.computer_name}'

                # Добавляем текст сообщения
                msg.attach(MIMEText(self.error_log_txt, "plain"))

                # Отправляем письмо
                server.send_message(msg)

                file.work_file("Email успешно отправлен.")
        except Exception as e:
            file.work_file(f"Ошибка отправки email: {str(e)}")

    # Отправляем ошибку в тг-боте
    def tg_error(self):
        # Подключаем бота
        TOKEN = getenv('TOKEN')
        Bot = TeleBot(TOKEN, parse_mode=None)

        '''
        # Если нужно получить ID
        
        @Bot.message_handler(commands=['start'])
        def get_id(message):
            print(message.chat.id)
        '''

        # Выводим сообщения
        try:
            # Рабочий
            # IDS = loads(getenv('IDS'))
            # Тестирование
            IDS = loads(getenv('TEST_IDS'))

            for ID in IDS:
                Bot.send_message(ID, self.error_log_txt)
        except Exception as e:
            file = FileHelper()
            file.work_file(f"Ошибка отправки телеграмм: {str(e)}")

    def file_error(self, file):
        file.work_file(self.error_log_txt)
