# Библиотека для получения пути к файлу
from Command_worker import CommandWorker

# import sys
from sys import exit


# Класс для работы с файлами
class FileHelper:
    @classmethod
    def __init__(cls):
        cls.file_log_path = CommandWorker.get_path("filepaths_ch.txt")
        cls.file_work_path = CommandWorker.get_path("work_log_ch.txt")
        cls.pass_7z = CommandWorker.get_path("passwordFor7zip_ch.txt")

    # Функция чтения 'логового' файла
    @classmethod
    def log_file(cls) -> (str, list):
        paths = []
        # Путь, где находиться скрипт
        try:
            # Получаем данные с файла
            f = open(cls.file_log_path, 'r')
            name_comp = f.readline()  # Получаем имя компа
            for line in f:  # Получаем пути к файлам
                paths.append(line)

            if name_comp and paths:
                return name_comp, paths
            else:
                FileHelper.work_file('Less than two lines in a file "filepaths_ch.txt".\n1-computer name; 2, 3, 4,... - path (-s) to file', error=True)
                exit(1)
        except (FileNotFoundError, ValueError):
            # Если файла нет, сохраняем ошибку, что его не было и мы его создали
            FileHelper.work_file('File "filepaths_ch.txt" does not exist.\nThe script created the file "filepaths_ch.txt".', error=True)
            # Создаём файл для записи
            with open(cls.file_log_path, 'w') as m_f:
                m_f.write('')
            # На случай создаём все нужные файлы
            cls.passwordFor7zip_ch()
            # Выходим из программы при ошибке
            exit(1)

    # Функция для записи информации в файл
    @classmethod
    def work_file(cls, text: str, error: bool = False):
        if error:
            text = 'ERROR:\n' + text
        # Открываем файл для записи
        with open(cls.file_work_path, 'a') as f:
            f.write(text)
            f.write('\n')

    # Функция для получения данных о 7_zip (путь к 7_zip и пароль)
    @classmethod
    def passwordFor7zip_ch(cls) -> (str, str):
        try:
            # Получаем данные
            with open(cls.pass_7z, 'r') as file:
                data = []
                for string in file:
                    data.append(string.replace('\n', ''))
            # Проверяем что с данными всё ОК
            if len(data) == 2:
                return data[0], data[1]
            else:
                # Не хватает данных, пишем как вводить их
                cls.work_file('ERROR in "passwordFor7zip_ch.txt": There is not enough data in the file.\nLine 1 is the path to 7_zip, line 2 is the password for the archive.', error=True)
                # Выходим из программы при ошибке
                exit(1)
        except (FileNotFoundError, ValueError):
            # Нет файла, выводим информацию о том что должно быть в файле и создаём файл
            cls.work_file('ERROR in "passwordFor7zip_ch.txt": There is no file. Line 1 is the path to 7_zip, line 2 is the password for the archive. The file was created under the name "passwordFor7zip_ch.txt".', error=True)
            with open(cls.pass_7z, 'w') as f:
                f.write('')
            # Выходим из программы при ошибке
            exit(1)
