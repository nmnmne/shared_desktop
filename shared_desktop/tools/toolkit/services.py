import abc
import functools
import json
import os
import pathlib
import shutil
import zipfile
import time
from dataclasses import field, dataclass
from typing import Coroutine, Dict, Tuple, List, Callable
import logging
from datetime import datetime as dt

import _asyncio
import aiohttp
from django.core.files.uploadedfile import InMemoryUploadedFile
from dotenv import load_dotenv
import asyncio
import ipaddress

from asgiref.sync import sync_to_async
from django.forms import model_to_dict
from shared_desktop.settings import MEDIA_ROOT2

from .models import SaveConfigFiles
from .models import (
    TrafficLightsObjects,
    TrafficLightConfigurator,
    TelegrammUsers
)
from .sdp_lib.management_controllers import controller_management
from .sdp_lib.swarco_controller import ITC_PC_config
from .constants import (
    AvailableControllers,
    AvailableSetCommandsController,
    AvailableGetCommandsController,
    ErrorMessages,
    JsonResponceBody,
    Database,
    RequestOptions,
    AvailableTypesRequest
)
from .sdp_lib.potok_controller import potok_user_api
from .sdp_lib.conflicts.calculate_conflicts import (
    CommonConflictsAndStagesAPI,
    SwarcoConflictsAndStagesAPI,
    PeekConflictsAndStagesAPI
)
from .sdp_lib.conflicts import calculate_conflicts
from .sdp_lib.peek_controller import processes as peek_processes


load_dotenv()
logger = logging.getLogger(__name__)


def set_curr_datetime() -> str:
    """
    Получает текущее время и дату
    :return: текущее время и дату
    """

    return controller_management.BaseCommon.set_curr_datetime()


def reverse_slashes(path: str) -> str:
    """
    Заменяет обратные слеши на прямые
    :param path: строковое представление пути до файла/катлога
    :return: строковое представление пути до файла/катлога со слешами вида "/"
    """

    return path.replace('\\', '/')


def correct_path_for_db(path: str) -> str:
    """
    Заменяет обратные слеши на прямые для пути к файлу в моделе SaveConfigFiles
    :param path: строковое представление пути до файла/катлога
    :return: строковое представление пути до файла/катлога со слешами вида "/"
    """

    return reverse_slashes(path).split('media/')[-1]


def get_controller_manager(type_request: str):
    """
    Создает объект менеждера для дальнейшего управления и взаимодействия во view функции/методе
    :param type_request: тип из api запроса
    :return: экземпляр класса, соответсвующий запросу
    """

    if type_request == RequestOptions.type_get_state.value or type_request == RequestOptions.type_get_states.value:
        manager = GetDataFromController()
    elif type_request == RequestOptions.type_set_command.value:
        manager = SetRequestToController()
    elif type_request == RequestOptions.type_get_config.value:
        manager = FileDownLoad()
    else:
        manager = None
    return manager


class QuerysetToDB:
    """
    Класс отправляет и обрабатывает запросы в БД
    """

    @staticmethod
    @sync_to_async()
    def async_db_query(param_for_search):
        queryset = TrafficLightsObjects.objects.filter(number=int(param_for_search))
        res = queryset.values()
        if res:
            res = queryset.values()[0]
        logger.debug(res)
        return res

    async def get_queryset(self, data_for_search: tuple) -> tuple:
        """
        Поиск объекта в бд по номеру/ip-address
        :param data_for_search: кортеж вида (Номер СО/IP-address из http запроса, поле поска в бд)
        :return: кортеж вида (Номер СО/IP-address из http запроса, model_to_dict(queryset)) если объект найден,
                 иначе  (Номер СО/IP-address из http запроса, None)
        """

        param, field = data_for_search
        logger.debug(data_for_search)
        if field == 'name':
            queryset = await TrafficLightsObjects.objects.filter(number=param).afirst()
        elif field == 'ipAddress':
            queryset = await TrafficLightsObjects.objects.filter(ip_adress=param).afirst()
        else:
            logger.critical(f'param_for_search: {data_for_search}')
            raise ValueError

        if queryset:
            return data_for_search, model_to_dict(queryset, fields=[
                Database.FIELD_number.value, Database.FIELD_description.value, Database.FIELD_type_controller.value,
                Database.FIELD_ip_adress.value, Database.FIELD_address.value,
                # 'number', 'description', 'type_controller', 'ip_adress', 'address'
            ])
        return data_for_search, None

    async def get_queryset_traffic_lights(self, source: str, field: str) -> dict | None:
        """
        Поиск объекта в бд по номеру/ip-address
        :param data_for_search: кортеж вида (Номер СО/IP-address из http запроса, поле поска в бд)
        :return: кортеж вида (Номер СО/IP-address из http запроса, model_to_dict(queryset)) если объект найден,
                 иначе  (Номер СО/IP-address из http запроса, None)
        """

        if field == Database.FIELD_number.value:
            queryset = await TrafficLightsObjects.objects.filter(number=source).afirst()
        elif field == Database.FIELD_ip_adress.value:
            queryset = await TrafficLightsObjects.objects.filter(ip_adress=source).afirst()
        else:
            raise ValueError

        if queryset:
            return model_to_dict(queryset, fields=[
                Database.FIELD_number.value, Database.FIELD_description.value, Database.FIELD_type_controller.value,
                Database.FIELD_ip_adress.value, Database.FIELD_address.value,
            ])

    @classmethod
    async def get_queryset_chat_id_tg(cls, chat_id):
        queryset = await TelegrammUsers.objects.filter(chat_id=chat_id).afirst()
        if queryset:
            return model_to_dict(queryset)

    async def main(self, queryset_data: dict):
        """
        Главный метод, который собирает данные для запроса в бд для каждого хоста
        :param queryset_data:
        :return:
        """

        async with asyncio.TaskGroup() as tg:
            tasks_res = [
                tg.create_task(
                    self.get_queryset_traffic_lights(ipAddr_or_num, Database.FIELD_ip_adress.value
                    if ipAddr_or_num.count('.') == 3 else Database.FIELD_number.value),
                    name=ipAddr_or_num) for ipAddr_or_num in queryset_data
            ]
        logger.debug(tasks_res)
        return self.merge_queryset_data(queryset_data, tasks_res)

    def merge_queryset_data(self, data_hosts: dict, res_queryset: list[_asyncio.Task]) -> dict:
        """
        Метод объединяет данные, полученные из queryset с данными из data_host
        :param data_hosts: данные со всеми хостами
        :param res_queryset: результат запроса в бд
        :return: обновленный словарь со всеми хостами
        """

        for res in res_queryset:
            ipAddr_or_num, result = res.get_name(), res.result()
            if result is None:
                data_hosts[ipAddr_or_num][JsonResponceBody.REQ_ERRORS.value] = ErrorMessages.NUMBER_NOT_IN_DB.value
                continue
            ipAddr = result.get(JsonResponceBody.IP_ADDRESS.value)
            if not ipAddr:
                data_hosts[ipAddr_or_num][
                    JsonResponceBody.REQ_ERRORS.value] = ErrorMessages.IP_ADDRESS_NOT_FOUND_IN_DB.value
                continue
            data_hosts[ipAddr] = data_hosts[ipAddr_or_num] | result | {
                JsonResponceBody.HOST_ID.value: result.get(Database.FIELD_number.value),
                JsonResponceBody.HAS_IN_DB.value: True
            }
            for i, item in enumerate((ipAddr_or_num, JsonResponceBody.IP_ADDRESS.value, JsonResponceBody.NUMBER.value)):
                try:
                    if i == 0 and Checker.validate_err_ipv4(ipAddr_or_num) is not None:
                        del data_hosts[item]
                    else:
                        del data_hosts[ipAddr][item]
                    # data_hosts.pop(item) if i == 0 and Checker.validate_err_ipv4(ipAddr_or_num) is None else data_hosts[ipAddr].pop(item)
                except KeyError:
                    pass
        logger.debug(data_hosts)
        ResponceMaker.save_json_to_file(data_hosts, 'common.json')
        return data_hosts


class Checker:
    """
    Класс различных проверок валидности данных для выполения api запросов
    """

    def get_available_req_entities(self, type_req: str) -> set[str]:

        """
        Формирует множество с допустимыми типами запросов исходя из type_req(get или set)
        :param type_req: тип запроса из тела запроса, отправленного в api
        :return: если type_req принадлежит коллекции с get типами, возвращает множество get типов.
                 Если type_req принадлежит коллекции с set типами, возвращает множество типами команд
        """

        if type_req in AvailableTypesRequest.TYPE_GET.value:
            available_req_entities = {v.value for v in AvailableGetCommandsController}
        elif type_req in AvailableTypesRequest.TYPE_SET.value:
            available_req_entities = {v.value: None for v in AvailableSetCommandsController}
        else:
            raise ValueError
        return available_req_entities

    def check_error_request_in_all_hosts(self, data_hosts: dict) -> bool:
        """
        Проверяет что в data_hosts есть хотябы один хост без "request_errors" значения data_hosts[request_errors]: ...
        :param data_hosts: словарь с данными о хостах
        :return: Если есть хотябы один хост без request_errors -> возвращает False, иначе True
        """

        for ipAddr, data_host in data_hosts.items():
            if data_host == ErrorMessages.NUMBER_NOT_IN_DB.value:
                return True
            if not data_host.get('request_errors'):
                return False
        return True

    @classmethod
    def validate_err_ipv4(cls, ipV4: str) -> None | str:
        """
        Проверяет соответствует ip_addr строковому представлению IPv4/IPv6
        :param ipV4: проверяемая строка с IP-адрессом
        :return: None, если нет ошибки и переданная строка является IPv4, иначе строкое представление
                 о некоррктном IPV4
        """

        err_ipv4 = None
        try:
            ipaddress.ip_address(ipV4)
        except ValueError as err:
            err_ipv4 = err.__str__()
        except Exception as err:
            logger.warning(err)
        finally:
            return err_ipv4

    def validate_type_controller(self, type_controller: str) -> None | str:
        """
        Метод проверяет валидность типа контроллера
        :param type_controller: тип контроллера
        :return: None если нет ошибки, иначе текст ошибки
        """
        if (type_controller is None
                or type_controller.upper() not in {controller.value for controller in AvailableControllers}):
            return ErrorMessages.TYPE_CONTROLLER_NOT_PROVIDED.value

    def validate_req_entity_get_req(self, req_entity: list[str], available_req_entity: set) -> None | str:

        """
        Метод проверяет валидность req_entity для запросов типа get
        :param available_req_entity:
        :param req_entity: список с типом/типами запросов. Например: [get_config], [get_state]
        :return: None если нет ошибки, иначе текст ошибки
        """

        if not isinstance(req_entity, list):
            return ErrorMessages.INVALID_REQ_ENTITY.value
        for req in req_entity:
            if req not in available_req_entity:
                return ErrorMessages.INVALID_REQ_ENTITY.value

    def validate_req_entity_set_req(
            self, req_entity: dict[str, str], available_commands: set[str], type_controller: str
    ) -> None | str:
        """
        Метод проверяет валидность запрашиваемой команды и её значения
        :param type_controller: тип контроллера, для которого будет проводится проверка
        :param req_entity: словарь с типом команды и её значением. Например: {Фаза: 1}, {ЖМ: 1} и т.д.
        :param available_commands: множество, в котором сожержатся допустимые команды из AvailableSetCommandsController
        :return: None если команда и значение валидны иначе текст ошибки
        """

        if not isinstance(req_entity, dict):
            return ErrorMessages.INVALID_REQ_ENTITY.value
        type_command, set_val = list(req_entity.items())[0]
        type_command, set_val = type_command.upper(), set_val.upper()
        if type_command is None or type_command not in available_commands:
            return ErrorMessages.INVALID_COMMAND_TYPE.value
        return self.validate_val_command(type_controller.upper(), type_command, set_val)

    def validate_val_command(self, type_controller: str, type_command: str, set_val: str) -> None | str:
        """
        Метод проверяет валидность значения команды
        :param type_controller: тип контроллера
        :param type_command: тип команды (из AvailableSetCommandsController)
        :param set_val: проверяемое значение команды
        :return: None, если значение валидно, иначе текст ошибки
        """

        stage = 'ФАЗА'
        if (type_command == AvailableSetCommandsController.REBOOT.value
                or type_command == AvailableSetCommandsController.PROGRAM_RESTART.value):
            return
        if stage in type_command:
            if not set_val.isdigit():
                return ErrorMessages.INVALID_STAGE_VALUE.value
            if type_controller == AvailableControllers.SWARCO.value:
                if int(set_val) not in range(9):
                    return ErrorMessages.INVALID_STAGE_VALUE_FOR_THIS_TYPE_CONTROLLER.value
            else:
                if int(set_val) not in range(65):
                    return ErrorMessages.INVALID_STAGE_VALUE_FOR_THIS_TYPE_CONTROLLER.value
        else:
            if (type_command == AvailableSetCommandsController.USER_PARAMETERS.value
                    or type_command != AvailableSetCommandsController.INPUTS.value):
                return
            allowed_values = {
                'ВКЛ', 'ВЫКЛ', 'TRUE', 'FALSE', 'ON', 'OFF', '0', '1'
            }

            if set_val not in allowed_values:
                return ErrorMessages.INVALID_COMMAND_VALUE.value

    def validate_all_properties_data_hosts(self, data_hosts: dict, type_req: str) -> dict:
        """
        Метод реализует проверку обязательных данных добавление свойства request_errors(при необходимости),
        характерных для типа запроса(request_entity)
        :param type_req: тип запроса из тела запроса, отправленного в api
        :param data_hosts: словарь со свойствами всем хостов из запроса api
        :return: проверенный словарь со всеми хостами
        """

        logger.debug(type_req)
        available_req_entity = self.get_available_req_entities(type_req)

        for ipAddr, data_host in data_hosts.items():
            err_ipAddr = self.validate_err_ipv4(ipAddr)
            if err_ipAddr is not None:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = err_ipAddr
                continue
            type_controller = data_host.get(JsonResponceBody.TYPE_CONTROLLER.value)
            err_type_controller = self.validate_type_controller(type_controller)
            if err_type_controller is not None:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = err_type_controller
                continue

            if type_req in AvailableTypesRequest.TYPE_GET.value:
                err_req_entity = self.validate_req_entity_get_req(
                    data_host.get(JsonResponceBody.REQ_ENTITY.value), available_req_entity
                )
            else:
                err_req_entity = self.validate_req_entity_set_req(
                    data_host.get(JsonResponceBody.REQ_ENTITY.value), available_req_entity, type_controller
                )
            if err_req_entity is not None:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = err_req_entity
                continue
        return data_hosts


class ResponceMaker:
    """
    Класс формирует данные для ответа типа json для различных типов запросов
    """

    @classmethod
    def save_json_to_file(cls, json_data, file_name='data_hosts.json', mode: str = 'w') -> None:
        """
        Формирует json и записывает в файл
        :param json_data: словарь, который будет записан как json
        :param file_name: путь к файлу
        :param mode: режим записи в файл
        :return:
        """

        with open(file_name, mode, encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            f.write('\n\n')

    @classmethod
    def merge_data_after_controller_management_req(cls, data_hosts: dict, res_req: list[_asyncio.Task]) -> dict:
        """
        Метод объединяет данные полученные после запроса с данными data_host
        :param data_hosts: словарь с данными всех хостов
        :param res_req: результат выполнения запроса
        :return: обновленные data_hosts
        """

        logger.debug(data_hosts)
        for res in res_req:
            ip = res.get_name()
            errInd, varBinds, obj = res.result()
            assert ip == obj.ip_adress
            if errInd:
                data_hosts[ip][JsonResponceBody.REQ_ERRORS.value] = errInd.__str__()
            else:
                json_from_controller_management = obj.create_json(errInd, varBinds)
                cls.save_json_to_file(json_from_controller_management, 'controller_management.json', mode='a')
                data_hosts[ip][JsonResponceBody.PROTOCOL.value] = (
                    json_from_controller_management.get(JsonResponceBody.PROTOCOL.value)
                )
                try:
                    (data_hosts[ip]
                               [JsonResponceBody.RESP_ENTITY.value]
                               [JsonResponceBody.RAW_DATA.value]) = (
                        json_from_controller_management[JsonResponceBody.RESP_ENTITY.value]
                                                       [JsonResponceBody.RAW_DATA.value]
                    )
                except KeyError:
                    pass
                try:
                    data_hosts[ip][JsonResponceBody.TIME_REQ_CONTROLLER.value] = (
                        json_from_controller_management[JsonResponceBody.TIME_REQ_CONTROLLER.value]
                    )
                except KeyError:
                    pass
                try:
                    data_hosts[ip][JsonResponceBody.REQUEST_EXEC_TIME.value] = (
                        int(time.time() - data_hosts[ip][JsonResponceBody.START_TIME.value])
                    )
                except KeyError:
                    pass

        return data_hosts

    @staticmethod
    def create_base_struct(data_hosts: dict) -> dict:
        """
        Метод создаёт общую структуру для json responce
        :param data_hosts: данные всех хостов из api запроса
        :return: словарь с созданными структурами для всех хостов из api запроса
        """
        logger.debug(data_hosts)

        for ipAddr, data_host in data_hosts.items():
            data_hosts[ipAddr] = {
                JsonResponceBody.START_TIME.value: int(time.time()),
                JsonResponceBody.REQ_ERRORS.value: data_host.get(JsonResponceBody.REQ_ERRORS.value),
                JsonResponceBody.HOST_ID.value: data_host.get(JsonResponceBody.HOST_ID.value),
                JsonResponceBody.PROTOCOL.value: data_host.get(JsonResponceBody.PROTOCOL.value),
                JsonResponceBody.VALID_DATA_REQUEST.value: data_host.get(JsonResponceBody.VALID_DATA_REQUEST.value),
                JsonResponceBody.TYPE_CONTROLLER.value: data_host.get(JsonResponceBody.TYPE_CONTROLLER.value),
                JsonResponceBody.ADDRESS.value: data_host.get(JsonResponceBody.ADDRESS.value),
                JsonResponceBody.TYPE.value: data_host.get(JsonResponceBody.TYPE.value),
                JsonResponceBody.REQUEST_EXEC_TIME.value: data_host.get(JsonResponceBody.REQUEST_EXEC_TIME.value),
                JsonResponceBody.REQ_ENTITY.value: data_host.get(JsonResponceBody.REQ_ENTITY.value),
                JsonResponceBody.RESP_ENTITY.value: {
                    JsonResponceBody.RAW_DATA.value: None
                }
            }
        logger.debug(data_hosts)
        return data_hosts

    @staticmethod
    def add_end_time_to_data_hosts(data_hosts: dict) -> dict:
        """
        Метод добавляет в json responce время, затраченное на выполение запроса
        :param data_hosts: данные всех хостов
        :param start_time: начало выполнения запроса а api
        :return: все хосты с добавленным свойством JsonResponceBody.REQUEST_EXEC_TIME.value
        """

        for ipAddr, _ in data_hosts.items():
            data_hosts[ipAddr][JsonResponceBody.REQUEST_EXEC_TIME.value] = (
                int(time.time() - data_hosts[ipAddr][JsonResponceBody.START_TIME.value])
            )
        return data_hosts

    def remove_prop(self, data_hosts: dict, remove_prop: tuple | list, add_exec_time: bool = True) -> dict:
        """
        Метод удаляет свойтва у каждого data_host из коллекции data_hosts
        :param data_hosts: данные всех хостов
        :param remove_prop: свойства из основного тела, которые необходимо удалить
        :param add_exec_time: рассчёт свойства JsonResponceBody.REQUEST_EXEC_TIME.value
        :return: обновлённая коллекция data_hosts
        """

        for ipAddr, _ in data_hosts.items():
            for prop in remove_prop:
                try:
                    del data_hosts[ipAddr][prop]
                except KeyError:
                    pass
            if add_exec_time:
                data_hosts[ipAddr][JsonResponceBody.REQUEST_EXEC_TIME.value] = (
                    int(time.time() - data_hosts[ipAddr][JsonResponceBody.START_TIME.value])
                )
        return data_hosts


class ControllerManagementBase:
    """
    Базовый класс управления контроллерами
    """

    def get_controller_obj(
            self, ip_adress: str, type_object: tuple, matches: dict, scn: str = None, host_id: str = None
    ):
        """
        Создает экземпляр класса на type_object для получения данных/управления контроллером
        :param matches: соответствия типа дк/типа команды своему классу
        :param ip_adress: ip дресс хоста
        :param type_object: кортеж вида (тип контроллера, тип запроса)
        :param scn: SCN контроллера, если необходимо задать вручную. Иначе бужет получен по snmp запросу
        :param host_id: id хоста для responce
        :return: экзмепляр соответствующего класса
        """

        obj = None
        try:
            obj = matches.get(type_object)(ip_adress, host_id)
            if 'scn' in obj.__dict__:
                obj.scn = scn or None
            logger.debug('try:')
        except TypeError:
            logger.debug('except TypeError %s:' % matches.get(type_object))
            obj = matches.get(type_object)(ip_adress, host_id)
        except Exception as err:
            logger.critical(err)
        finally:
            logger.info(obj)
            return obj


class GetDataFromController(ControllerManagementBase):
    """
    Класс получения данных о текущем состоянии контроллера
    """

    matches = {
        (AvailableControllers.SWARCO.value, 'get_state'):
            controller_management.SwarcoGetModeWeb,
        (AvailableControllers.PEEK.value, 'get_state'):
            controller_management.PeekGetModeWeb,
        (AvailableControllers.PEEK.value, 'get_states'):
            controller_management.GetDifferentStatesFromWeb,
        (AvailableControllers.POTOK_P.value, 'get_state'):
            controller_management.PotokP,
        (AvailableControllers.POTOK_S.value, 'get_state'):
            controller_management.PotokS,
    }

    async def main(self, data_hosts: dict) -> dict:
        """
        Главный метод для отправки запросов о состоянии хостов
        :param data_hosts: хосты с собранными данными
        :return: список завершённых задач
        """

        objects = []
        logger.debug(data_hosts)
        async with asyncio.TaskGroup() as tg:
            for ipAddr, data_host in data_hosts.items():
                logger.debug(data_host.get(JsonResponceBody.REQ_ENTITY.value))
                if data_host.get(JsonResponceBody.REQ_ERRORS.value):
                    continue
                scn = data_host.get(JsonResponceBody.SCN.value)
                type_controller = data_host.get(JsonResponceBody.TYPE_CONTROLLER.value)
                host_id = data_host.get(JsonResponceBody.HOST_ID.value)
                req_entity = data_host.get(JsonResponceBody.REQ_ENTITY.value)[0]
                obj = self.get_controller_obj(ipAddr, (type_controller.upper(), req_entity), self.matches, scn, host_id)
                if obj is None:
                    (data_hosts[ipAddr]
                    [JsonResponceBody.REQ_ERRORS.value]) = ErrorMessages.INVALID_CONTROLLER_TYPE_REQ.value
                    continue
                objects.append(obj)
            result_request = [
                tg.create_task(obj.get_request(get_mode=True), name=obj.ip_adress) for obj in objects
            ]

        data_hosts = ResponceMaker.merge_data_after_controller_management_req(data_hosts, result_request)
        logger.debug(data_hosts)
        return data_hosts


class SetRequestToController(ControllerManagementBase):
    """
    Класс управления дорожным контроллером
    """

    matches_controller_instance = {
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.FLASH_BUTTON.value):
            controller_management.AsyncPushButtonSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.DARK_BUTTON.value):
            controller_management.AsyncPushButtonSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.LOCAL_BUTTON.value):
            controller_management.AsyncPushButtonSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.FLASH_MAN.value):
            controller_management.AsyncSetInputsSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.DARK_MAN.value):
            controller_management.AsyncSetInputsSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.STAGE_MAN.value):
            controller_management.AsyncSetInputsSwarcoSSH,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.FLASH_SNMP.value):
            controller_management.SwarcoSTCIP,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.DARK_SNMP.value):
            controller_management.SwarcoSTCIP,
        (AvailableControllers.SWARCO.value, AvailableSetCommandsController.STAGE_SNMP.value):
            controller_management.SwarcoSTCIP,
        (AvailableControllers.POTOK_S.value, AvailableSetCommandsController.STAGE_SNMP.value):
            controller_management.PotokS,
        (AvailableControllers.POTOK_S.value, AvailableSetCommandsController.FLASH_SNMP.value):
            controller_management.PotokS,
        (AvailableControllers.POTOK_S.value, AvailableSetCommandsController.DARK_SNMP.value):
            controller_management.PotokS,
        (AvailableControllers.POTOK_S.value, AvailableSetCommandsController.PROGRAM_RESTART.value):
            controller_management.PotokS,
        (AvailableControllers.POTOK_P.value, AvailableSetCommandsController.STAGE_SNMP.value):
            controller_management.PotokP,
        (AvailableControllers.POTOK_P.value, AvailableSetCommandsController.FLASH_SNMP.value):
            controller_management.PotokP,
        (AvailableControllers.POTOK_P.value, AvailableSetCommandsController.DARK_SNMP.value):
            controller_management.PotokP,
        (AvailableControllers.POTOK_P.value, AvailableSetCommandsController.PROGRAM_RESTART.value):
            controller_management.PotokP,

        (AvailableControllers.PEEK.value, AvailableSetCommandsController.STAGE_MAN.value):
            controller_management.PeekSetInputsWeb,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.STAGE_SNMP.value):
            controller_management.PeekUG405,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.FLASH_MAN.value):
            controller_management.PeekSetInputsWeb,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.DARK_MAN.value):
            controller_management.PeekSetInputsWeb,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.CP_RED.value):
            controller_management.PeekSetInputsWeb,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.FLASH_MAN.value):
            controller_management.PeekSetInputsWeb,
        (AvailableControllers.PEEK.value, AvailableSetCommandsController.USER_PARAMETERS.value):
            controller_management.PeekSetUserParametersWeb,
    }

    matches_commands = {
        'ЖМ КНОПКА': AvailableSetCommandsController.FLASH_BUTTON.value,
        'ОС КНОПКА': AvailableSetCommandsController.DARK_BUTTON.value,
        'ЛОКАЛ КНОПКА': AvailableSetCommandsController.LOCAL_BUTTON.value,
        'ФАЗА MAN': AvailableSetCommandsController.STAGE_MAN.value,
        'ОС MAN': AvailableSetCommandsController.DARK_MAN.value,
        'ЖМ MAN': AvailableSetCommandsController.FLASH_MAN.value,
        'ОС SNMP': AvailableSetCommandsController.DARK_SNMP.value,
        'ЖМ SNMP': AvailableSetCommandsController.FLASH_SNMP.value,
        'ФАЗА SNMP': AvailableSetCommandsController.STAGE_SNMP.value,
        'КК CP_RED': AvailableSetCommandsController.CP_RED.value,
        'ПАРАМЕТРЫ ПРОГРАММЫ': AvailableSetCommandsController.USER_PARAMETERS.value,
        'РЕСТАРТ ПРОГРАММЫ': AvailableSetCommandsController.PROGRAM_RESTART.value,
        'ПЕРЕЗАГРУЗКА ДК': AvailableSetCommandsController.REBOOT.value
    }

    async def main(self, data_hosts: dict) -> dict:
        """
        Метод для отправки команд управления дорожным контроллером и сбора информации о запросе
        :param data_hosts: хосты с собранными данными
        :return: список завершённых задач
        """
        objects_methods = []
        logger.debug(data_hosts)
        for ipAddr, data in data_hosts.items():
            if data.get(JsonResponceBody.REQ_ERRORS.value):
                continue
            logger.debug(data)
            host_id = data.get(JsonResponceBody.HOST_ID.value)
            scn = data.get(JsonResponceBody.SCN.value)
            type_controller = data.get(JsonResponceBody.TYPE_CONTROLLER.value).upper()
            type_command, set_val = list(data.get(JsonResponceBody.REQ_ENTITY.value).items())[0]
            type_command = self.matches_commands.get(type_command.upper(), type_command.upper())
            obj = self.get_controller_obj(
                ipAddr, (type_controller.upper(), type_command), self.matches_controller_instance, scn, host_id
            )
            if obj is None:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = ErrorMessages.INVALID_CONTROLLER_TYPE_REQ.value
                continue
            method = self._get_method(obj, type_command, set_val)
            if method is not None:
                objects_methods.append((method, ipAddr))
            else:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = ErrorMessages.INVALID_COMMAND_TYPE.value

        if objects_methods:
            async with asyncio.TaskGroup() as tg:
                result_request = [tg.create_task(task, name=ipAddr) for task, ipAddr in objects_methods]
            logger.debug(f'result-->>> {result_request}')
        # data_hosts = self.get_raw_data_responce_entity(result_request, data_hosts)
        data_hosts = ResponceMaker.merge_data_after_controller_management_req(data_hosts, result_request)
        logger.debug(data_hosts)
        return data_hosts

    def _get_method(self, obj, type_command: str, set_val: str = None) -> Coroutine | None:

        set_stage = {AvailableSetCommandsController.STAGE_MAN.value, AvailableSetCommandsController.STAGE_SNMP.value}
        set_flash = {
            AvailableSetCommandsController.FLASH_MAN.value,
            AvailableSetCommandsController.FLASH_SNMP.value,
            AvailableSetCommandsController.FLASH_BUTTON.value
        }
        set_dark = {
            AvailableSetCommandsController.DARK_MAN.value,
            AvailableSetCommandsController.DARK_SNMP.value,
            AvailableSetCommandsController.DARK_BUTTON.value
        }
        all_red = {AvailableSetCommandsController.CP_RED.value}
        set_user_params_peek_web = AvailableSetCommandsController.USER_PARAMETERS.value
        set_restart_programm = AvailableSetCommandsController.PROGRAM_RESTART.value

        logger.debug(f'Команда: {type_command}, Значение: {set_val}')

        method = None
        if type_command in set_stage:
            method = obj.set_stage(set_val)
        elif type_command in set_flash:
            method = obj.set_flash(set_val)
        elif type_command in set_dark:
            method = obj.set_dark(set_val)
        elif type_command in all_red:
            method = obj.set_allred(set_val)
        elif type_command == set_restart_programm:
            method = obj.set_restart_program(set_val or '1')
        elif type_command == set_user_params_peek_web:
            method = obj.set_user_parameters(params_string=set_val)
        return method


class FileDownLoad:
    """
    Класс обслуживания загрузки файлов конфигурации контроллеров
    """

    swarco_config_path = os.getenv('path_to_itc_config_xml')

    @staticmethod
    def save_file_to_db(path: str, ipAddr: str, data: dict, source: str, description: str) -> SaveConfigFiles:
        """
        Метод сохранения файла конфигурации в бд
        :param description: описание источника сохранения файла
        :param source: назначение файла(created/uploaded)
        :param ipAddr: IPv4 хоста
        :param path: путь к конфигу(Swarco)/каталогу проекта(Peek)
        :param data: данные о хосте
        :return: None
        """

        f = SaveConfigFiles(source=source, file=path,
                            controller_type=data.get(JsonResponceBody.TYPE_CONTROLLER.value),
                            description=description,
                            address=data.get(JsonResponceBody.ADDRESS.value),
                            ip_adress=ipAddr,
                            number=data.get(JsonResponceBody.HOST_ID.value))
        f.file.name = correct_path_for_db(f.file.path)
        f.save()
        return f

    async def download_file(self, data_hosts: dict) -> dict:
        """
        Метод загрузки файла конфигурации с дорожного контроллера. Swarco -> scp, Peek -> ftp
        :param data_hosts: данные о хостах
        :return: результаты загрузки файла
        """

        logger.debug(data_hosts)
        obj_swarco_async, obj_peek_sync, result_async_request, result_sync_request = [], [], [], [],
        async with asyncio.TaskGroup() as tg:
            for ipAddr, data_host in data_hosts.items():
                if data_host.get(JsonResponceBody.REQ_ERRORS.value) is not None:
                    continue
                if data_host.get(JsonResponceBody.TYPE_CONTROLLER.value).upper() == AvailableControllers.SWARCO.value:
                    obj_swarco_async.append(controller_management.SwarcoSSHBase(ipAddr))
                elif data_host.get(JsonResponceBody.TYPE_CONTROLLER.value).upper() == AvailableControllers.PEEK.value:
                    # obj_peek_sync.append()... не реализовано
                    pass
                else:
                    continue
            if obj_swarco_async:
                data_hosts[ipAddr][JsonResponceBody.PROTOCOL.value] = JsonResponceBody.SSH.value
                result_async_request = [
                    tg.create_task(obj.adownload_scp(access_level='swarco_r',
                                                     files=[self.swarco_config_path],
                                                     dest_path=MEDIA_ROOT2 / 'uploaded_configs'),
                                   name=obj.ip_adress) for obj in obj_swarco_async
                ]

            if obj_peek_sync:
                # логика скачивания для Пика по ftp еще не реализована
                result_sync_request = []
            res = result_async_request + result_sync_request

        logger.debug(result_async_request)
        for data_host in res:
            errIndication, src, obj = data_host.result()
            if errIndication:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = errIndication
                continue
            if isinstance(obj, controller_management.SwarcoSSHBase):
                manager = ITC_PC_config.SwarcoParseConfigXML(
                    f'{src}/{ITC_PC_config.SwarcoParseConfigXML.xml_itc_config_name}'
                )
                errIndication, data = manager.create_PTC2(src)
                # data[0] -> path к конфигу, data[1] -> доп. сведения. В случае Swarco -> словарь с данными из
                # itc-config.xml "general"(кол-во групп, id_backplaine и т.д.)

                if errIndication:
                    data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = errIndication
                    continue
            else:
                data = [None, None]  # Заглушка
                pass  # Тут должно быть что то для Пика, возможно отдельный класс, в котором упаковываются файлы в архив
            data_hosts[obj.ip_adress][JsonResponceBody.DOWNLOAD_DATA.value] = data
        logger.debug(data_hosts)
        return data_hosts

    async def main(self, data_hosts: dict) -> dict:
        """
        Метод загрузки файла конфигурации с дорожного контроллера. Swarco -> scp, Peek -> ftp
        :param data_hosts: данные о хостах
        :return: результаты загрузки файла
        """

        logger.debug(data_hosts)
        obj_swarco_async, obj_peek_sync, result_async_request, result_sync_request = [], [], [], [],
        async with asyncio.TaskGroup() as tg:
            for ipAddr, data_host in data_hosts.items():
                if data_host.get(JsonResponceBody.REQ_ERRORS.value) is not None:
                    continue
                if data_host.get(JsonResponceBody.TYPE_CONTROLLER.value).upper() == AvailableControllers.SWARCO.value:
                    obj_swarco_async.append(controller_management.SwarcoSSHBase(ipAddr))
                elif data_host.get(JsonResponceBody.TYPE_CONTROLLER.value).upper() == AvailableControllers.PEEK.value:
                    # obj_peek_sync.append()... не реализовано
                    pass
                else:
                    continue
            if obj_swarco_async:
                data_hosts[ipAddr][JsonResponceBody.PROTOCOL.value] = JsonResponceBody.SSH.value
                result_async_request = [
                    tg.create_task(obj.adownload_scp(
                        access_level='swarco_r',
                        files=[self.swarco_config_path],
                        dest_path=MEDIA_ROOT2 / 'uploaded_configs'),
                        name=obj.ip_adress
                    ) for obj in obj_swarco_async
                ]

            if obj_peek_sync:
                # логика скачивания для Пика по ftp еще не реализована
                result_sync_request = []
            res = result_async_request + result_sync_request

        logger.debug(result_async_request)
        for data_host in res:
            errIndication, src, obj = data_host.result()
            if errIndication:
                data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = errIndication
                continue
            if isinstance(obj, controller_management.SwarcoSSHBase):
                manager = ITC_PC_config.SwarcoParseConfigXML(
                    f'{src}/{ITC_PC_config.SwarcoParseConfigXML.xml_itc_config_name}'
                )
                errIndication, data = manager.create_PTC2(src)
                # data[0] -> path к конфигу, data[1] -> доп. сведения. В случае Swarco -> словарь с данными из
                # itc-config.xml "general"(кол-во групп, id_backplaine и т.д.)

                if errIndication:
                    data_hosts[ipAddr][JsonResponceBody.REQ_ERRORS.value] = errIndication
                    continue
            else:
                data = [None, None]  # Заглушка
                pass  # Тут должно быть что то для Пика, возможно отдельный класс, в котором упаковываются файлы в архив
            data_hosts[obj.ip_adress][JsonResponceBody.DOWNLOAD_DATA.value] = data
        logger.debug(data_hosts)
        return data_hosts

    def make_zip_archive(self, path_to_config: str, ipAddr: str, host_id: str, type_controller: str) -> pathlib.Path:
        """
        Метод упаковывает в zip архив конфига/катлога проекта контроллера
        :param path_to_config: пусть к конфигу/каталогу проекта
        :param ipAddr: строковое представление ipv4 контроллера
        :param host_id: id контроллера(номер со/произвольное название)
        :param type_controller: тип контроллера: Swarco/Peek
        :return: Пусть к упакованному zip архиву
        """

        parent_dir = pathlib.Path('/'.join(path_to_config.split('/')[:-1]))
        path_for_send = pathlib.Path(f'{parent_dir}/for_send')
        os.makedirs(path_for_send)
        for file in parent_dir.iterdir():
            if not file.is_dir() and '.xml' not in file.name:
                shutil.copy(file, path_for_send)
        z_arch = pathlib.Path(f'{parent_dir}/{ipAddr} {host_id or ""}_{type_controller}.zip')
        with zipfile.ZipFile(z_arch, "w", zipfile.ZIP_DEFLATED) as z:
            for file in path_for_send.iterdir():
                if '.xml' not in file.name:
                    z.write(file, arcname=file.name)
        return z_arch

    def create_zip_archive_and_save_to_db_multiple(self, data_hosts: dict) -> dict:
        """
        Метод упаковывает скачанные конфиги/каталоги проектов и сохраняет их в бд, а также
        добавляет в словарь информацию о хосте
        :param data_hosts: словарь со всеми хостами
        :param res_download: результат загрузки
        :return: обновленный словарь с данными о хостах
        """
        logger.debug('create_zip_archive_and_save_to_db_multiple')

        for ipAddr, data_host in data_hosts.items():
            # data[0] -> path к конфигу, data[1] -> доп. сведения. В случае Swarco -> словарь с данными из
            # itc-config.xml "general"(кол-во групп, id_backplaine и т.д.)
            if data_hosts.get(ipAddr).get(JsonResponceBody.REQ_ERRORS.value) is not None:
                continue
            # data: список, где data[0] -> путь к скачанному(Peek)/созданному(Swarco .PTC2) файлу,
            # data[1] -> словарь полезных данных, в Swarco это general из xml
            path_to_file = data_host.get(JsonResponceBody.DOWNLOAD_DATA.value)[0]
            self.save_file_to_db(
                path_to_file, ipAddr, data_host, Database.CREATED.value, Database.DESCR_UPLOAD_CONFIG.value
            )
            res_make_zip = self.make_zip_archive(
                path_to_file, ipAddr,
                data_host.get(JsonResponceBody.HOST_ID.value),
                data_host.get(JsonResponceBody.TYPE_CONTROLLER.value)
            )
            # data_host[JsonResponceBody.PATH_TO_ARHIVE.value] = res_make_zip
            # saved_archive = self.save_file_to_db(str(res_make_zip), ipAddr, data_host)

            saved_archive = self.save_file_to_db(
                str(res_make_zip), ipAddr, data_host, Database.CREATED.value, Database.DESCR_CREATE_ARCHIVE.value
            )
            data_host[JsonResponceBody.RESP_ENTITY.value][JsonResponceBody.PATH_TO_URL.value] = {
                str(res_make_zip.name): saved_archive.file.url
            }
            data_host[JsonResponceBody.MODEL_OBJ.value] = saved_archive
            # data_host[JsonResponceBody.RESP_ENTITY.value][JsonResponceBody.PATH_TO_URL.value] = self.save_archive_to_db(
            #     res_make_zip, data_host
            # )
            (data_host[JsonResponceBody.RESP_ENTITY.value]
            [JsonResponceBody.RAW_DATA.value]) = data_host.get(JsonResponceBody.DOWNLOAD_DATA.value)[1]
            del data_host[JsonResponceBody.DOWNLOAD_DATA.value]
            # del data_host[JsonResponceBody.PATH_TO_ARHIVE.value]
            data_hosts[ipAddr] = data_host
        logger.debug(data_hosts)
        return data_hosts


class TelegrammBot:
    """
    Класс для работы с телеграмм ботом
    """

    token = os.getenv('SDP_BOT')
    send_document = 'sendDocument'
    send_message = 'sendDocument'

    def add_data_to_datahosts(self, data_hosts: dict, res_send_file: list[_asyncio.Task]) -> dict:
        """
        Метод собирает данные для responce в ответное сообщение пользователю telegramm, отправившему запрос
        :param data_hosts: данные с хостами
        :param res_send_file: результат с данными(заершённые задачи)
        :return: обновлённый словарь с данными о хостах
        """

        for res in res_send_file:
            logger.debug(res.result())
            ip = res.get_name()
            curr_host = data_hosts.get(ip)
            curr_host['responce_tlg'] = res.result()
            # del curr_host['obj']
        logger.debug(data_hosts)
        return data_hosts

    # def collect_data_for_responce(self, data_hosts: dict, res_send_file: list[_asyncio.Task]) -> dict:
    #     """
    #     Метод собирает данные для responce в ответное сообщение пользователю telegramm, отправившему запрос
    #     :param data_hosts: данные с хостами
    #     :param res_send_file: результат с данными(заершённые задачи)
    #     :return: обновлённый словарь с данными о хостах
    #     """
    #
    #     for res in res_send_file:
    #         logger.debug(res.result())
    #         ip = res.get_name()
    #         curr_host = data_hosts.get(ip)
    #         curr_host['responce_tlg'] = res.result()
    #         curr_host['protocol'] = 'ssh/ftp'
    #         del curr_host['path_to_archive']
    #         curr_host['raw_data_for_responce'] = {
    #             'intersection': curr_host.get('intersection'),
    #             'owner': curr_host.get('owner'),
    #             'controller-id': curr_host.get('controller-id'),
    #             'backplane-id': curr_host.get('backplane-id'),
    #         }
    #     logger.debug(data_hosts)
    #     return data_hosts

    async def send_request(self, chat_id: str, token=None, send_message=None, send_file=None, timeout=4) -> dict:
        """
        Отправка ответа пользователю отправившему запрос в telegramm через http запрос
        :param chat_id: чат id пользователя
        :param token: токен бота, по дефолту из env
        :param send_message: тип отправки -> сообщение
        :param send_file: тип отправки -> файл
        :param timeout: таймаут http сессии
        :return: telegramm json от http запроса
        """

        token = token or self.token
        if send_file:
            data = {'document': open(send_file, 'rb')}
            url = f'https://api.telegram.org/bot{token}/sendDocument?chat_id={chat_id}'
        elif send_message:
            url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}'
            data = {'parse_mode': 'MarkdownV2', 'text': send_message}
        else:
            raise ValueError('Не выбран тип запроса')

        timeout = aiohttp.ClientTimeout(timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=data) as s:
                return await s.json()

    async def send_file(self, chat_id: str, path_to_file: str, timeout=4, token: str = None) -> dict:
        """
        Метод отправляет файл пользователю отправившему запрос в telegramm через http запрос
        :param chat_id: чат id пользователя
        :param path_to_file: путь к zip архиву
        :param timeout: таймаут http сессии
        :param token: токен бота, по дефолту из env
        :return: telegramm json от http запроса
        """
        token = token or self.token
        res = await self.send_request(
            chat_id, token, send_file=path_to_file, timeout=timeout
        )
        return res

    async def send_message(self, chat_id: str, path_to_file, timeout=4, token=None):
        token = token or self.token
        logger.debug(chat_id, path_to_file)
        await self.send_request(
            chat_id, token, path_to_file,
        )

    async def main(
            self, data_hosts: dict, chat_id: str, send_message=None, send_file=None
    ) -> dict:
        """
        Метод групповой отправки ответного сообщения пользователю отправившему запрос в telegramm через http запрос
        :param chat_id:
        :param data_hosts: данные со всеми хостами
        :param send_message: тип отправки запроса текстовое сообщение
        :param send_file: тип отправки запроса файл
        :return: обновленные данные, готовые для json responce
        """

        logger.debug('---main----')
        async with asyncio.TaskGroup() as tg:
            res = [
                tg.create_task(
                    self.send_file(chat_id, data_host.get(JsonResponceBody.MODEL_OBJ.value).file.path),
                    name=ipAddr
                )
                for ipAddr, data_host in data_hosts.items() if data_host.get(JsonResponceBody.REQ_ERRORS.value) is None
            ]

        logger.debug(res)
        data_hosts = self.add_data_to_datahosts(data_hosts, res)
        logger.debug(data_hosts)
        return data_hosts


class CommonTables(metaclass=abc.ABCMeta):
    """
    Абстрактный базовый класс для определения классов как представления той или иной
    таблицы паспорта.
    """

    def __init__(self, raw_data_from_table: str, create_properties=False):
        self.raw_data = raw_data_from_table
        self.group_table = None
        self.stages_table = None
        self.num_groups = None
        self.responce = None
        if create_properties:
            self.create_properties()

    @abc.abstractmethod
    def create_properties(self, *args, **kwargs):
        """
        Метод для создания свойств какой - либо таблицы из паспорта
        :return:
        """
        ...

    @abc.abstractmethod
    def create_responce(self, *args, **kwargs):
        """
        Метод формирует словарь для json-responce
        :return:
        """
        ...

    def separators_is_valid(self, data: str, num_separators: int, required_separator: str = '\t') -> bool:
        return True if num_separators == data.count(required_separator) else False


class GroupTable(CommonTables):
    """
    Интерфейс преобразования сырых данных из "Таблицы направлений"
    в свойства направлений для сравнения с другими таблицами паспорта.
    """

    def create_properties(self, data: str = None):
        """
        Формирует свойства таблицы на основе "Таблицы направлений"
        :return: словарь со свойствами направлений
        """

        self.group_table = self._create_groups_table(self.raw_data)
        logger.debug(self.stages_table)
        logger.debug(self.group_table)

    def _create_groups_table(self, data: str, separator: str = '\t') -> Dict:

        table_groups = {}
        try:
            for line in (group.split(separator) for group in data.replace(' ', '').splitlines() if group):
                num_group, name_group, stages = line
                if not num_group or not name_group or not stages:
                    print('[cma[sc')
                    continue
                determinant_always_red = {'красн', 'Пост.красное', 'красное', '-'}
                group_properties = {
                    'type_group': name_group,
                    'always_red': any(fragment in stages.lower() for fragment in determinant_always_red),
                    'stages': sorted(stages.split(',')),
                    'ok': True,
                    'errors': []
                }
                table_groups[num_group] = group_properties
        except ValueError:
            return {}
        ResponceMaker.save_json_to_file(table_groups, 'table_groups_new.json')
        return table_groups if self.separators_is_valid(data=data, num_separators=len(table_groups) * 2) else {}

    def create_stages_table(self):
        pass

    def create_responce(self, has_errors: str, err_in_user_data: str) -> Dict:
        """
        Формирует словарь для json-responce
        :param has_errors: Наличие ошибкок после расчёта.
        :param err_in_user_data: Валидность входящих данных от пользователя
        :return: словарь для json-responce
        """

        responce = {
            'compare_groups': {
                'groups_info': self.group_table,
                'has_errors': has_errors,
                'error_in_user_data': err_in_user_data
            }
        }
        self.responce = responce
        return responce


class StagesTable(CommonTables):
    """
    Интерфейс преобразования сырых данных из "Программы(таблица фаз)"
    в свойства направлений для сравнения с другими таблицами паспорта.
    """

    def create_properties(self, create_group_table: bool = False):
        """
        Формирует свойства таблицы, необходимые для сравнения с таблицей фаз
        :return: словарь вида {фаза: направления в фазе}
            Пример: {'1': '1,2,3,4,5,6', '2': '1,2,3,4,5,6', '3': '2,3,4,6,10', '4': '4,7,8,9',
                     '5': '7,8,9,11', '6': '1,2,3,4,6,10'}
        """

        self.stages_table = self._create_stage_table(self.raw_data)
        logger.debug(self.stages_table)
        if create_group_table:
            self.group_table = self._create_groups_table(self.stages_table)
        else:
            self.group_table = {}
        logger.debug(self.group_table)

    def _create_stage_table(self, data: str, separator: str = '\t') -> Dict[str, list]:
        """
        Фомирует словарь с принадлежностью напралвений к фазе
        :param data: строка сырых данных с разделителем r'\t' по умолчанию.
                 Пример: '1\t1,2,3,4,5,6\n2\t1,2,3,4,5,6\n3\t2,3,4,6,10\n4\t4,7,8,9\n5\t7,8,9,11\n6\t1,2,3,4,6,10\n\n'
        :return: словарь вида {Фаза: направления в фазе}.
                 Пример:
                 {'1': ['1', '2', '3', '4', '5', '6'], '2': ['1', '2', '3', '4', '5', '6'],
                 '3': ['2', '3', '4', '6', '10'], '4': ['4', '7', '8', '9'],
                 '5': ['7', '8', '9', '11'], '6': ['1', '2', '3', '4', '6', '10']}
        """

        table_stages = {}
        try:
            for stage_prop in (stage.split(separator) for stage in data.replace(' ', '').splitlines() if stage):
                if not stage_prop:
                    continue
                num_stage, groups_in_stage = stage_prop
                table_stages[num_stage] = groups_in_stage.split(',')
            logger.debug(table_stages)
        except ValueError:
            return {}
        return table_stages if self.separators_is_valid(data=data, num_separators=len(table_stages)) else {}

    def _create_groups_table(self, data: Dict[str, list]) -> Dict[str, list]:
        """
        Формирует данные для колонки "Фазы в которых участвует направление" паспорта
        :param data:
        :param num_groups:
        :return:
        """

        if not data:
            return {}
        groups = set()
        # Сформировать множество наименований групп
        for group in functools.reduce(lambda x, y: x + y, data.values()):
            try:
                groups.add(int(group))
            except ValueError:
                groups.add(float(group))
        logger.debug(data)
        # Сформировать словарь в принадлежностью группы к фазам:
        # {'1': ['1', '2', '3', '4', '5', '6'], '2': ['1', '2', '3', '4', '5', '6'] ... }
        groups_in_stages = {group: set() for group in map(str, sorted(groups))}
        for _group in groups_in_stages:
            for _stage, _group_in_stages in data.items():
                if _group in _group_in_stages:
                    groups_in_stages[_group].add(_stage)
                continue
            groups_in_stages[_group] = sorted(groups_in_stages[_group])
        return groups_in_stages

    def create_responce(self, has_errors: str, err_in_user_data: str) -> Dict:
        """
        Формирует словарь для json-responce
        :param has_errors: Наличие ошибкок после расчёта.
        :param err_in_user_data: Валидность входящих данных от пользователя
        :return: словарь для json-responce
        """

        responce = {
            'make_groups_in_stages': {
                'calculate_result': self.group_table,
                'has_errors': has_errors,
                'error_in_user_data': err_in_user_data
            }
        }
        self.responce = responce
        return responce


class PassportProcessing:
    """
    Интерфейс для сравнения и расчёта различных данных из паспорта объекта
    """

    def __init__(self, raw_table_groups=None, raw_table_stages=None):
        self.raw_table_groups = raw_table_groups
        self.raw_table_stages = raw_table_stages

    def compare_groups_in_stages(self) -> Tuple[GroupTable, bool, None | str]:
        """
        Проверяет на эквивалентность принадлежности группы к фазами количества групп в двух таблицах паспорта:
        таблицы направлений и таблицы временной программы
        :param src_group_table: строка с данными из "Таблицы направлений".
               Пример: '1\tТранспортное\t1,2\n2\tТранспортное\t1,2,7\n3\tТранспортное\t4\n4\tТранспортное\t4,
                        5\n5\tПоворотное\t3,6,7\n6\tОбщест.трансп\t3,6\n7\tПешеходное\t3,6\n8\tПоворотное\t3,5,6,7\n
                        9\tПоворотное\t5\n10\tПешеходное\t4\n11\tПоворотное\t1,5\n12\tТранспортное\tПост. красное\n13\
                        tПешеходное\t2,4,7\n'
        :param src_stages_table: строка с данными из "Временной программы"
               Пример: '1\t1,2,11\n2\t1,2,13\n3\t5,6,7,8\n4\t3,4,10,13\n5\t4,8,9,11\n6\t5,6,7,8\n7\t2,5,8,13\n\n'
        :return: Словарь для json-responce вида:
        """

        table_groups = GroupTable(self.raw_table_groups, create_properties=True)
        table_stages = StagesTable(self.raw_table_stages, create_properties=True)
        err_in_user_data = self._check_valid_user_data_compares_groups(table_groups, table_stages)
        has_errors = False

        if err_in_user_data is not None:
            has_errors = True
            return table_groups, has_errors, err_in_user_data

        for num_group, properties in table_groups.group_table.items():
            if properties.get('always_red'):
                continue
            error_groups_discrepancy = self._compare_groups_discrepancy(
                properties.get('stages'), num_group, table_stages
            )
            if error_groups_discrepancy is not None:
                table_groups.group_table[num_group]['errors'] = error_groups_discrepancy
                table_groups.group_table[num_group]['ok'] = False
                has_errors = True
        return table_groups, has_errors, err_in_user_data

    def create_groups_in_stages_content(self) -> Tuple[StagesTable, bool, None | str]:
        """
        Формирует свойства в виде словаря для расчёта принадлежности групп к фазам, для
        "Табблицы направлений", колонок "№ нап.", "Тип направления"	"Фазы, в кот. участ. направл."
        :return: кортеж  вида: (instance класса StagesTable, наличие ошибок после расчёта, наличие ошибок в
                 пользовательских данных)
        """

        table_stages = StagesTable(self.raw_table_stages)
        table_stages.create_properties(create_group_table=True)
        err_in_user_data = self._check_valid_user_data_groups_in_stages_content(table_stages)
        has_errors = False
        if err_in_user_data is not None:
            has_errors = True
        return table_stages, has_errors, err_in_user_data

    def get_result(self, options: List[str]) -> Dict:
        """
        Метод выполняет роль менеджера: получает на вход список опций, каждой из которых соответсвует
        свой метод. Далее для каждой опции вызывает соответсвуйщий метод из self._get_method,
        после чего формирует общий responce для всех вызванных методов.
        :param options: Список строк с опциями, например: [compare_groups, calc_groups_in_stages]
        :return: Словарь для responce
        """

        responce = {}
        try:
            for result in map(lambda option_: self._get_method(option_)(), options):
                obj, has_errors, err_in_user_data = result
                responce |= obj.create_responce(has_errors, err_in_user_data)
        except TypeError:
            return responce
        return responce

    def _compare_groups_discrepancy(
            self, table_groups_stages: List, name_group: str, table_stages: StagesTable
    ) -> None | List[str]:
        """
        Проверяет соответствие приадлежности группы к фазе в "Таблице направлений" и
        таблицы "Временная программа"(таблица фаз)
        :param table_groups_stages: фазы из колонки "Фазы, в кот. участ. направ."
        :param name_group: группа, для которой будет осуществляться проверка соответсвия принадлжености.
        :param table_stages: instance класса StagesTable
        :return: Если есть несоответствия, вернёт list с текстами пояснения несоответствий, иначе None
        """

        #
        # if stages_table_group is None:
        #     continue  # добавить проверку. возможно добавить ошибку в errors что список фаз не может быть пусттым
        errors = []
        for num_stage in table_groups_stages:
            for stage_, groups_in_stage in table_stages.stages_table.items():
                curr_error = None
                if num_stage == stage_ and name_group not in groups_in_stage:
                    curr_error = (
                        f'Группа присутствует в таблице направлений(<Фазы, в кот. участ. направ>), '
                        f'но отсутствует таблице фаз. '
                        f'Группа={name_group}, Фаза={num_stage}'
                    )
                elif num_stage != stage_ and name_group in groups_in_stage and stage_ not in table_groups_stages:
                    curr_error = (
                        f'Группа присутствует в таблице фаз, но отсутствует в таблице направлений. '
                        f'Группа={name_group}, Фаза={stage_}'
                    )
                elif num_stage not in table_stages.stages_table:
                    curr_error = (
                        f'Группа присутствует в таблице направлений(<Фазы, в кот. участ. направ>), '
                        f'но отсутствует таблице фаз. '
                        f'Группа={name_group}, Фаза={num_stage}'
                    )
                if curr_error is not None and curr_error not in errors:
                    errors.append(curr_error)
        return errors or None

    def _check_valid_user_data_compares_groups(
            self, table_groups: GroupTable, table_stages: StagesTable
    ) -> None | str:
        """
        Проверяет корректность обработки входных данных из "Таблицы направления" и "Временной программы",
        полученные от клиента и формирует текст ошибки.
        Если словарь table_groups.group_table и/или table_stages.stages_table
        пустой, значит полльзоваетелем были предоставлены некорректные данные.
        :param table_groups: instance класса GroupTable
        :param table_stages: instance класса StagesTable
        :return: Текст ошибки err, если данные невалидны для обработки, иначе None
        """

        err = None
        if not table_groups.group_table and not table_stages.stages_table:
            err = 'Предоставлены некоррекнтные данные таблицы направлений и таблицы фаз(временной программы)'
        elif not table_groups.group_table:
            err = 'Предоставлены некоррекнтные данные таблицы направлений'
        elif not table_stages.stages_table:
            logger.debug(table_stages)
            err = 'Предоставлены некоррекнтные данные таблицы фаз(временной программы)'
        return err

    def _check_valid_user_data_groups_in_stages_content(self, table_stages: StagesTable, err=None) -> None | str:
        """
        Проверяет валидность пользовательских(входных) данных для расчёта принадлежности направоений к фазам.
        :param table_stages: instance класса StagesTable
        :param err: Сущность ошибки
        :return: При некорректных входных данных строку с ошибкой, иначе None
        """

        if not table_stages.group_table or not table_stages.stages_table:
            err = 'Предоставлены некоррекнтные данные таблицы направлений'
        return err

    def _get_method(self, option: str) -> Callable:
        """
        Вовращает метод, сопоставленный переданной опции
        :param option: опция в строковом представлении
        :return: метод, который соответсвует переданной опции
        """

        matches = {
            'compare_groups': self.compare_groups_in_stages,
            'calc_groups_in_stages': self.create_groups_in_stages_content
        }
        return matches.get(option)


class TrafficLightConfiguratorPotok(metaclass=abc.ABCMeta):
    def __init__(self, condition_string):
        self.condition_string = condition_string

    @abc.abstractmethod
    def write_data_to_db(self):
        """
        Записывает в бд результаты выполнения функции
        :return:
        """
        ...


class GetFunctionsPotokTrafficLightsConfigurator(TrafficLightConfiguratorPotok):
    function_name = 'Извлечь функции'

    def __init__(self, condition_string):
        super().__init__(condition_string)
        self.functions = None
        self.errors = []

    def get_functions(self) -> List:
        """
        Формирует список с функциями(токенами) из self.condition_string и записывает результат в бд
        :return: Список с функциями(токенами) из self.condition_string
        """

        self.functions = potok_user_api.Tokens(self.condition_string).get_tokens()
        self.write_data_to_db()
        return self.functions

    def write_data_to_db(self) -> None:
        """
        Записывает результат получения функций(токенов) в бд
        :return: None
        """

        TrafficLightConfigurator.objects.create(
            function=self.function_name,
            condition_string=self.condition_string,
            tokens=self.functions,
            errors=', '.join(e for e in self.errors) if self.errors else ''
        )


class GetResultCondition(TrafficLightConfiguratorPotok):
    """
    Интерфейс проверки условия продления/перехода из tlc контроллера Поток
    """

    function_name = 'Значение условия'

    def __init__(self, condition_string: str, func_values: Dict):
        super().__init__(condition_string)
        self.func_values = func_values
        self.current_result = None
        self.condition_string_for_parse = None
        self.errors = []

    def get_condition_result(self, func_values: Dict = None):
        """
        Получет результат условия вызова/продления выражения tlc контроллера Поток.
        :param func_values: значения функций, которые будут подставлены в условие вызова/продления
        :return: True, если условие выподняется при наборе func_values, иначе False
        """

        func_vals = func_values or self.func_values
        if self.check_valid_funcs_from_condition() and not self.errors:
            request = potok_user_api.ConditionResult(self.condition_string)
            self.current_result = request.get_condition_result(func_vals)
            self.condition_string_for_parse = request.condition_string_for_parse
        self.write_data_to_db()
        return self.current_result

    def check_valid_funcs_from_condition(self) -> bool:
        """
        Проверят валидность функций(токенов) из условия вызова/продления выражения tlc контроллера Поток с
        self.func_values из переданного запроса.
        :return: True, если набор функций одинаков, иначе False
        """

        curr_tokens = potok_user_api.Tokens(self.condition_string).get_tokens()
        logger.debug(f'curr_tokens: {curr_tokens}')
        logger.debug(f'list(self.func_values.items(): {list(self.func_values.items())}')
        if curr_tokens != list(self.func_values.keys()):
            self.errors.append('Ошибка данных: функции из условия продления/вызова и функции с переданными значениями '
                               'различны. Сформируйте заново функции из строки условия перехода/продления')
            return False
        return True

    def write_data_to_db(self) -> None:
        """
        Записывает результат получения значения условия продления/перехода из tlc в бд
        :return:  None
        """

        TrafficLightConfigurator.objects.create(
            function=self.function_name,
            condition_string=self.condition_string,
            condition_string_for_parse=self.condition_string_for_parse or '',
            function_values=self.func_values,
            result_condition_value=self.current_result,
            errors=', '.join(e for e in self.errors) if self.errors else ''
        )


class DatabaseAPI:
    """
    API базы данных
    """

    @classmethod
    def save_txt_conflicts(
            cls, path_to_file: str, source: str = 'created', description: str = 'конфликты и фазы txt'
    ) -> SaveConfigFiles:
        """
        Сохраняет запись в бд модели SaveConfigFiles о созданном txt-файле с расчётами конфликтов и фаз.
        :param path_to_file: Путь к txt фазйлу.
        :param source: Контент поля source для txt-файла модели SaveConfigFiles .
        :param description: Контент поля description модели SaveConfigFiles
        :return: Экземпляр сохранённой записи
        """

        f = SaveConfigFiles(source=source, file=path_to_file, description=description)
        f.file.name = correct_path_for_db(f.file.path)
        f.save()
        return f

    @classmethod
    def save_config(
            cls,
            file: str | InMemoryUploadedFile,
            controller_type: str,
            source: str,
            description: str = None,
            address: str = None,
            ip_adress: str = None,
            number: str = None
    ) -> SaveConfigFiles:
        """
        Сохраняет запись в бд модели SaveConfigFiles о созданном конфигурационном файле/архиве.
        :param source: Контент поля source для txt-файла модели SaveConfigFiles.
        :param file: Путь к txt файлу.
        :param description: Контент поля description модели SaveConfigFiles.
        :param address: Контент поля address модели SaveConfigFiles.
        :param ip_adress: Контент поля ip_adress модели SaveConfigFiles.
        :param number: Контент поля number модели SaveConfigFiles.
        :return: Экземпляр сохранённой записи.
        """

        f = SaveConfigFiles(
            source=source,
            file=file,
            controller_type=controller_type,
            description=description,
            address=address,
            ip_adress=ip_adress,
            number=number
        )
        f.file.name = correct_path_for_db(f.file.path)
        f.save()
        return f


class ConflictsAndStages:
    """
    Расчёт конфликтов, фаз, а также других свойств для формирования файла конфигурации дорожного контроллера.
    """

    def __init__(
            self,
            raw_stages_groups: str | Dict,
            type_controller: str,
            create_txt=False,
            scr_original_config: InMemoryUploadedFile = None
    ):
        self.errors = []
        self.raw_data_stages_groups = raw_stages_groups
        self.stages_groups = self._get_data_stages_groups_dict(raw_stages_groups)
        self.type_controller = type_controller
        self.create_txt = create_txt
        self.uploaded_file_obj = self._save_config_to_db(scr_original_config)
        self.instance_data = None

    def _get_api_class(self, matching_data: str):
        """
        Возвращает необходимый класс для расчёта конфликтов и фаз на основе переданных типа контроллера
        :param matching_data: Словаорь с соответствиями типа контроллера классу для расчётов.
        :return: Необходимый для расчётов класс
        """

        matches_aclass = {
            AvailableControllers.SWARCO.value.lower(): SwarcoConflictsAndStagesAPI,
            AvailableControllers.PEEK.value.lower(): PeekConflictsAndStagesAPI,
            'common': CommonConflictsAndStagesAPI,
        }
        return matches_aclass.get(matching_data)

    def _get_data_stages_groups_dict(self, data_stages_groups: str | Dict) -> Dict:
        """
        Конвертирует данные "фаза: направления" из str в dict. Если data_stages_groups является str,
        например: '1,5\n3,4\n\n6,9,10', то будет сконвертирована: {'1': '1,5', '2': '3,4', '3': '', '4': '6,9,10'}.
        Если data_stages_groups является dict, то просто возвращает себя.
        :param data_stages_groups: Строка или словарь с привязкой фаза: направления
        :return: Словарь с привязкой фаза: направления
        """

        if isinstance(self.raw_data_stages_groups, str):
            return calculate_conflicts.Utils.stages_to_dict(data_stages_groups)
        elif isinstance(self.raw_data_stages_groups, dict):
            return data_stages_groups
        else:
            self.errors.append('Предоставлены некорректные данные для расчёта')

    def _get_path_to_save_txt_file(self) -> str:
        """
        Формирует путь для сохранения txt файла с расчитанными конфликтами и фазами
        :return:
        """

        return f'{MEDIA_ROOT2}/conflicts/txt/сalculated_conflicts {dt.now().strftime("%d %b %Y %H_%M_%S")}.txt'

    def _save_config_to_db(self, config: InMemoryUploadedFile | str) -> SaveConfigFiles | None:
        """
        Сохраняет загруженный файл в БД
        :param config: Конфигурационный файл
        :return: Сохранённый экземпляр модели SaveConfigFiles
        """

        if isinstance(config, (InMemoryUploadedFile, str)):
            f = DatabaseAPI.save_config(
                file=config,
                controller_type=self.type_controller,
                source='uploaded',
                description='загружен для формирования конфига с расчётами конфликтов и фаз'
            )
            return f

    def _convert_path_to_url_for_download(self):
        """
        Сохраняет в БД файл конфига/txt с расчитанными конфликтами и фазами, а также меняет в
        self.instance_data path к файлу на url для скачивания
        :return:
        """

        txt = self.instance_data.get(calculate_conflicts.DataFields.txt_file.value)
        config = self.instance_data.get(calculate_conflicts.DataFields.config_file.value)

        if txt is not None:
            path = txt.pop('path_to_file')
            f_txt = DatabaseAPI.save_txt_conflicts(path_to_file=path)
            self.instance_data[calculate_conflicts.DataFields.txt_file.value]['url_to_file'] = f_txt.file.url
        if config is not None:
            path = config.pop('path_to_file')
            f_config = DatabaseAPI.save_config(
                file=path,
                controller_type=self.instance_data[calculate_conflicts.DataFields.type_controller.value],
                source='created',
                description='создан с рассчитанными конфликтами и фазами'
            )
            self.instance_data[calculate_conflicts.DataFields.config_file.value]['url_to_file'] = f_config.file.url

    def validate_user_data(self):
        pass

    def calculate(self):
        """
        Алгоритм получения расчётов конфликтов и фаз, а также формирования txt-файла и/или конфигуационного
        фала контроллера Peek или Swarco.
        :return:
        """

        a_class = self._get_api_class(self.type_controller)
        path_to_original_config = None
        if isinstance(self.uploaded_file_obj, SaveConfigFiles):
            path_to_original_config = str(self.uploaded_file_obj.file.path)

        if a_class is CommonConflictsAndStagesAPI:
            obj = a_class(
                self.stages_groups, create_txt=self.create_txt, path_to_save_txt=self._get_path_to_save_txt_file()
            )
        elif a_class in {SwarcoConflictsAndStagesAPI, PeekConflictsAndStagesAPI}:
            obj = a_class(
                self.stages_groups, create_txt=self.create_txt, path_to_save_txt=self._get_path_to_save_txt_file(),
                path_to_src_config=path_to_original_config
            )
        # elif issubclass(calculate_conflicts.SwarcoConflictsAndStagesAPI, a_class):
        #     obj = a_class(
        #         self.stages_groups, create_txt=self.create_txt, path_to_save_txt=self._get_path_to_save_txt_file(),
        #         path_to_src_config=path_to_original_config
        #     )
        # elif issubclass(calculate_conflicts.PeekConflictsAndStagesAPI, a_class):
        #     obj = a_class(
        #         self.stages_groups, create_txt=self.create_txt, path_to_save_txt=self._get_path_to_save_txt_file(),
        #         path_to_src_config=path_to_original_config
        #     )
        else:
            self.errors.append('Данные для расчёта не валидны')
            return
        obj.build_data()
        self.instance_data = obj.instance_data
        self._convert_path_to_url_for_download()

@dataclass
class PeekProcess(peek_processes.Intersection):
    errors: list = field(default_factory=list)

    def get_repaired_cmd_sg(self) -> None:
        self.validate_data()
        if not self.errors:
            self.repair_cmd_sg_all_stages()
            self.repaired_xp_data['pretty_string'] = self.get_pretty_output()

    def validate_data(self) -> None:
        try:
            for xp, xp_data in self.source_xp_data.items():
                if not xp.isdigit():
                    self.errors.append(f'Номер процесса должен быть представлен числом: {xp}')
                if len(xp_data) != 2:
                    self.errors.append(f'Данные о процессе должны состоять из списка двух элементов')
                if not all(el.isdigit() for el in xp_data[0].split(',')):
                    self.errors.append(f'Номера фаз, принадлежащих процессу должны быть представлены числом. '
                                       f'Процесс: {xp}, Фазы: {xp_data[0]}')
        except ValueError:
            self.errors.append('Некорректный формат предоставленных данных')


