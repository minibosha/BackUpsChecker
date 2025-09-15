# Библиотека для ОС
import subprocess
import ctypes
import psutil

# import os
from os import path, getpid
# import sys
from sys import exit, executable


class CommandWorker:
    # Получение пути к файлу кода (папка скрипта) и добавление его имени
    @staticmethod
    def get_path(name: str) -> str:
        return path.abspath(name)

    # Отправка и возврат ответа от командной строки
    @staticmethod
    def command_get(command: str) -> str:
        timeout_seconds = 300  # 5 минут

        try:
            # Создаем процесс
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='CP866',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            # Ждем завершения процесса с таймаутом
            stdout, _ = process.communicate(timeout=timeout_seconds)



            #  ОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладкаОткладка
            print(stdout)



            # Проверяем код возврата
            if process.returncode != 0:
                return f'ERROR: COMMAND FAILED WITH CODE {process.returncode}.\nOutput: {stdout}'

            # Возвращаем результат
            return stdout

        except subprocess.TimeoutExpired:
            # Принудительно завершаем процесс при таймауте
            error_msg = f"TIME ERROR: command {command} TOO MUCH TIME TO WAIT"

            try:
                if 'process' in locals() and process.poll() is None:
                    # Завершаем весь процесс и его потомков
                    subprocess.run(f"taskkill /F /T /PID {process.pid}",
                                  shell=True,
                                  capture_output=True,
                                  timeout=10)
            except Exception as e:
                error_msg += f"\nERROR TASKKILL: {e}"

            # Возвращаем все ошибки
            return error_msg

        except FileNotFoundError as e:
            return f'ERROR: COMMAND NOT FOUND. {e}'
        except Exception as e:
            return f'ERROR: UNEXPECTED ERROR. {e}'

    @staticmethod
    def check_processes(target_name: str) -> None:
        current_pid = getpid()

        # Перебираем все запущенные процессы
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Проверяем имя процесса и исключаем текущий процесс
                if proc.info['name'].lower() == target_name.lower() and proc.info['pid'] != current_pid:
                    print("Программа уже запущена! Завершаем текущий экземпляр.")
                    exit(0)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Игнорируем процессы, к которым нет доступа
                continue

        # Основной код программы
        print("Программа запущена. Это первый экземпляр.")
