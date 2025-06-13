""" Скачиваем библиотеки """
from datetime import date, timedelta
# Скачиваем дополнительные файлы
from File_helper import FileHelper
from Command_worker import CommandWorker
from Error_feedback import *


''' Функции '''
def get_dates():
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%d.%m.%Y")
    yesterday_str = yesterday.strftime("%d.%m.%Y")
    return [today_str, yesterday_str]


''' Основная программа '''
while True:
    '''Переменные для программы '''
    data_info = {'name': ['bytes', 'date']}  # Пример
    error_log = []
    files = FileHelper()  # Класс для быстрой работы с файлами

    ''' Считываем данные с файла '''
    name_comp, paths = files.log_file()

    ''' Получаем командой информацию о файлах в пути через dir '''
    for path in paths:
        answer_cmd = CommandWorker.command_get('dir ' + path).split()  # Получаем ответ от cmd
        curr_date, prev_date = get_dates()  # Получаем сегодняшнюю и вчерашнюю дату
        # Находим все файлы и их информацию
        for ind, word in enumerate(answer_cmd[:len(answer_cmd) - 3]):
            # Проверяем данные по памяти
            # Проверяем, что файл сегодняшний
            if word == curr_date:
                # Добавляем имя файла и информацию о нём по дате
                name = answer_cmd[ind + 3]
                if name not in ['.', '..', '...']:
                    bytes = answer_cmd[ind + 2]
                    data_info[name] = [bytes, curr_date]
            elif word == prev_date:
                # Проверяем что вдруг этот файл уже есть, но 'свежий'
                name = answer_cmd[ind + 3]
                if name not in ['.', '..', '...'] and not data_info.get(name):
                    bytes = answer_cmd[ind + 2]
                    data_info[name] = [bytes, prev_date]

        # Проверяем что есть файл и его память норм, иначе выдаём ошибку что копии нет или файл слишком маленький
        if len(data_info) < 2:
            error_log = ['There are no files for today or tomorrow.']

        # Проверяем что файл не битый

        # Выдаём ошибки, если они есть
        if error_log:
            pass  # Кидаем в Error_feedback (comp_name)
        # Вычисляем дату следующей проверки (замедление работы кода при ожидании, вдруг есть)

        print(data_info)

    exit()
