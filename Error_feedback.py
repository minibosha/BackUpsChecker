# Библиотеки для отправки ошибки
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from File_helper import FileHelper
import ssl


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

    # Отправляем ошибку по почте
    def email_error(self):
        file = FileHelper()
        try:
            # Создаем безопасное соединение
            context = ssl.create_default_context()

            # Используем контекстный менеджер для автоматического закрытия соединения
            with smtplib.SMTP_SSL("smtp.yandex.com", 465, context=context) as server:
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
        pass
