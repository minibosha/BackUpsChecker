""" Скачиваем библиотеки """
import asyncio
# import datetime
from datetime import date, timedelta, datetime
# import os
from os import path
# import time
from time import sleep

# Скачиваем дополнительные файлы
from Command_worker import CommandWorker, AsyncCommandWorker
from Error_feedback import ErrorFeedback
from File_helper import FileHelper

# import sys

''' Функции '''


# Ограничение числа в диапазоне
def constrain(n: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(n, max_val))


# Получаем нынешнюю и вчерашнюю дату
def get_dates():
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%d.%m.%Y")
    yesterday_str = yesterday.strftime("%d.%m.%Y")
    return [today_str, yesterday_str]


# Загружает время следующего выполнения из файла
def load_next_run_time():
    if not path.exists(CHECK_TIME_FILE):
        return None
    try:
        with open(CHECK_TIME_FILE, "r", encoding="utf-8") as file:
            return datetime.fromisoformat(file.read().strip())
    except (ValueError, OSError) as error:
        FileHelper().work_file(f"Ошибка чтения файла: {error}")
        return None


# Сохраняет время следующего выполнения в файл
def save_next_run_time(next_run):
    try:
        with open(CHECK_TIME_FILE, "w", encoding="utf-8") as file:
            file.write(next_run.isoformat())
    except OSError as error:
        FileHelper().work_file(f"Ошибка записи в файл: {error}")


''' Ассинхронные функции '''


async def check_single_file_async(
        data_name: str,
        obj: tuple,
        path_curr: str,
        curr_date: str,
        prev_date: str,
        today_file: bool,
        password_7_zip: str,
        path_to_7_zip: str,
        files,
        command_worker: AsyncCommandWorker,
        semaphore: asyncio.Semaphore) -> tuple:
    """
    Асинхронная версия проверки одного файла
    Возвращает: (success, data_name, result) или (False, data_name, error)
    """
    async with semaphore:  # Ограничиваем параллелизм
        try:
            # Проверяем актуальность файла (ваша существующая логика)
            if obj[1] == curr_date or (obj[1] == prev_date and not today_file):
                path_to_file_name = path.join(path_curr, data_name)
                extension = data_name.split(".")[-1].lower()

                # 7zip файлы
                if extension in ["zip", "rar", "gz", "7z"]:
                    command = f'"{path_to_7_zip}" t -p"{password_7_zip}" "{path_to_file_name}"'
                    result = await command_worker.command_get_async(command)
                    if 'Everything is Ok' in result:
                        files.work_file(f'7Zip, {path_to_file_name} - Everything is Ok')
                        return (True, data_name, result)
                    else:
                        return (False, data_name, result)

                # Acronis файлы
                elif extension in ["tib", "tibx", "TIB", "TIBX"]:
                    command = f'acrocmd validate backup --loc={path_curr} --arc={data_name}'
                    result = await command_worker.command_get_async(command)
                    if 'completed successfully' in result or 'завершено успешно' in result:
                        files.work_file(f'acronis, {path_to_file_name} - Everything is Ok')
                        return (True, data_name, result)
                    else:
                        return (False, data_name, result)

                # Macrium Reflect файлы
                elif extension in ["mrimg", "mrbakx"]:
                    command = f'"C:\\Program Files\\Macrium\\Reflect\\mrverify.exe" "{path_to_file_name}" --password "{password_7_zip}"'
                    result = await command_worker.command_get_async(command)
                    if 'Verification succeeded' in result or 'Проверка прошла успешно' in result:
                        files.work_file(f'MR, {path_to_file_name} - Everything is Ok')
                        return (True, data_name, result)
                    else:
                        return (False, data_name, result)

            # Файл не актуален для проверки
            return (True, data_name, "File not relevant for today")

        except Exception as e:
            return (False, data_name, f"Error checking {data_name}: {str(e)}")


async def check_backup_files_async(
        data_info: dict,
        path_curr: str,
        curr_date: str,
        prev_date: str,
        today_file: bool,
        password_7_zip: str,
        path_to_7_zip: str,
        files,
        max_concurrent: int = 4) -> list:
    """
    Асинхронная проверка всех файлов с ограничением параллелизма через семафор
    Возвращает: error_log (список ошибок)
    """
    error_log = []

    # Создаем семафор для ограничения параллелизма
    semaphore = asyncio.Semaphore(max_concurrent)
    command_worker = AsyncCommandWorker(max_workers=max_concurrent)

    try:
        # Создаем задачи для всех файлов
        tasks = []
        for data_name, obj in data_info.items():
            task = check_single_file_async(
                data_name=data_name,
                obj=obj,
                path_curr=path_curr,
                curr_date=curr_date,
                prev_date=prev_date,
                today_file=today_file,
                password_7_zip=password_7_zip,
                path_to_7_zip=path_to_7_zip,
                files=files,
                command_worker=command_worker,
                semaphore=semaphore
            )
            tasks.append(task)

        # Ждем завершения ВСЕХ задач
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем результаты
        for result in results:
            if isinstance(result, Exception):
                # Обработка исключений из gather
                error_log.append(f"Task failed with exception: {str(result)}")
                continue

            success, data_name, result_text = result

            if not success and "File not relevant for today" not in result_text:
                error_log.append(result_text)

        return error_log
    finally:
        # Всегда освобождаем ресурсы
        command_worker.executor.shutdown(wait=True)


''' Основная программа '''


def main_program():
    # Программные переменные
    data_info = {}  # {'name': ['bytes', 'date']}
    error_log = []
    name_paths_error_log = []
    files = FileHelper()  # Класс для быстрой работы с файлами

    ''' Считываем данные с файлов '''
    name_comp, paths, names_to_paths = files.log_file()
    path_to_7_zip, password_7_zip = files.passwordFor7zip_ch()

    ''' Получаем командой информацию о файлах в пути через dir '''
    for ind_for_err_path, path_curr in enumerate(paths):
        data_info = {}  # Обнуляем информацию, чтобы не было ошибок с одинаковым названием файлов

        today_file: bool = False
        answer_cmd = CommandWorker.command_get('dir ' + path_curr).split()  # Получаем ответ от cmd
        curr_date, prev_date = get_dates()  # Получаем сегодняшнюю и вчерашнюю дату
        # Проверяем что у нас хватает информации
        if len(answer_cmd) < 3:
            error_log.append(f"ERROR ANSWER CMD (DIR): {answer_cmd}")
            name_paths_error_log.append(names_to_paths[ind_for_err_path])
            continue
        # Находим все файлы и их информацию
        for ind, word in enumerate(answer_cmd[:len(answer_cmd) - 3]):
            # Проверяем данные по памяти
            # Проверяем, что файл сегодняшний
            if word == curr_date:
                # Переменные нужные для программы
                bytes = 0
                name = ''
                # Считываем кол-во бит в файле
                ind_for_int = 2
                dig_of_num = []
                while ind + ind_for_int < len(answer_cmd) and answer_cmd[ind + ind_for_int].isdigit():
                    try:
                        dig_of_num.append(int(answer_cmd[ind + ind_for_int]))
                        ind_for_int += 1
                    except ValueError:
                        break
                else:
                    # Перемножаем разряды бит
                    for i in range(len(dig_of_num)):
                        bytes += dig_of_num[::-1][i] * (1000 ** i)  # Возводим в степень 1000 по индексу
                    # Получаем имя программы
                    name = answer_cmd[ind + ind_for_int]
                    if '.' not in name and ind + ind_for_int + 1 < len(answer_cmd):
                        ind_for_int += 1
                        # Ограничиваем результат на случай
                        ind_for_int = ind_for_int = constrain(ind_for_int, 2, len(answer_cmd) - ind - 1)

                        while '.' not in name and ind + ind_for_int < len(answer_cmd):
                            name += ' ' + answer_cmd[ind + ind_for_int]
                            ind_for_int += 1
                    # Сохраняем результат
                    if name and bytes and name not in ['.', '..', '...', '<DIR>'] and name.split(".")[-1] != "xml":
                        data_info[name] = [bytes, curr_date]
                        today_file = True
            elif word == prev_date:
                # Переменные нужные для программы
                bytes = 0
                name = ''
                # Считываем кол-во бит в файле
                ind_for_int = 2
                dig_of_num = []
                while ind + ind_for_int < len(answer_cmd) and answer_cmd[ind + ind_for_int].isdigit():
                    try:
                        dig_of_num.append(int(answer_cmd[ind + ind_for_int]))
                        ind_for_int += 1
                    except ValueError:
                        break
                else:
                    # Перемножаем разряды бит
                    for i in range(len(dig_of_num)):
                        bytes += dig_of_num[::-1][i] * (1000 ** i)  # Возводим в степень 1000 по индексу
                    # Получаем имя программы
                    name = answer_cmd[ind + ind_for_int]
                    if '.' not in name and ind + ind_for_int + 1 < len(answer_cmd):
                        ind_for_int += 1
                        # Ограничиваем результат на случай
                        ind_for_int = ind_for_int = constrain(ind_for_int, 2, len(answer_cmd) - ind - 1)

                        while '.' not in name and ind + ind_for_int < len(answer_cmd):
                            name += ' ' + answer_cmd[ind + ind_for_int]
                            ind_for_int += 1
                    # Сохраняем результат
                    if name and bytes and name not in ['.', '..', '...', '<DIR>'] and name.split(".")[
                        -1] != "xml" and not data_info.get(name):
                        data_info[name] = [bytes, prev_date]

        # Проверяем что есть файл и его память норм, иначе выдаём ошибку что копии нет или файл слишком маленький
        if len(data_info) < 1:
            error_log.append(f'There are no files for today or tomorrow in path {path_curr}.')
            name_paths_error_log.append(names_to_paths[ind_for_err_path])
        else:
            for key, obj in data_info.items():
                if obj[1] == curr_date or (obj[1] == prev_date and not today_file):
                    if obj[0] > 5242880:
                        files.work_file(
                            f'{curr_date} check: The {key} file occupies {obj[0]} bytes of memory and its creation date is {obj[1]}.')  # Лог, что с этим файлом всё ок
                    else:
                        er_txt = f'{curr_date} ERROR: The {key} file occupies {obj[0]} bytes of memory (<5Mb) and its creation date is {obj[1]}.'
                        files.work_file(er_txt, error=True)
                        error_log.append(er_txt)
                        name_paths_error_log.append(names_to_paths[ind_for_err_path])

        # Проверяем что файл не битый через 7_zip, macrimum reflect или акронис
        error_log_ans = []
        try:
            error_log_ans = asyncio.run(check_backup_files_async(
                data_info=data_info,
                path_curr=path_curr,
                curr_date=curr_date,
                prev_date=prev_date,
                today_file=today_file,
                password_7_zip=password_7_zip,
                path_to_7_zip=path_to_7_zip,
                files=files,
                max_concurrent=4))  # Максимум 4 файла одновременно

            # Добавляем ошибки файлов
            if error_log_ans:
                error_log.extend(error_log_ans)
                name_paths_error_log.append(names_to_paths[ind_for_err_path])
        except Exception as e:
            files.work_file(f'UNKNOWN ERROR: {e}', error=True)
            error_log.append(e)
            name_paths_error_log.append(names_to_paths[ind_for_err_path])

    # Выдаём ошибки, если они есть
    # Парсим данные
    error_log = list(filter(bool, error_log))
    # Проверяем что массив не пустой
    if error_log:
        errors = ErrorFeedback(name_comp, error_log, name_paths_error_log)
        errors.send_error()


''' Проверка и запуск программы по времени '''
# Конфигурационные константы
CHECK_TIME_FILE = path.abspath("checkTimeForBC.txt")
CHECK_INTERVAL_HOURS = 24
MAX_SLEEP_SECONDS = 3600  # 1 час
file = FileHelper()

''' Проверка, что это первый запуск программы '''
file.work_file("Программа запущена!")

"""Основной цикл выполнения программы"""
next_run = load_next_run_time()

# Если время не загружено, выполняем задачу сразу
if next_run is None:
    file.work_file("Первоначальный запуск программы")
    main_program()
    next_run = datetime.now() + timedelta(hours=CHECK_INTERVAL_HOURS)
    save_next_run_time(next_run)

    file.work_file(f"Следующее выполнение запланировано на: {next_run}")

while True:
    current_time = datetime.now()

    # Проверяем, настало ли время выполнения
    if current_time >= next_run:
        main_program()  # Выполнение основной программы.

        # Планируем следующее выполнение
        next_run = datetime.now()
        next_run = next_run + timedelta(hours=CHECK_INTERVAL_HOURS)
        save_next_run_time(next_run)
        file.work_file(f"Следующее выполнение запланировано на: {next_run}")

    # Рассчитываем время до следующей проверки
    seconds_until_next = (next_run - current_time).total_seconds()
    sleep_time = min(seconds_until_next, MAX_SLEEP_SECONDS)

    if sleep_time > 0:
        # Спим
        sleep(sleep_time)
