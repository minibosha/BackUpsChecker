# Библиотека для ОС
import subprocess

# import os
from os import path
# import sys
from sys import exit


class CommandWorker:
    # Получение пути к файлу кода (папка скрипта) и добавление его имени
    @staticmethod
    def get_path(name: str) -> str:
        return path.abspath(name)

    # Отправка и возврат ответа от командной строки
    @staticmethod
    def command_get(command: str) -> str:
        try:
            # Выполняем команду через оболочку (shell=True)
            result = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='CP866'
            )
            return result
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            with open(path.abspath("work_log_ch.txt"), 'a') as file:
                file.write(f'ERROR: COMMAND ERROR. {e}')
            return ''
