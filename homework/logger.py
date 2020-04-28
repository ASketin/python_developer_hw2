import logging

# логгер для отслеживания работы
logger_info = logging.getLogger("Patient")
logger_info.setLevel(logging.INFO)
handler = logging.FileHandler("info.txt", 'a', 'utf-8')
formatter = logging.Formatter("%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s")
handler.setFormatter(formatter)
logger_info.addHandler(handler)

# логгер для отслеживания ошибок
logger_error = logging.getLogger("Error")
logger_error.setLevel(logging.ERROR)
handler_error = logging.FileHandler("errors.txt", 'a', 'utf-8')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error)
