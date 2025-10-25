# Библиотеки для отправки ошибки
from File_helper import FileHelper

# import ssl
from ssl import create_default_context
# import telebot
from telebot import TeleBot
# import email.mime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# import smtplib
from smtplib import SMTP_SSL
# import sys
from sys import exit

# Библиотеки, чтобы скрыть важные данные
from dotenv import load_dotenv
from os import getenv
from json import loads


# Подгрузка токена бота и его создание
load_dotenv()


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
            self.error_log_txt += f'{ind + 1}) path name: {name_paths_error_log[ind]}:\n{er}\n'

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
