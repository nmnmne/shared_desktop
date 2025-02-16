from time import process_time_ns

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.generic import TemplateView
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
import json
import logging
import time
import asyncio
import openpyxl
from io import BytesIO

from .models import ControllerManagement, TrafficLightsObjects
from . import services as services
from .serializers import BaseTrafficLightsSerializer, ControllerHostsSerializer
from .constants import RequestOptions, AvailableTypesRequest

logger = logging.getLogger(__name__)

TYPES_CONTROLLER = ['Swarco', 'Поток (S)', 'Поток (P)', 'Peek']

"""" API  """


class ControllerManagementHostsConfigurationViewSetAPI(viewsets.ModelViewSet):
    queryset = ControllerManagement.objects.all()
    serializer_class = ControllerHostsSerializer
    lookup_field = 'name'


class SearchByNumberTrafficLightsAPIVeiw(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = TrafficLightsObjects.objects.all()
    serializer_class = BaseTrafficLightsSerializer
    lookup_field = 'number'


class TrafficLightsUpdate(APIView):
    permission_classes = (IsAdminUser, IsAuthenticated)

    def post(self, request):
        start_time = time.time()
        logger.debug(request.FILES)
        file_in_memory = request.FILES['file'].read()
        wb = openpyxl.load_workbook(filename=BytesIO(file_in_memory))
        sh = wb.active

        all_obj = []
        for row_cells in sh.iter_rows():
            # num_co, addr, ip_addr, decsr, type_controller = row_cells
            num_co, type_controller, addr, description, ip_addr = row_cells

            num_co, addr, ip_addr, description, type_controller = num_co.value, addr.value, ip_addr.value, \
                description.value, type_controller.value

            matches_controllers_to_group = {
                'Swarco': 1,
                'Peek': 2,
                'Поток (P)': 3,
                'Поток (S)': 4,
                'Сигнал (STCIP)': 5,
                'Сигнал (SXTP)': 6,
                'ДКС': 7,
                'ДКС (Старт)': 8,
                'ДКСТ': 9,
            }
            group = matches_controllers_to_group.get(type_controller, 0)

            all_obj.append((
                TrafficLightsObjects(number=num_co, adress=addr, description=description,
                                     ip_adress=ip_addr, type_controller=type_controller, group=group)
            ))
        TrafficLightsObjects.objects.all().delete()
        TrafficLightsObjects.objects.bulk_create(all_obj)
        logger.debug('Время обновления: %s' % (time.time() - start_time))
        return Response({'result': 'данные обновлены'})


class ControllerManagementAPI(APIView):
    """
    Управление/получение данных/загрузка конфига с контроллеров
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):

        start_time = time.time()
        data_body = request.data
        logger.debug(data_body)
        data_hosts_body, type_req, req_from_telegramm, chat_id, search_in_db = (
            data_body.get(RequestOptions.hosts.value),
            data_body.get(RequestOptions.type_request.value),
            data_body.get(RequestOptions.request_from_telegramm.value),
            data_body.get(RequestOptions.chat_id.value),
            data_body.get(RequestOptions.search_in_db.value)
        )
        logger.debug(data_hosts_body)
        if (data_hosts_body is None or type_req is None or type_req not in
                AvailableTypesRequest.TYPE_GET.value | AvailableTypesRequest.TYPE_SET.value):
            return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})

        db = services.QuerysetToDB()
        if req_from_telegramm is not None:
            if chat_id is None:
                return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})
            chat_id_is_valid = asyncio.run(db.get_queryset_chat_id_tg(chat_id))
            if chat_id_is_valid is None:
                return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})

        responce_manager = services.ResponceMaker()
        checker = services.Checker()

        data_hosts = responce_manager.create_base_struct(data_hosts_body)
        logger.debug(data_hosts)

        if search_in_db:
            data_hosts = asyncio.run(db.main(data_hosts))
            logger.debug('data_hosts_for_req_after_req_to_db')
            logger.debug(data_hosts)
        else:
            data_hosts = data_hosts_body

        responce_manager.save_json_to_file(data_hosts, 'data_hosts_after_queryset.json')
        logger.debug(data_hosts)
        data_hosts = checker.validate_all_properties_data_hosts(data_hosts, type_req)
        logger.debug(data_hosts)
        if checker.check_error_request_in_all_hosts(data_hosts):
            return Response(data_hosts)
        controller_manager = services.get_controller_manager(type_req)
        if controller_manager is None:
            return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})

        data_hosts = asyncio.run(controller_manager.main(data_hosts))
        if type_req == RequestOptions.type_get_config.value:
            logger.debug(data_hosts)
            data_hosts = controller_manager.create_zip_archive_and_save_to_db_multiple(data_hosts)
            if checker.check_error_request_in_all_hosts(data_hosts):
                return Response(responce_manager.add_end_time_to_data_hosts(data_hosts))
            if req_from_telegramm:
                send_file_tg = services.TelegrammBot()
                data_hosts = asyncio.run(
                    send_file_tg.main(data_hosts, chat_id, send_file=True)
                )
            data_hosts = responce_manager.remove_prop(data_hosts, (services.JsonResponceBody.MODEL_OBJ.value,))
            logger.debug(data_hosts)

        responce_manager.save_json_to_file(data_hosts)
        logger.debug(f'Время выполнения запроса: {time.time() - start_time}')
        return Response(data_hosts)


class GetFileFromControllerAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        start_time = time.time()
        logger.debug(request.data)
        data_body = request.data
        data_hosts_body, type_req, chat_id = (
            request.data.get('hosts'), request.data.get('type_request'), request.data.get('chat_id')
        )
        logger.debug(data_hosts_body)
        if not data_hosts_body or not type_req or not chat_id:
            return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})

        responce_manager = services.ResponceMaker()
        db = services.QuerysetToDB()

        chat_idIsvalid = asyncio.run(db.get_queryset_chat_id_tg(chat_id))
        if chat_idIsvalid is None or chat_idIsvalid.get('chat_id') is None:
            return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})
        logger.debug(chat_idIsvalid)
        logger.debug(chat_idIsvalid['chat_id'])

        needQueryset = request.data.get(services.RequestOptions.search_in_db.value)
        if needQueryset:

            data_hosts_for_req = db.get_parsed_data(data_hosts_body)
            logger.debug('data_hosts_for_req_after_req_to_db')
            logger.debug(data_hosts_for_req)

        else:
            # Тут должна быть проверка, что передан именно IP-адресс и допустимый тип контроллера
            data_hosts_for_req = data_hosts_body

        if services.check_error_request_in_all_hosts(data_hosts_for_req):
            return Response({'detail': services.ErrorMessages.BAD_DATA_FOR_REQ.value})

        manager = services.DownLoadFile()
        res_download = asyncio.run(manager.download_file(data_hosts_for_req))

        logger.debug(res_download)
        data_hosts_for_req = manager.create_zip_archive_and_save_to_db_multiple(
            data_hosts_for_req, res_download
        )

        # logger.debug(data_hosts_for_req)
        if services.check_error_request_in_all_hosts(data_hosts_for_req):
            responce = responce_manager.create_json(
                data_hosts_for_req, start_time
            )
            return Response(responce)

        send_file_tg = services.TelegrammBot()
        res_send_file = asyncio.run(send_file_tg.main(data_hosts_for_req, [
            (ipAddr, data_body.get('chat_id'), data_host.get('path_to_archive'))
            for ipAddr, data_host in data_hosts_for_req.items()
        ], send_file=True
                                                      ))

        logger.debug(res_send_file)
        # for res in res_send_file:
        #     logger.debug(res.result())
        #     ip = res.get_name()
        #     curr_host = data_hosts_for_req.get(ip)
        #     curr_host['responce_tlg'] = res.result()
        #     curr_host['protocol'] = 'ssh/ftp'
        #     curr_host['request_execution_time'] = f'{int(time.time() - start_time)} seconds'
        #     del curr_host['path_to_archive']
        #     curr_host['raw_data_for_responce'] = {
        #         'intersection': curr_host.get('intersection'),
        #         'owner': curr_host.get('owner'),
        #         'controller-id': curr_host.get('controller-id'),
        #         'backplane-id': curr_host.get('backplane-id'),
        #     }
        #     # logger.debug(data_hosts_for_req)
        #     # logger.debug(data_hosts_for_req.get(ip))
        #     # logger.debug(curr_host['raw_data_for_responce'])

        logger.debug(data_hosts_for_req)
        logger.debug(f'Время выполнения запроса: {time.time() - start_time}')
        responce = responce_manager.create_json(data_hosts_for_req, start_time)
        return Response(responce)


class CompareGroupsAPI(APIView):
    """
    Управление/получение данных/загрузка конфига с контроллеров
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):

        start_time = time.time()
        data_body = request.data
        options = data_body.get('options', [])
        logger.debug(data_body)
        manager = services.PassportProcessing(
            data_body.get('content_table_groups'), data_body.get('content_table_stages')
        )
        responce = manager.get_result(options)
        # if option == RequestOptions.compare_groups.value:
        #     table_groups, has_errors, err_in_user_data = manager.compare_groups_in_stages(
        #         data_body.get('content_table_groups'), data_body.get('content_table_stages')
        #     )
        #     responce = services.ResponceMaker.create_responce_compare_groups_in_stages(
        #         table_groups.group_table, has_errors, err_in_user_data
        #     )
        # elif option == RequestOptions.calc_groups_in_stages.value:
        #     table_groups, has_errors, err_in_user_data = manager.create_groups_in_stages_content(
        #         data_body.get('content_table_stages')
        #     )
        #     responce = services.ResponceMaker.create_groups_in_stages_content(
        #         table_groups.group_table, has_errors, err_in_user_data
        #     )

        logger.debug(f'Время выполнения запроса: {time.time() - start_time}')
        return Response(responce)


class PotokTrafficLightsConfiguratorAPI(APIView):
    permission_classes = (IsAuthenticated,)

    get_functions_from_condition_string = 'get_functions_from_condition_string'
    get_condition_result = 'get_condition_result'
    condition = 'condition'

    def post(self, request):
        start_time = time.time()
        data_body = request.data
        condition = data_body.get(self.condition)
        options = data_body.get('options')
        if options is None:
            return Response({'detail': 'Предоставлены некорректные данные для запроса'})
        option_get_functions_from_condition_string = options.get(self.get_functions_from_condition_string)
        option_get_condition_result = options.get(self.get_condition_result)

        print(f'data_body: {data_body}')
        if option_get_functions_from_condition_string:
            get_funcs = services.GetFunctionsPotokTrafficLightsConfigurator(condition)
            get_funcs.get_functions()
            responce = {
                'functions': get_funcs.functions,
                'errors': get_funcs.errors
            }
        elif option_get_condition_result:
            func_values = data_body.get('payload').get('get_condition_result').get('func_values')
            get_result_condition = services.GetResultCondition(condition, func_values)
            get_result_condition.get_condition_result()
            responce = {
                'result': get_result_condition.current_result,
                'errors': get_result_condition.errors
            }
        else:
            responce = {'detail': 'Предоставлены некорректные данные для запроса'}
        print(f'responce: {responce}')
        print(f'Время выполения запроса составило {time.time() - start_time}')
        return Response(responce)


class ConflictsAndStagesAPI(APIView):
    """
    Управление/получение данных/загрузка конфига с контроллеров
    """

    # permission_classes = (IsAuthenticated,)

    def post(self, request):

        start_time = time.time()
        logger.debug(request.FILES)

        try:
            entity_req_data = json.loads(request.data['data'])
            stages = entity_req_data['stages']
            type_controller = entity_req_data['type_controller']
            create_txt = entity_req_data['create_txt']
            create_config = entity_req_data['create_config']
            swarco_vals = entity_req_data['swarco_vals']
            file: InMemoryUploadedFile | None = request.FILES.get('file')

        except KeyError:
            return Response({'detail': 'Предоставлены некорректные данные для запроса'})

        data = services.ConflictsAndStages(raw_stages_groups=stages, type_controller=type_controller, create_txt=create_txt, scr_original_config=file)
        if data.errors:
            return Response({'detail': data.errors})
        data.calculate()

        logger.debug(f'Время выполнения запроса: {time.time() - start_time}')
        return Response(data.instance_data)


class PeekProcesses(APIView):
    """
    Расчёт строки CmdSG EC-X Configurator
    """

    def post(self, request):
        """
        Производит запрос на вычисление CmdSG и возвращает json ответ
        """

        data_body = request.data
        if data_body is not None:
            intersection = services.PeekProcess(data_body)
            intersection.get_repaired_cmd_sg()
            responce = {
                'source_data': intersection.source_xp_data,
                'repaired_cmd_sg': intersection.repaired_xp_data,
                'errors': intersection.errors
            }
        else:
            responce = {'errors': ['the calculation data is not provided']}
        return Response(responce)


"""" TEMPLATE VIEWS  """


class ManageControllers(TemplateView):
    template_name = 'toolkit/manage_controllers.html'
    extra_context = {
        'first_row_settings': {
            'label_settings': 'Настройки ДК', 'ip': 'IP-адресс', 'scn': 'SCN', 'protocol': 'Протокол'
        },
        'second_row_get': {
            'controller_data': 'Информация с ДК', 'label_get_data': 'Получать данные с ДК', 'label_data': 'Данные с ДК'
        },
        'third_row_set': {
            'set_btn': 'Отправить'
        },
        'num_hosts': [i for i in range(1, 31)],
        'title': 'Управление контроллером',
        'types_controllers': TYPES_CONTROLLER
    }


class DownloadConfig(TemplateView):
    template_name = 'tools/download_config.html'


class CompareGroups(TemplateView):
    template_name = 'tools/passport.html'


class PotokTrafficLightsConfigurator(TemplateView):
    template_name = 'tools/tlc_potok.html'


class ConflictsAndStages(TemplateView):

    template_name = 'tools/calc_conflicts.html'
    extra_context = {
        'title': 'Расчёт конфликтов и фаз'
    }

