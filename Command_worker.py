# Библиотека для ОС
import subprocess
import ctypes

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
        timeout_seconds = 15  # 5 минут

        try:
            # Создаем процесс с подключенными каналами ввода/вывода
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='CP866'
            )

            # Ждем завершения процесса с таймаутом
            stdout, _ = process.communicate(timeout=timeout_seconds)

            # Проверяем код возврата
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command, output=stdout)

            return stdout

        except subprocess.TimeoutExpired:
            # Принудительно завершаем процесс при таймауте
            error_msg = f"TIME ERROR: command {command} TOO MUCH TIME TO WAIT"

            try:
                if 'process' in locals():
                    # На Windows используем taskkill для принудительного завершения процесса
                    subprocess.run(f"taskkill /F /PID {process.pid}",
                                   shell=True,
                                   capture_output=True,
                                   timeout=10)
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                # Если не удалось завершить через taskkill, пробуем альтернативный метод
                try:
                    # Используем ctypes для вызова Windows API
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(1, False, process.pid)
                    kernel32.TerminateProcess(handle, -1)
                    kernel32.CloseHandle(handle)
                except:
                    # Если все методы не сработали, просто продолжаем
                    pass
            finally:
                return error_msg

        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            return f'ERROR: COMMAND ERROR. {e}'
