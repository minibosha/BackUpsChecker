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
    def log_file(cls) -> (str, list, list):
        paths = []
        names_to_paths = []

        # Путь, где находиться скрипт
        try:
            # Получаем данные с файла
            with open(cls.file_log_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

                if len(lines) < 1:
                    FileHelper.work_file(
                        'File "filepaths_ch.txt" is empty.\nRequired format:\ncomputer_name\npath1\nname1\npath2\nname2\n...',
                        error=True)
                    exit(1)

                name_comp = lines[0]  # Первая строка - имя компа

                # Обрабатываем пары путь-название
                i = 1
                while i < len(lines):
                    # Добавляем путь (все нечетные позиции относительно начала файла)
                    if i < len(lines):
                        path_line = lines[i]
                        if path_line:  # Если путь не пустой
                            paths.append(path_line)

                    # Проверяем, есть ли название для этого пути
                    if i + 1 < len(lines):
                        name_line = lines[i + 1]
                        if name_line:  # Если название не пустое
                            names_to_paths.append(name_line)
                        else:
                            names_to_paths.append(None)
                        i += 2  # Переходим к следующей паре
                    else:
                        # Если нет названия для последнего пути
                        names_to_paths.append(None)
                        i += 1  # Завершаем цикл

            # Убеждаемся, что списки одинаковой длины
            while len(names_to_paths) < len(paths):
                names_to_paths.append(None)

            # Проверяем только name_comp и paths, names_to_paths может содержать None
            if name_comp and paths:
                return name_comp, paths, names_to_paths
            else:
                FileHelper.work_file('Less than two lines in a file "filepaths_ch.txt".\nRequired format:\ncomputer_name\npath1\nname_to_path1\npath2\nname_to_path2\n...', error=True)
                exit(1)
        except (FileNotFoundError, ValueError, IndexError):
            # Если файла нет, сохраняем ошибку, что его не было и мы его создали
            FileHelper.work_file('File "filepaths_ch.txt" does not exist.\nThe script created the file "filepaths_ch.txt".', error=True)
            # Создаём файл для записи
            with open(cls.file_log_path, 'w', encoding='utf-8') as m_f:
                m_f.write('COMPUTER_NAME\n')
                m_f.write('C:\\backup\\path1\n')
                m_f.write('backup_name_1\n')
                m_f.write('D:\\data\\path2\n')
                m_f.write('data_backup_2\n')
                m_f.write('...')
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
                f.write('Path to 7Zip/n')
                f.write('Password for archives')
            # Выходим из программы при ошибке
            exit(1)
