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
    data_info = {}  # {'name': ['bytes', 'date']}
    error_log = []
    files = FileHelper()  # Класс для быстрой работы с файлами

    ''' Считываем данные с файла '''
    name_comp, paths = files.log_file()

    ''' Получаем командой информацию о файлах в пути через dir '''
    for path in paths:
        answer_cmd = CommandWorker.command_get('dir ' + path).split()  # Получаем ответ от cmd
        print(answer_cmd)
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
            error_log = ['There are no files for today or tomorrow.']
        for key, obj in data_info.items():
            if obj[1] == curr_date or obj[1] == prev_date:
                if obj[0] > 5242880:
                    break  # Лог, что с этим файлом всё ок
                else:
                    print('error', key, obj)
                    pass  # ОШИБКА, файл меньше нормы

        # Проверяем что файл не битый

        # Выдаём ошибки, если они есть
        if error_log:
            pass  # Кидаем в Error_feedback (comp_name)
        # Вычисляем дату следующей проверки (замедление работы кода при ожидании, вдруг есть)

        print(data_info)

    exit()
