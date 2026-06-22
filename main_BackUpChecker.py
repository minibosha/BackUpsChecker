""" Скачиваем библиотеки """
import asyncio
# import atexit
from atexit import register
# import datetime
from datetime import date, timedelta, datetime
# import os
from os import path, scandir, getpid, remove, SEEK_END
# import sys
from sys import exit
# import time
from time import sleep

# import psutil
from psutil import pid_exists

# Скачиваем дополнительные файлы
from Command_worker import CommandWorker, AsyncCommandWorker
from Error_feedback import ErrorFeedback
from File_helper import FileHelper

''' Функции '''


# Проверяет размер файла лога. Если он превышает max_size_kb КБ,
def trim_log_file_if_needed(log_path, max_size_kb=100, trim_size_kb=75):
    if not path.exists(log_path):
        return
    file_size = path.getsize(log_path)
    max_bytes = max_size_kb * 1024
    if file_size <= max_bytes:
        return
    trim_bytes = trim_size_kb * 1024
    try:
        with open(log_path, 'r', encoding='utf-8-sig') as f:
            # Перемещаем указатель на trim_bytes (примерно) и читаем оставшуюся часть
            f.seek(0, SEEK_END)
            total_size = f.tell()
            if total_size > trim_bytes:
                f.seek(trim_bytes)
            else:
                f.seek(0)
            data = f.read()
        with open(log_path, 'w', encoding='utf-8-sig') as f:
            f.write(data)
    except Exception as e:
        # Если что-то пошло не так, просто логируем ошибку
        FileHelper().work_file(f"ERROR trimming log file: {e}", error=True)


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
        with open(CHECK_TIME_FILE, "r", encoding="utf-8-sig") as file:
            time_str = file.read().strip()
            # Пробуем разные форматы (с пробелом или T, с секундами или без)
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            FileHelper().work_file(f"ERROR parsing time: {time_str}", error=True)
            return None
    except (ValueError, OSError) as error:
        FileHelper().work_file(f"ERROR reading time file: {error}", error=True)
        return None


# Сохраняет время следующего выполнения в файл
def save_next_run_time(next_run):
    # Сохраняем время без секунд и микросекунд
    next_run_clean = next_run.replace(second=0, microsecond=0)
    try:
        with open(CHECK_TIME_FILE, "w", encoding="utf-8-sig") as file:
            file.write(next_run_clean.strftime("%Y-%m-%d %H:%M"))
    except OSError as error:
        FileHelper().work_file(f"ERROR writing time file: {error}", error=True)


def check_single_instance():
    """Проверяет, не запущена ли уже программа с обработкой PID"""
    lock_file = "program.lock"

    # Проверяем, существует ли файл блокировки
    if path.exists(lock_file):
        try:
            # Читаем PID из файла
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Проверяем, существует ли процесс с таким PID
            if pid_exists(old_pid):
                # Процесс всё ещё работает
                return False
            else:
                # Процесс завершился, но файл остался (аварийное завершение)
                remove(lock_file)
        except (ValueError, FileNotFoundError):
            # Файл повреждён или удалён, удаляем его
            try:
                remove(lock_file)
            except:
                pass

    # Создаём новый файл блокировки
    try:
        with open(lock_file, 'w') as f:
            f.write(str(getpid()))

        # Регистрируем удаление файла при нормальном завершении
        def cleanup():
            try:
                remove(lock_file)
            except:
                pass

        register(cleanup)
        return True

    except Exception:
        return False


''' Ассинхронные функции '''


# Простая асинхронная проверка одного файла
async def check_single_file_async(file_info, command_worker, semaphore):
    # Распаковываем данные
    (data_name, obj, path_curr, path_display_name,
     curr_date, prev_date, today_file,
     password_7_zip, path_to_7_zip, files, flags) = file_info

    # Флаг --skip (уже отфильтрован на предыдущем этапе, но на всякий случай)
    if flags.get('skip'):
        files.work_file(f'Skipping {data_name} (flag --skip)')
        return None, None

    # Таймаут из флага (по умолчанию 5400)
    timeout = int(flags.get('timeout', 5400))

    # Фильтрация по расширениям (повторно на случай, если файл не был отфильтрован ранее)
    extension = data_name.split(".")[-1].lower() if '.' in data_name else ''
    if 'ignore_extensions' in flags:
        ignored = [ext.strip().lower() for ext in flags['ignore_extensions'].split(',')]
        if extension in ignored:
            return None, None
    if 'extensions' in flags:
        allowed = [ext.strip().lower() for ext in flags['extensions'].split(',')]
        if extension not in allowed:
            return None, None

    # Таймаут из флага (по умолчанию 5400)
    timeout = int(flags.get('timeout', 5400))

    async with semaphore:
        try:
            # Проверка даты (если нет флага --force)
            if not flags.get('force'):
                if obj[1] != curr_date and not (obj[1] == prev_date and not today_file):
                    return None, None

            path_to_file_name = path.join(path_curr, data_name)
            extension = data_name.split(".")[-1].lower()

            # Пропускаем служебные файлы (CB*)
            check = True
            if len(data_name) >= 3:
                if data_name[:2] == "CB" or data_name[:3] in ["CB:", "CB.", "CB_"]:
                    check = False

            if check:
                #  Проверка 7-ZIP архивов
                if extension in ["zip", "rar", "gz", "7z"]:
                    command = f'"{path_to_7_zip}" t -p"{password_7_zip}" "{path_to_file_name}"'
                    result = await command_worker.command_get_async(command, timeout=timeout)
                    if 'Everything is Ok' in result:
                        files.work_file(f'7Zip, {path_to_file_name} - OK')
                        return None, None
                    # Флаг --ignore-errors: не возвращаем ошибку, только логируем
                    if flags.get('ignore_errors'):
                        files.work_file(f'7Zip error ignored: {result[:200]}...')
                        return None, None
                    return f"7Zip: {result}", path_display_name

                #  Проверка Acronis образов
                elif extension in ["tib", "tibx", "TIB", "TIBX"]:
                    command = f'acrocmd validate backup --loc={path_curr} --arc={data_name}'
                    result = await command_worker.command_get_async(command, timeout=timeout)
                    success_patterns = ['completed successfully', 'завершено успешно']
                    if any(pattern in result for pattern in success_patterns):
                        files.work_file(f'Acronis, {path_to_file_name} - OK')
                        return None, None
                    if flags.get('ignore_errors'):
                        files.work_file(f'Acronis error ignored: {result[:200]}...')
                        return None, None
                    return f"Acronis: {result}", path_display_name

                #  Проверка Macrium образов
                elif extension in ["mrimg", "mrbakx"]:
                    command = f'"C:\\Program Files\\Macrium\\Reflect\\mrverify.exe" "{path_to_file_name}" --password "{password_7_zip}"'
                    result = await command_worker.command_get_async(command, timeout=timeout)
                    success_patterns = ['Verification succeeded', 'Проверка прошла успешно']
                    if any(pattern in result for pattern in success_patterns):
                        files.work_file(f'Macrium, {path_to_file_name} - OK')
                        return None, None
                    if flags.get('ignore_errors'):
                        files.work_file(f'Macrium error ignored: {result[:200]}...')
                        return None, None
                    return f"Macrium: {result}", path_display_name

            return None, None

        except Exception as e:
            # Детальная запись об исключении
            import traceback
            tb = traceback.format_exc()
            files.work_file(f'Exception in {data_name}: {type(e).__name__}: {e}\n{tb}', error=True)
            return f"Exception: {type(e).__name__}: {e}", path_display_name


# Проверяет все файлы с ограничением в 4 одновременные задачи
async def check_all_files_async(file_tasks):
    semaphore = asyncio.Semaphore(4)
    command_worker = AsyncCommandWorker(max_workers=4)

    try:
        tasks = [check_single_file_async(file_info, command_worker, semaphore) for file_info in file_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        error_log = []
        path_log = []

        for result in results:
            if isinstance(result, Exception):
                error_log.append(f"Task error: {type(result).__name__}: {str(result)}")
                path_log.append("Unknown")
            elif result[0] is not None:
                error_log.append(result[0])
                path_log.append(result[1])

        return error_log, path_log
    finally:
        command_worker.executor.shutdown(wait=True)


''' Основная программа '''


def main_program():
    # Программные переменные
    data_info = {}  # {'name': ['bytes', 'date']}
    error_log = []
    name_paths_error_log = []
    files = FileHelper()  # Класс для быстрой работы с файлами
    async_tasks = []  # Класс для ассинхронной проверки всех файлов

    # Обрезаем лог-файл, если он слишком большой (один раз за запуск)
    trim_log_file_if_needed(files.file_work_path, 100, 75)

    ''' Считываем данные с файлов '''
    name_comp, paths, names_to_paths, global_flags_list, file_flags_list = files.log_file()
    path_to_7_zip, password_7_zip = files.passwordFor7zip_ch()

    ''' Считываем и парсим данные с Checked.txt'''
    files_to_check = set()
    checked = set()
    if not path.exists(path.abspath("checked.txt")):
        checked = set()
    else:
        with open(path.abspath("checked.txt"), 'r', encoding='utf-8') as f:
            checked = {line.strip() for line in f if line.strip()}

    ''' Получаем командой информацию о файлах в пути через dir '''
    for ind_for_err_path, path_curr in enumerate(paths):
        data_info = {}  # Обнуляем информацию, чтобы не было ошибок с одинаковым названием файлов

        today_file: bool = False
        answer_cmd = CommandWorker.command_get('dir ' + path_curr).split()  # Получаем ответ от cmd
        curr_date, prev_date = get_dates()  # Получаем сегодняшнюю и вчерашнюю дату

        # Дополнительная проверка даты
        try:
            # Надежное получение списка файлов через os.scandir
            for entry in scandir(path_curr):
                if entry.is_file():
                    # Получаем дату изменения файла в вашем формате ДД.ММ.ГГГГ
                    mod_time_timestamp = entry.stat().st_mtime
                    mod_time = datetime.fromtimestamp(mod_time_timestamp).strftime("%d.%m.%Y")
                    file_size = entry.stat().st_size  # Размер в байтах

                    # Сохраняем только файлы за сегодня/вчера и не XML
                    if mod_time in (curr_date, prev_date) and not entry.name.endswith('.xml'):
                        data_info[entry.name] = [file_size, mod_time]
                        if mod_time == curr_date:
                            today_file = True

        except Exception as e:
            error_log.append(f"ERROR READING DIRECTORY {path_curr}: {str(e)}")
            name_paths_error_log.append(names_to_paths[ind_for_err_path])
            continue

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
            # Проверяем память и дату на каждый файл
            for key, obj in data_info.items():
                if obj[1] == curr_date or (obj[1] == prev_date and not today_file):
                    # Получаем глобальные флаги для текущего пути
                    global_flags = global_flags_list[ind_for_err_path]
                    # Получаем флаги для конкретного файла (если есть)
                    file_specific = file_flags_list[ind_for_err_path].get(key, {})
                    # Объединяем: файловые флаги переопределяют глобальные
                    final_flags = {**global_flags, **file_specific}

                    # Фильтрация по расширениям и флагу skip
                    extension = key.split(".")[-1].lower() if '.' in key else ''

                    # Флаг --skip: полностью пропускаем файл
                    if final_flags.get('skip'):
                        files.work_file(f'Skipping {key} (flag --skip)')
                        continue  # не добавляем в отчёт и не проверяем размер

                    # Флаг --ignore_extensions: пропускаем файлы с указанными расширениями
                    if 'ignore_extensions' in final_flags:
                        ignored = [ext.strip().lower() for ext in final_flags['ignore_extensions'].split(',')]
                        if extension in ignored:
                            files.work_file(f'Skipping {key} (extension in ignore list)')
                            continue

                    # Флаг --extensions: проверяем только указанные расширения
                    if 'extensions' in final_flags:
                        allowed = [ext.strip().lower() for ext in final_flags['extensions'].split(',')]
                        if extension not in allowed:
                            files.work_file(f'Skipping {key} (extension not in allowed list)')
                            continue

                    # Проверка размера (если не отключена флагом skip_size)
                    min_size = int(final_flags.get('min_size', 5242880))  # по умолчанию 5 МБ

                    if not final_flags.get('skip_size'):
                        if obj[0] > min_size:
                            files.work_file(
                                f'{curr_date} check: The {key} file occupies {obj[0]} bytes of memory and its creation date is {obj[1]}.')
                        else:
                            er_txt = f'{curr_date} ERROR: The {key} file occupies {obj[0]} bytes of memory (<{min_size} bytes) and its creation date is {obj[1]}.'
                            files.work_file(er_txt, error=True)
                            error_log.append(er_txt)
                            name_paths_error_log.append(names_to_paths[ind_for_err_path])
                    else:
                        files.work_file(f'{curr_date} info: Skipped size check for {key} (size: {obj[0]} bytes)')

                # Сохраняем данные для проверки наличия/отсутствия файла
                full_path = path.join(path_curr, key)
                files_to_check.add(full_path)

                # Собираем информацию для асинхронной проверки
                file_info = (
                    key, obj, path_curr, names_to_paths[ind_for_err_path],
                    curr_date, prev_date, today_file,
                    password_7_zip, path_to_7_zip, files,
                    final_flags  # Используем уже готовые флаги
                )
                async_tasks.append(file_info)

    ''' Сравниваем checked с текущими файлами '''
    missing_files = checked - files_to_check
    new_files = files_to_check - checked

    # Обрабатываем пропавшие файлы
    if missing_files:
        for missing in missing_files:
            er_txt = f"FILE MISSING: {missing} was previously checked but now not found."
            files.work_file(er_txt, error=True)
            error_log.append(er_txt)
            name_paths_error_log.append(missing)  # или можно добавить имя бэкапа, если есть
        # Удаляем пропавшие из checked (чтобы не повторять ошибку)
        checked -= missing_files

    # Добавляем новые файлы в checked
    checked |= new_files

    # Сохраняем обновлённый checked
    with open(path.abspath("checked.txt"), 'w', encoding='utf-8') as f:
        for p in sorted(checked):
            f.write(p + '\n')

    ''' Асинхронно проверяем все файлы на наличие ошибок '''
    if async_tasks:
        try:
            errors_async, paths_async = asyncio.run(check_all_files_async(async_tasks))
            error_log.extend(errors_async)
            name_paths_error_log.extend(paths_async)
        except Exception as e:
            files.work_file(f'Async check failed: {e}', error=True)
            error_log.append(str(e))
            name_paths_error_log.append(names_to_paths[0])

    # Выдаём ошибки, если они есть
    # Парсим данные
    error_log = list(filter(bool, error_log))
    # Проверяем что массив не пустой
    if error_log:
        errors = ErrorFeedback(name_comp, error_log, name_paths_error_log)
        errors.send_error()


''' Проверка, что файл открыт впервые '''
if not check_single_instance():
    FileHelper().work_file("Программа уже запущена! Завершаем этот экземпляр.", error=True)
    exit(0)

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

        # Вычисляем следующее время КАК ПРЕДЫДУЩЕЕ + ИНТЕРВАЛ
        scheduled_next_run = next_run + timedelta(hours=CHECK_INTERVAL_HOURS)

        # Если вычисленное время УЖЕ прошло (например, проверка висела 30 часов),
        while scheduled_next_run <= datetime.now():
            scheduled_next_run += timedelta(hours=CHECK_INTERVAL_HOURS)

        # Сохраняем и используем новое время
        next_run = scheduled_next_run
        save_next_run_time(next_run)

        file.work_file(f"Следующее выполнение запланировано на: {next_run}")

    # Рассчитываем время до следующей проверки
    seconds_until_next = (next_run - current_time).total_seconds()
    sleep_time = min(seconds_until_next, MAX_SLEEP_SECONDS)

    if sleep_time > 0:
        # Спим
        sleep(sleep_time)
