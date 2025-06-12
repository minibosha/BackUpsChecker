""" Скачиваем библиотеки """
import os
import subprocess
import time
import sys
# Скачиваем дополнительные файлы
import File_helper
import Mail_sender
import Tg_sender
from Command_worker import CommandWorker


''' Основная программа '''
while True:
    '''Переменные для программы '''
    error_log = []
    name_comp = ''
    paths = []

    ''' Считываем данные с файла и создаём его, если файла нет '''
    # Путь, где находиться скрипт
    file_path = CommandWorker.get_path("filepaths_ch.txt")
    try:
        # Получаем данные с файла
        f = open(file_path, 'r')
        name_comp = f.readline()
        for line in f:
            paths.append(line)
    except (FileNotFoundError, ValueError):
        # Если файла нет, сохраняем ошибку, что его не было и мы его создали
        with open(CommandWorker.get_path("work_log_ch.txt"), 'w') as er_f:
            er_f.write('File "filepaths_ch.txt" does not exist.\nScript make the file ""filepaths_ch.txt"".')
        with open(file_path, 'w') as m_f:
            m_f.write('')
        # Выходим из программы при ошибке
        sys.exit(1)


