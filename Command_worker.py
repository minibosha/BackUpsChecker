# Библиотека для ОС
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
# import os
from os import path

import psutil


# import sys


class CommandWorker:
    # Получение пути к файлу кода (папка скрипта) и добавление его имени
    @staticmethod
    def get_path(name: str) -> str:
        return path.abspath(name)

    # Отправка и возврат ответа от командной строки
    @staticmethod
    def command_get(command: str) -> str:
        timeout_seconds = 5400  # 90 минут = 5400 секунд

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


class AsyncCommandWorker:
    def __init__(self, max_workers: int = 4):
        # Потоки для асинхронного выполнения команд
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def command_get_async(self, command: str, timeout: int = 5400) -> str:
        # Асинхронно выполняет команду с возможностью задать таймаут
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._execute_sync, command, timeout)

    def _execute_sync(self, command: str, timeout: int = 5400) -> str:
        # Синхронное выполнение команды (используется внутри command_get_async)
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='CP866',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            stdout, _ = process.communicate(timeout=timeout)
            if process.returncode != 0:
                return f'ERROR: COMMAND FAILED WITH CODE {process.returncode}.\nOutput: {stdout}'
            return stdout
        except subprocess.TimeoutExpired:
            error_msg = f"TIME ERROR: command {command} TOO MUCH TIME TO WAIT ({timeout} sec)"
            try:
                if 'process' in locals():
                    # Завершаем процесс и всех его потомков
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except:
                            pass
                    parent.kill()
                    process.wait(timeout=5)
            except Exception as e:
                error_msg += f"\nERROR TASKKILL: {e}"
            return error_msg
        except FileNotFoundError as e:
            return f'ERROR: COMMAND NOT FOUND. {e}'
        except Exception as e:
            return f'ERROR: {e}'
