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
            if word == curr_date:
                # Добавляем имя файла и информацию о нём
                name = answer_cmd[ind + 3]
                if name not in ['.', '..', '...']:
                    bytes = answer_cmd[ind + 2]
                    data_info[name] = [bytes, curr_date]
            elif word == prev_date:
                name = answer_cmd[ind + 3]
                if name not in ['.', '..', '...'] and not data_info.get(name):
                    bytes = answer_cmd[ind + 2]
                    data_info[name] = [bytes, prev_date]
            else:
                pass  # error

        print(data_info, answer_cmd)
    exit()
