from abc import ABC, abstractmethod

import psycopg2
from dateutil.parser import parse
import regex as re
import logging
from homework.logger import logger_error, logger_info, handler, handler_error
from homework.db_config import config


# лучше вместо глобальных констант, создать структуры с интерфейсом
# обновления элементов и форматов
from tests.constants import PATIENT_FIELDS

OPERATORS_CODE = {900, 901, 902, 903, 904, 905, 906, 908, 909, 910,
                  911, 912, 913, 914, 915, 916, 917, 918, 919, 920,
                  921, 922, 923, 924, 925, 926, 927, 928, 929, 930,
                  931, 932, 933, 934, 936, 937, 938, 939, 941, 950,
                  951, 952, 953, 954, 955, 956, 958, 960, 961, 962,
                  963, 964, 965, 966, 967, 968, 969, 970, 971, 977,
                  978, 980, 981, 982, 983, 984, 985, 986, 987, 988,
                  989, 991, 992, 993, 994, 995, 996, 997, 999}

DOC_TYPE = {"паспорт": 10, "заграничный паспорт": 9,
            "водительское удостоверение": 10}
INAPROPRIATE_SYMBOLS = r"[a-zA-Z\u0400-\u04FF.!@?#$%&:;*\,\;\=[\\\]\^_{|}<>]"


def my_logging_decorator(method):
    def method_wrapper(*args):

        exist = False
        result = None

        if method.__name__ == "__set__":
            if args[0]._name in args[1].__dict__:
                exist = True

        if method.__name__ == "__init__":
            result = method(*args)
            logger_info.info(f"Patient was {method.__name__}")

        else:
            try:
                result = method(*args)
                if exist:
                    logger_info.info(f"{args[0]._name} was changed")
                if method.__name__ == "save":
                    logger_info.info(f"Patient was {method.__name__}")
            except (TypeError, ValueError, AttributeError, psycopg2.DatabaseError,
                    Exception) as e:
                logger_error.error(e)
                raise e

        return result

    return method_wrapper


def db_request(request, amount=None, db="patients"):
    params = config()
    params["database"] = db
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(request)
    result = None
    if amount is not None:
        result = cur.fetchone() if amount == "one" else cur.fetchall()
    conn.commit()
    cur.close()
    return result


class BaseDescriptor(ABC):
    """
        Базовый дескриптор
    """

    def __set_name__(self, owner, name):
        self._name = name
        self._value = None

    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    @staticmethod
    def check_type(value):
        if not isinstance(value, str):
            raise TypeError("Not string")

    @abstractmethod
    def __set__(self, instance, value):
        pass


class StringDescriptor(BaseDescriptor):
    """
        Дескриптор данных для first_name, last_name.
        В случае некорректного формата данных выбрасвает
        ошибку ValueError, все ошибки логируются в errors.
        Изменение имени после инициализация объекта запре-
        щено.

        Формат имени предполагает отсутствие цифр и небуквенных
        символов
    """

    @my_logging_decorator
    def __set__(self, instance, value):
        self.check_type(value)
        if self.check_name(value):
            if self._name not in instance.__dict__:
                instance.__dict__[self._name] = value
            else:
                raise AttributeError("Changes Forbidden")
        else:
            raise ValueError("Incorrect Name/Surname")

    @staticmethod
    def check_name(value):
        if not value.isalpha():
            return False
        return True


class DateDescriptor(BaseDescriptor):
    """
       Дата имеет тип datetime.
       Исключения логгируем в errors
    """

    @my_logging_decorator
    def __set__(self, instance, value):
        self.check_type(value)
        if self.check_date(value):
            tmp = parse(value)
            instance.__dict__[self._name] = tmp

        else:
            raise ValueError("input not str type")

    @staticmethod
    def check_date(value):
        try:
            parse(value)
        except ValueError:
            return False
        return True


class PhoneDescriptor(BaseDescriptor):
    """
        Проверяет значение на соответствие формату.
        Исключения логгируем в errors
    """

    @my_logging_decorator
    def __set__(self, instance, value):
        number = self.check_phone(value)
        if number is not None:
            instance.__dict__[self._name] = number
        else:
            raise ValueError("Invalid number")

    @staticmethod
    def check_phone(number):
        parsed_num = re.findall(r"\d+", number)
        res = "8"
        res += ''.join(parsed_num)[1:]
        if len(res) != 11:
            return None
        if int(res[1:4]) not in OPERATORS_CODE:
            return None
        if re.search(INAPROPRIATE_SYMBOLS, number) is not None:
            return None
        return res


class DocDescriptor(BaseDescriptor):
    """
        Дескриптор для типа документа и его номера
        Содержит проверку для обоих полей
    """

    @my_logging_decorator
    def __set__(self, instance, value):

        if self._name == "document_id":
            res = self.check_id(value, DOC_TYPE[instance.document_type])
            if res is not None:
                instance.__dict__[self._name] = res
            else:
                raise ValueError("Invalid ID")

        elif self._name == "document_type":
            if self.check_doc(value):
                instance.__dict__[self._name] = value
            else:
                raise ValueError("Invalid document")

    @staticmethod
    def check_id(number, fix_size):
        parsed_num = re.findall(r"\d+", number)
        res = ''.join(parsed_num)
        if len(res) != fix_size:
            return None
        if re.search(INAPROPRIATE_SYMBOLS, number) is not None:
            return None
        return res

    @staticmethod
    def check_doc(doc_type):
        if str.lower(doc_type) not in DOC_TYPE:
            return False
        return True


class Patient:
    """
        Объект хранит информацию о пациенте
        : имя(string) - должно состоять из букв
        : фамилия(string) - должно состоять из букв
        : дата рождения(string) - будем хранить в формате
            datetime
        : номер телефона(string) - соответствие формату,хранение в
            виде 8xxxxxxxxxxx
        : тип документа(string) - ограниченный набор(паспорт,
            удостоверения, прочее)
        : номер документа(string) - проверять на соответствие
            номера формату документа

        Создание, изменние, сохранение объекта записываем
            в лог info
        Исключения, случившиеся при работе,
            в лог errors

        Пациент хранится в БД Postgres.Поля database и table
        указывают на необходимую таблицу.
    """

    first_name = StringDescriptor()
    last_name = StringDescriptor()
    birth_date = DateDescriptor()
    phone = PhoneDescriptor()
    document_type = DocDescriptor()
    document_id = DocDescriptor()

    logger_info = logging.getLogger("Patient")
    logger_error = logging.getLogger("Error")

    database = "patients"
    table = "ill_patients"

    @my_logging_decorator
    def __init__(self, first_name, last_name, birth_date,
                 phone, document_type, document_id: str):
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.phone = phone
        self.document_type = document_type
        self.document_id = document_id

    @staticmethod
    def create(first_name, last_name, birth_date, phone,
               document_type, document_id):
        return Patient(first_name, last_name, birth_date, phone,
                       document_type, document_id)

    @my_logging_decorator
    def save(self):
        data = [self.first_name, self.last_name, self.birth_date.date(),
                self.phone, self.document_type, self.document_id]
        data = str(tuple(map(str, data)))[1:-1]
        db_request(f"insert into {self.table} values (DEFAULT, {data})")

    def __del__(self):
        handler.close()
        handler_error.close()


class CollectionIterator:

    def __init__(self, table, limit=None):
        self.table = table
        first_index = db_request(f"select Min(id) from {self.table}", "one")
        self.line = 0 if first_index[0] is None else int(first_index[0])
        self.limit = None if limit is None \
            else self.line + limit

    def __iter__(self):
        return self

    def __next__(self):
        if self.has_more():
            result = db_request(f"select * from {self.table} where id = {self.line}",
                                "one")
            self.line += 1
            return Patient(*result[1:])
        else:
            raise StopIteration()

    def has_more(self):
        last_index = db_request(f"select Max(id) from {self.table}", "one")
        if last_index[0] is None or self.line > last_index[0]:
            return False
        if self.limit is not None and self.line >= self.limit:
            return False
        return True


class PatientCollection:
    """
        Берет данные из БД Postgres, поддерживает итерацию
        содержит метод limit, возвращаюший итератор/генератор
        первых n записей.В поле self.table указывают необходимую
        таблицу.
    """

    def __init__(self, table):
        self.table = table

    @my_logging_decorator
    def __iter__(self):
        return CollectionIterator(self.table)

    @my_logging_decorator
    def limit(self, n):
        return CollectionIterator(self.table, n)
