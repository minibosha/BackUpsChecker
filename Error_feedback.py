# Библиотеки для отправки ошибки
import telebot
import ssl

from File_helper import FileHelper

# import email.mime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# import smtplib
from smtplib import SMTP_SSL
# import sys
from sys import exit


class ErrorFeedback:
    def __init__(self, computer_name: str, error_logs: list) -> None:
        self.computer_name = computer_name
        self.error_logs = error_logs

        # Формируем текст сообщения с ошибками
        self.error_log_txt = f'Errors from {self.computer_name}: \n'
        for ind, er in enumerate(error_logs):
            self.error_log_txt += f'{ind + 1}) {er}\n'

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
            context = ssl.create_default_context()

            # Используем контекстный менеджер для автоматического закрытия соединения
            with SMTP_SSL("smtp.yandex.com", 465, context=context) as server:
                # Аутентификация
                server.login("boldaevaleksandr@yandex.ru", "qsjanliarwuodpxq")

                # Формируем сообщение
                msg = MIMEMultipart()
                msg["From"] = "boldaevaleksandr@yandex.ru"
                msg["To"] = "nnaill.ru@mail.ru"
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
        TOKEN = '7894828943:AAGcbqqSmj1z-pXfO6tGlUPFKDE65LDk1gk'
        Bot = telebot.TeleBot(TOKEN, parse_mode=None)
        # Если нужно получить ID
        '''
        @Bot.message_handler(commands=['start'])
        def get_id(message):
            print(message.chat.id)
        '''
        # Выводим сообщения
        # Рабочий
        # IDS = [1181643061, 968066585]
        # Тестирование
        IDS = [1181643061]
        for ID in IDS:
            Bot.send_message(ID, self.error_log_txt)

    def file_error(self, file):
        file.work_file(self.error_log_txt)
