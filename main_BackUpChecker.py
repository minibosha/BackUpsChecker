""" Скачиваем библиотеки """
import datetime
import os
import time

from Command_worker import CommandWorker
from Error_feedback import ErrorFeedback
# Скачиваем дополнительные файлы
from File_helper import FileHelper


''' Функции '''


# Получаем нынешнюю и вчерашнюю дату
def get_dates():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    today_str = today.strftime("%d.%m.%Y")
    yesterday_str = yesterday.strftime("%d.%m.%Y")
    return [today_str, yesterday_str]


# Загружает время следующего выполнения из файла
def load_next_run_time():
    if not os.path.exists(CHECK_TIME_FILE):
        return None
    try:
        with open(CHECK_TIME_FILE, "r", encoding="utf-8") as file:
            return datetime.datetime.fromisoformat(file.read().strip())
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


''' Основная программа '''


def main_program():
    # Программные переменные
    data_info = {}  # {'name': ['bytes', 'date']}
    error_log = []
    files = FileHelper()  # Класс для быстрой работы с файлами
    path_to_7_zip, password_7_zip = files.passwordFor7zip_ch()

    ''' Считываем данные с файла '''
    name_comp, paths = files.log_file()

    ''' Получаем командой информацию о файлах в пути через dir '''
    for path in paths:
        today_file: bool = False
        answer_cmd = CommandWorker.command_get('dir ' + path).split()  # Получаем ответ от cmd
        curr_date, prev_date = get_dates()  # Получаем сегодняшнюю и вчерашнюю дату
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
                while answer_cmd[ind + ind_for_int].isdigit():
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
                    if '.' not in name:
                        ind_for_int += 1
                        while '.' not in name:
                            if ind + ind_for_int >= len(answer_cmd):
                                name = answer_cmd[ind + ind_for_int]
                                break
                            name += ' '
                            name += answer_cmd[ind + ind_for_int]
                            ind_for_int += 1
                    # Сохраняем результат
                    if name and bytes and name not in ['.', '..', '...', '<DIR>']:
                        data_info[name] = [bytes, curr_date]
                        today_file = True
            elif word == prev_date:
                # Переменные нужные для программы
                bytes = 0
                name = ''
                # Считываем кол-во бит в файле
                ind_for_int = 2
                dig_of_num = []
                while answer_cmd[ind + ind_for_int].isdigit():
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
                    if '.' not in name:
                        ind_for_int += 1
                        while '.' not in name:
                            if ind + ind_for_int >= len(answer_cmd):
                                name = answer_cmd[ind + ind_for_int]
                                break
                            name += ' '
                            name += answer_cmd[ind + ind_for_int]
                            ind_for_int += 1
                    # Сохраняем результат
                    if name and bytes and name not in ['.', '..', '...', '<DIR>'] and not data_info.get(name):
                        data_info[name] = [bytes, prev_date]

        # Проверяем что есть файл и его память норм, иначе выдаём ошибку что копии нет или файл слишком маленький
        if len(data_info) < 1:
            error_log.append(f'There are no files for today or tomorrow in path {path}.')
        else:
            for key, obj in data_info.items():
                if obj[1] == curr_date or obj[1] == prev_date and not today_file:
                    if obj[0] > 5242880:
                        files.work_file(
                            f'{curr_date} check: The {key} file occupies {obj[0]} bytes of memory and its creation date is {obj[1]}.')  # Лог, что с этим файлом всё ок
                    else:
                        er_txt = f'{curr_date} ERROR: The {key} file occupies {obj[0]} bytes of memory (<5Mb) and its creation date is {obj[1]}.'
                        files.work_file(er_txt, error=True)
                        error_log.append(er_txt)

        # Проверяем что файл не битый через 7_zip
        try:
            for data_name in data_info.keys():
                path_to_file_name = os.path.join(path, data_name)
                command_for_7Zip = f'"{path_to_7_zip}" t -p"{password_7_zip}" "{path_to_file_name}"'
                answer_7Zip = CommandWorker.command_get(command_for_7Zip)
                if 'Everything is Ok' in answer_7Zip:
                    files.work_file(f'7Zip, {path_to_file_name} - Everything is Ok')
                else:
                    error_log.append(answer_7Zip)
        except Exception as e:
            files.work_file(f'UNKNOWN ERROR: {e}', error=True)

    # Выдаём ошибки, если они есть
    if error_log:
        errors = ErrorFeedback(name_comp, error_log)
        errors.send_error()


''' Проверка и запуск программы по времени '''
# Конфигурационные константы
CHECK_TIME_FILE = os.path.abspath("checkTimeForBC.txt")
CHECK_INTERVAL_HOURS = 24
MAX_SLEEP_SECONDS = 3600  # 1 час
file = FileHelper()

"""Основной цикл выполнения программы"""
next_run = load_next_run_time()

# Если время не загружено, выполняем задачу сразу
if next_run is None:
    file.work_file("Первоначальный запуск программы")
    main_program()
    next_run = datetime.datetime.now() + datetime.timedelta(hours=CHECK_INTERVAL_HOURS)
    save_next_run_time(next_run)

file.work_file(f"Следующее выполнение запланировано на: {next_run}")

while True:
    current_time = datetime.datetime.now()

    # Проверяем, настало ли время выполнения
    if current_time >= next_run:
        main_program()  # Выполнение основной программы.

        # Планируем следующее выполнение
        next_run = next_run + datetime.timedelta(hours=CHECK_INTERVAL_HOURS)
        save_next_run_time(next_run)
        file.work_file(f"Следующее выполнение запланировано на: {next_run}")

    # Рассчитываем время до следующей проверки
    seconds_until_next = (next_run - current_time).total_seconds()
    sleep_time = min(seconds_until_next, MAX_SLEEP_SECONDS)

    if sleep_time > 0:
        # Спим
        time.sleep(sleep_time)
