# Библиотека для ОС
import os
import subprocess


class CommandWorker:
    # Получение пути к файлу кода (папка скрипта) и добавление его имени
    @staticmethod
    def get_path(name: str):
        return os.path.abspath(name)

    # Отправка и возврат ответа от командной строки
    @staticmethod
    def command_get(command: str):
        # Отправка сообщения командной строки и получение ответа от неё
        returned_output = subprocess.check_output(command)
        # Возвращаем ответ в нужной кодировке
        return returned_output.decode("CP866")
