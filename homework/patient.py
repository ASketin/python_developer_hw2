from abc import ABC, abstractmethod
from dateutil.parser import parse
import regex as re
import logging
import os
from homework.logger import logger_error, logger_info, handler, handler_error

from homework.config import PHONE_FORMAT, DRIVER_LICENSE_TYPE, DRIVER_LICENSE_FORMAT, PASSPORT_TYPE

# лучше вместо глобальных констант, создать структуры с интерфейсом
# обновления элементов и форматов
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


class BaseDescriptor(ABC):
    """
        Базовый дескриптор
    """

    def __set_name__(self, owner, name):
        self.name = name
        self.value = None

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    @staticmethod
    def check_type(value):
        if not isinstance(value, str):
            logger_error.error(f"Invalid type")
            raise TypeError("Not string")

    @abstractmethod
    def __set__(self, instance, value):
        pass


class StringDescriptor(BaseDescriptor):
    """
        Дескриптор данных для first_name, last_name.
        В случае некорректного формата данных выбрасвает
        ошибку ValueError, все ошибки логируются в errors.

        Формат имени предполагает отсутствие цифр и небуквенных
        символов, количество уникальнх символов > 2
    """

    def __set__(self, instance, value):
        self.check_type(value)
        if self.check_name(value):
            if self.name not in instance.__dict__:
                instance.__dict__[self.name] = value
            else:
                logger_error.error(f"Changes Forbidden")
                raise AttributeError("Changes Forbidden")
        else:
            logger_error.error(f"Incorrect Name/Surname {value}")
            raise ValueError("Incorrect Name/Surname")

    @staticmethod
    def check_name(value):
        if len(set(value)) < 2:
            return False
        if not value.isalpha():
            return False
        return True


class DateDescriptor(BaseDescriptor):
    """
       Дата имеет тип datetime.
       Исключения логгируем в exceptions
    """

    def __set__(self, instance, value):
        self.check_type(value)
        if self.check_date(value):
            tmp = parse(value)
            if self.name in instance.__dict__:
                logger_info.info(f"Date was changed ")
            instance.__dict__[self.name] = tmp

        else:
            logger_error.error(f"Invalid date: {value}")
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

    def __set__(self, instance, value):
        self.check_type(value)
        number, status = self.check_phone(value)
        if status:
            if self.name in instance.__dict__:
                logger_info.info("Phone was changed")
            instance.__dict__[self.name] = number
        else:
            logger_error.error(f"Invalid number: {value}")
            raise ValueError("Invalid number")

    @staticmethod
    def check_phone(number):
        parsed_num = re.findall(r"\d+", number)
        res = "8"
        res += ''.join(parsed_num)[1:]
        if len(res) != 11:
            return None, False
        if int(res[1:4]) not in OPERATORS_CODE:
            return None, False
        if re.search(INAPROPRIATE_SYMBOLS, number) is not None:
            return None, False
        return res, True


class DocDescriptor(BaseDescriptor):
    """
        Дескриптор для типа документа и его номера
        Содержит проверку для обоих полей
    """

    def __set__(self, instance, value):

        if self.name == "document_id":
            self.check_type(value)
            res, status = self.check_id(value, DOC_TYPE[instance.document_type])
            if status:
                if self.name in instance.__dict__:
                    logger_info.info("ID was changed")
                instance.__dict__[self.name] = res
            else:
                logger_error.error(f"Invalid id: {value}")
                raise ValueError("Invalid ID")

        elif self.name == "document_type":
            self.check_type(value)
            if self.check_doc(value):
                if self.name in instance.__dict__:
                    logger_info.info("Type was changed")
                instance.__dict__[self.name] = value
            else:
                logger_error.error(f"Invalid document: {value}")
                raise ValueError("Invalid document")

    @staticmethod
    def check_id(number, fix_size):
        parsed_num = re.findall(r"\d+", number)
        res = ''.join(parsed_num)
        if len(res) != fix_size:
            return None, False
        if re.search(INAPROPRIATE_SYMBOLS, number) is not None:
            return None, False
        return res, True

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
            удостоверения, прочее), надо реализовать метод
            добавления нового документа карантинного пропуска к
            примеру
        : номер документа(string) - проверять на соответствие
            номера формату документа

        Создание, изменние, сохранение объекта записываем
            в лог info
        Исключения, случившиеся при работе,
            в лог errors

        Хранить пациента нужно в csv, у класса
        есть метод save для дозаписи в файл
    """

    first_name = StringDescriptor()
    last_name = StringDescriptor()
    birth_date = DateDescriptor()
    phone = PhoneDescriptor()
    document_type = DocDescriptor()
    document_id = DocDescriptor()

    logger_info = logging.getLogger("Patient")
    logger_error = logging.getLogger("Error")

    def __init__(self, first_name, last_name, birth_date,
                 phone, document_type, document_id: str,
                 created=None):
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.phone = phone
        self.document_type = document_type
        self.document_id = document_id

        if not created:
            logger_info.info(f"{first_name} {last_name} was written")

    @staticmethod
    def create(first_name, last_name, birth_date, phone,
               document_type, document_id):
        logger_info.info(f"{first_name} {last_name} was created")
        return Patient(first_name, last_name, birth_date, phone,
                       document_type, document_id, created=True)

    def save(self):
        data = [self.first_name, self.last_name, self.birth_date,
                self.phone, self.document_type, self.document_id]
        with open("table.csv", "a", encoding="utf-8") as table:
            table.write(u",".join(map(str, data)) + u"\n")
            logger_info.info(f"patient was saved")

    def __del__(self):
        handler.close()
        handler_error.close()


class CollectionIterator:

    def __init__(self, path, limit=None):
        self.collection = open(path, "r", encoding="utf-8")
        self.limit = limit
        self.line = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.has_more():
            params = self.collection.readline()
            self.line += 1
            return Patient(*params.split(","))
        else:
            raise StopIteration()

    def has_more(self):
        if self.line == self.limit:
            return False
        if self.collection.tell() != os.fstat(
                self.collection.fileno()).st_size:
            return True
        else:
            return False

    def __del__(self):
        self.collection.close()


class PatientCollection:
    """Берет данные из csv файла, поддерживает итерацию
       ссодержит метод limit, возвращаюший итератор/генератор
       первых n записей
    """

    def __init__(self, path):
        self.path = path

    def __iter__(self):
        return CollectionIterator(self.path)

    def limit(self, n):
        return CollectionIterator(self.path, n)
