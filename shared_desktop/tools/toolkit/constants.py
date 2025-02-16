"""
Модуль содержит константы для api, реализованные через класс Enum
"""

from enum import Enum


class AvailableControllers(Enum):
    """
    Доступные типы контроллера
    """
    SWARCO = 'SWARCO'
    POTOK_P = 'ПОТОК (P)'
    POTOK_S = 'ПОТОК (S)'
    PEEK = 'PEEK'


# class AvailableCommands(Enum):
#     """
#     Доступные команды управления
#     """
#
#     FLASH_BUTTON = 'ЖМ КНОПКА'
#     DARK_BUTTON = 'ОС КНОПКА'
#     LOCAL_BUTTON = 'ЛОКАЛ КНОПКА'
#     STAGE_MAN = 'ФАЗА MAN'
#     DARK_MAN = 'ОС MAN'
#     FLASH_MAN = 'ЖМ MAN'
#     DARK_SNMP = 'ОС SNMP'
#     FLASH_SNMP = 'ЖМ SNMP'
#     STAGE_SNMP = 'ФАЗА SNMP'
#     CP_RED = 'КК CP_RED'
#     PROGRAMM_RESTART = 'РЕСТАРТ ПРОГРАММЫ'
#     REBOOT = 'ПЕРЕЗАГРУЗКА ДК'


class AvailableSetCommandsControllerRESERVED(Enum):
    """
    Доступные запросы команд для данного api типа set
    """

    FLASH_BUTTON = 'flash_button'
    DARK_BUTTON = 'dark_button'
    LOCAL_BUTTON = 'local_button'
    STAGE_MAN = 'stage_man'
    DARK_MAN = 'dark_man'
    FLASH_MAN = 'flash_man'
    DARK_SNMP = 'dark_snmp'
    FLASH_SNMP = 'flash_snmp'
    STAGE_SNMP = 'stage_snmp'
    CP_RED = 'all_red_cp'
    USER_PARAMETERS = 'user_parameters'
    PROGRAM_RESTART = 'restart_program'
    REBOOT = 'reboot'


class AvailableSetCommandsController(Enum):
    """
    Доступные запросы команд для данного api типа set
    """

    FLASH_BUTTON = 'ЖМ КНОПКА'
    DARK_BUTTON = 'ОС КНОПКА'
    LOCAL_BUTTON = 'ЛОКАЛ КНОПКА'
    STAGE_MAN = 'ФАЗА MAN'
    DARK_MAN = 'ОС MAN'
    FLASH_MAN = 'ЖМ MAN'
    DARK_SNMP = 'ОС SNMP'
    FLASH_SNMP = 'ЖМ SNMP'
    STAGE_SNMP = 'ФАЗА SNMP'
    CP_RED = 'КК CP_RED'
    PROGRAM_RESTART = 'РЕСТАРТ ПРОГРАММЫ'
    USER_PARAMETERS = 'ПАРАМЕТРЫ ПРОГРАММЫ'
    INPUTS = 'ВВОДЫ'
    REBOOT = 'ПЕРЕЗАГРУЗКА ДК'


class AvailableGetCommandsController(Enum):
    """
    Доступные запросы команд для данного api типа get
    """

    GET_STATE = 'get_state'
    GET_STATES = 'get_states'
    GET_CONFIG = 'get_config'


class AvailableTypesRequest(Enum):
    """
    Доступные типы запросов
    """

    TYPE_GET = {'get_state', 'get_config', 'get_states'}
    TYPE_SET = {'set_command'}


class ErrorMessages(Enum):
    """
    Тексты сообщений для json responce
    """

    BAD_DATA_FOR_REQ = 'Некорректные данные для запроса'
    NUMBER_NOT_IN_DB = 'Объект с данным номером/ip не найден в базе'
    IP_ADDRESS_NOT_FOUND_IN_DB = 'IP-adress не найден в базе'
    IP_ADDRESS_NOT_PROVIDED = 'IP-adress не предоставлен'
    TYPE_CONTROLLER_NOT_PROVIDED = 'Тип контроллера не указан'
    VALUE_COMMAND_IS_EMPTY = 'Значение не может быть пустым для команды'
    INVALID_STAGE_VALUE = 'Недопустимое значение фазы'
    INVALID_COMMAND_OR_VALUE = 'Недопустимая команда и/или недопустимое значение команды'
    INVALID_STAGE_VALUE_FOR_THIS_TYPE_CONTROLLER = 'Недопустимое значение фазы для данного типа ДК'
    INVALID_COMMAND_VALUE = 'Недопустимое значение для команды'
    INVALID_CONTROLLER_TYPE = 'Недопустимый тип контроллера'
    INVALID_CONTROLLER_TYPE_REQ = 'Недопустимый зарос для данного типа контроллера'
    INVALID_COMMAND_TYPE = 'Недопустимый тип команды'
    INVALID_REQ_ENTITY = 'Недопустимый тип запроса'
    NUM_CO_OR_IP_NOT_PROVIDED = 'Номер СО/ip_address не предоставлены'


class RequestOptions(Enum):
    """
    Доступные опции запросов в api
    """

    search_in_db = 'search_in_db'
    request_from_telegramm = 'req_from_telegramm'
    type_set = 'set'
    type_get = 'get'
    type_get_config = 'get_config'
    type_get_state = 'get_state'
    type_get_states = 'get_states'
    type_set_command = 'set_command'
    chat_id = 'chat_id'
    hosts = 'hosts'
    type_request = 'type_request'


class JsonResponceBody(Enum):
    """
    Класс с перечислениями полей json responce
    """

    REQ_ERRORS = 'request_errors'
    HOST_ID = 'host_id'
    SCN = 'scn'
    IP_ADDRESS = 'ip_adress'
    PROTOCOL = 'protocol'
    VALID_DATA_REQUEST = 'valid_data_request'
    TYPE_CONTROLLER = 'type_controller'
    ADDRESS = 'address'
    NUMBER = 'number'
    TYPE = 'type'
    REQUEST_EXEC_TIME = 'request_execution_time'
    REQ_ENTITY = 'request_entity'
    RESP_ENTITY = 'responce_entity'
    RAW_DATA = 'raw_data'
    DOWNLOAD_DATA = 'download_data'
    PATH_TO_ARHIVE = 'path_to_archive'
    PATH_TO_URL = 'url_to_archive'
    SSH = 'ssh'
    FTP = 'ftp'
    START_TIME = 'start_time'
    MODEL_OBJ = 'obj'
    HAS_IN_DB = 'has_in_db'
    TIME_REQ_CONTROLLER = 'request_time'


class Database(Enum):
    """
    Класс хранит константы, связанные с использованием бд: названия полей, описание и т.д.
    """

    CREATED = 'created'
    UPLOADED = 'uploaded'
    DESCR_UPLOAD_CONFIG = 'загрузка конфига'
    DESCR_CREATE_ARCHIVE = 'создание архива с конфигом'

    FIELD_number = 'number'
    FIELD_description = 'description'
    FIELD_type_controller = 'type_controller'
    FIELD_ip_adress = 'ip_adress'
    FIELD_address = 'address'