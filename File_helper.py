# Библиотека для получения пути к файлу
import shlex  # Для разбора строк с флагами
# import sys
from sys import exit

from Command_worker import CommandWorker


# Класс для работы с файлами
class FileHelper:
    @classmethod
    def __init__(cls):
        cls.file_log_path = CommandWorker.get_path("filepaths_ch.txt")
        cls.file_work_path = CommandWorker.get_path("work_log_ch.txt")
        cls.pass_7z = CommandWorker.get_path("passwordFor7zip_ch.txt")

    # Читает filepaths_ch.txt
    @classmethod
    def log_file(cls) -> (str, list, list, list, list):
        paths = []
        names_to_paths = []
        global_flags_list = []
        file_flags_list = []

        try:
            with open(cls.file_log_path, 'r', encoding='utf-8-sig') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

                if len(lines) < 1:
                    cls.work_file(
                        'File "filepaths_ch.txt" is empty.\nRequired format:\ncomputer_name\npath1\nname1\npath2\nname2\n...',
                        error=True)
                    exit(1)

                name_comp = lines[0]  # первая строка – имя компьютера

                i = 1
                while i < len(lines):
                    #  Чтение пути
                    path_line = lines[i]
                    if not path_line:
                        i += 1
                        continue
                    paths.append(path_line)

                    #  Чтение имени бэкапа
                    if i + 1 < len(lines):
                        name_line = lines[i + 1]
                        names_to_paths.append(name_line if name_line else None)
                        i += 2
                    else:
                        names_to_paths.append(None)
                        i += 1

                    #  Сбор флагов для этого пути (может быть несколько строк)
                    global_flags = {}
                    file_flags = {}

                    while i < len(lines) and lines[i].startswith('-'):
                        flag_line = lines[i]
                        i += 1

                        # Файловый флаг: --file=имя_файла остальные_флаги
                        if flag_line.startswith('--file=') or flag_line.startswith('-f='):
                            try:
                                # Разбираем всю строку через shlex, чтобы корректно обработать кавычки
                                parts = shlex.split(flag_line)
                                file_part = parts[0]  # --file=имя или -f=имя
                                if '=' in file_part:
                                    eq_pos = file_part.find('=')
                                    file_name = file_part[eq_pos + 1:].strip()
                                    file_specific = {}
                                    # Остальные элементы — флаги для этого файла
                                    for part in parts[1:]:
                                        if '=' in part:
                                            k, v = part.split('=', 1)
                                            k = k.lstrip('-').replace('-', '_')
                                            file_specific[k] = v
                                        elif part.startswith('--'):
                                            k = part[2:].replace('-', '_')
                                            file_specific[k] = True
                                        elif part.startswith('-') and len(part) > 1:
                                            k = part[1:].replace('-', '_')
                                            file_specific[k] = True
                                    file_flags[file_name] = file_specific
                                else:
                                    cls.work_file(f'ERROR in file flag format: {flag_line}', error=True)
                            except Exception as e:
                                cls.work_file(f'ERROR in parsing flags for file: {flag_line[:50]}... {e}', error=True)
                        else:
                            # Глобальные флаги (без --file=)
                            try:
                                parts = shlex.split(flag_line)
                                for part in parts:
                                    if '=' in part:
                                        k, v = part.split('=', 1)
                                        k = k.lstrip('-').replace('-', '_')
                                        global_flags[k] = v
                                    elif part.startswith('--'):
                                        k = part[2:].replace('-', '_')
                                        global_flags[k] = True
                                    elif part.startswith('-') and len(part) > 1:
                                        k = part[1:].replace('-', '_')
                                        global_flags[k] = True
                            except Exception as e:
                                cls.work_file(f'ERROR in parsing global flags "{flag_line}": {e}', error=True)

                    # Сохраняем собранные флаги для этого пути
                    global_flags_list.append(global_flags)
                    file_flags_list.append(file_flags)

                # Добиваем списки до одинаковой длины (на случай отсутствия флагов)
                while len(names_to_paths) < len(paths):
                    names_to_paths.append(None)
                while len(global_flags_list) < len(paths):
                    global_flags_list.append({})
                while len(file_flags_list) < len(paths):
                    file_flags_list.append({})

                if name_comp and paths:
                    return name_comp, paths, names_to_paths, global_flags_list, file_flags_list
                else:
                    cls.work_file(
                        'ERROR: Less than two lines in a file "filepaths_ch.txt".\nRequired format:\ncomputer_name\npath1\nname_to_path1\npath2\nname_to_path2\n...',
                        error=True)
                    exit(1)

        except (FileNotFoundError, ValueError, IndexError) as e:
            cls.work_file(f'ERROR in "filepaths_ch.txt": {type(e).__name__}: {e}', error=True)
            cls.work_file('The script created the file "filepaths_ch.txt". Fill it and restart.', error=True)
            with open(cls.file_log_path, 'w', encoding='utf-8-sig') as m_f:
                m_f.write('COMPUTER_NAME\n')
                m_f.write('C:\\backup\\path1\n')
                m_f.write('backup_name_1\n')
                m_f.write('D:\\data\\path2\n')
                m_f.write('data_backup_2\n')
                m_f.write('...')
            cls.passwordFor7zip_ch()
            exit(1)

    @classmethod
    def work_file(cls, text: str, error: bool = False):
        # Запись в лог-файл (work_log_ch.txt)
        if error:
            text = 'ERROR:\n' + text
        with open(cls.file_work_path, 'a', encoding='utf-8-sig') as f:
            f.write(text + '\n')

    @classmethod
    def passwordFor7zip_ch(cls) -> (str, str):
        # Чтение пути к 7z и пароля
        try:
            with open(cls.pass_7z, 'r', encoding='utf-8-sig') as file:
                data = [line.strip() for line in file if line.strip()]
            if len(data) == 2:
                return data[0], data[1]
            else:
                cls.work_file(
                    'ERROR in "passwordFor7zip_ch.txt": There is not enough data in the file.\nLine 1 is the path to 7_zip, line 2 is the password for the archive.',
                    error=True)
                exit(1)
        except (FileNotFoundError, ValueError):
            cls.work_file(
                'ERROR in "passwordFor7zip_ch.txt": There is no file. Line 1 is the path to 7_zip, line 2 is the password for the archive. The file was created under the name "passwordFor7zip_ch.txt".',
                error=True)
            with open(cls.pass_7z, 'w', encoding='utf-8-sig') as f:
                f.write('C:\\Program Files\\7-Zip\\7z.exe\n')
                f.write('password')
            exit(1)
