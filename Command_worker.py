# Библиотека для ОС
import os
import subprocess
import locale


class CommandWorker:
    # Получение пути к файлу кода (папка скрипта) и добавление его имени
    @staticmethod
    def get_path(name: str) -> str:
        return os.path.abspath(name)

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
        except subprocess.CalledProcessError as e:
            # Обработка ошибок выполнения команды
            error_msg = f"Ошибка выполнения команды (код {e.returncode}):\n{e.output}"
            print(error_msg)
            return error_msg
        except FileNotFoundError as e:
            # Обработка случая, когда команда не найдена
            error_msg = f"Команда не найдена: {e.filename}"
            print(error_msg)
            return error_msg
        except Exception as e:
            # Обработка всех остальных исключений
            error_msg = f"Неизвестная ошибка: {str(e)}"
            print(error_msg)
            return error_msg
