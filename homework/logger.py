import logging

# логгер для отслеживания работы
logger_info = logging.getLogger("Patient")
logger_info.setLevel(logging.INFO)
# логгер для отслеживания ошибок
logger_error = logging.getLogger("Error")
logger_error.setLevel(logging.ERROR)
