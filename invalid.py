# -------КЛАСС ОШИБОК-----------
class ErrorFieldEmpty(Exception):
    """
    Исключение, вызываемое при попытке оставить обязательное текстовое поле пустым.
    """
    def __init__(self, field_name):
        self.field_name = field_name
        super().__init__(f"Поле '{field_name}' не может быть пустым.")


class ErrorDateField(Exception):
    """
    Исключение, вызываемое при некорректном вводе даты.
    """
    def __init__(self, date_field, message):
        self.date_field = date_field
        super().__init__(f"Поле '{date_field}' некорректно. {message}")


class ErrorInvalidFormat(Exception):
    """
    Исключение, вызываемое при вводе данных в неверном формате.
    """
    def __init__(self, field_name, message):
        self.field_name = field_name
        super().__init__(f"Неверный формат данных в поле '{field_name}'. {message}")
