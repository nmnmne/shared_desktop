import asyncio
import threading
import time
import ipaddress

from pysnmp.hlapi.asyncio import *

from tools.forms import ControllerForm
from tools.models import Central, UtcParameterSet

from django.forms import modelformset_factory
from django.shortcuts import render
from django.http import JsonResponse

# Глобальная переменная для отслеживания текущих запросов
current_requests = {}


async def get_phase(request):
    ip_address = request.GET.get('ip_address')
    protocol = request.GET.get('protocol')
    community_string = "private"
    countdown_str = None

    if protocol == "STCIP":
        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError:
            countdown_str = "Invalid IP Address"
        else:
            command_oid = ObjectIdentity(
                "1.3.6.1.4.1.1618.3.7.2.11.1.0"
            )
            status_oid = ObjectIdentity(
                "1.3.6.1.4.1.1618.3.7.2.11.2.0"
            )
            # Асинхронный вызов SNMP getCmd
            error_indication, error_status, error_index, var_binds = await getCmd(
                SnmpEngine(),
                CommunityData(community_string),
                UdpTransportTarget((ip_address, 161)),
                ContextData(),
                ObjectType(command_oid),
                ObjectType(status_oid),
            )
            
            if error_indication:
                countdown_str = f"Ошибка: {error_indication}"
            else:
                try:
                    # Получаем значение статуса фазы
                    status_value = var_binds[1][1].prettyPrint()
                    if int(status_value) > 0:
                        status_value = str(int(status_value) - 1)
                except (IndexError, ValueError) as e:
                    print(f"Ошибка: {e}")
                    status_value = ""

                countdown_str = f"Фаза: {status_value}"

    if protocol == "UTMC":

        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError:
            countdown_str = "Invalid IP Address"
        else:

            def snmp_get_request(ip, community, oid):
                (
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ) = next(
                    getCmd(
                        SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                        lexicographicMode=True,
                    )
                )

                if error_indication:
                    countdown_str= f"Ошибка: {error_indication}"
                    return countdown_str
                if error_status:
                    countdown_str = f"Ошибка: {error_status.prettyPrint()} на {error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    return countdown_str

                for name, val in var_binds:
                    oid_val = val.prettyPrint()
                    # print("current_phase", oid_val)
                    return oid_val

            async def snmp_get_next_request(ip, community, oid):
                (
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ) = next(
                    nextCmd(
                        SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                        lexicographicMode=True,
                    )
                )

                if error_indication:
                    countdown_str = error_indication
                    return JsonResponse({'countdown': countdown_str})
                if error_status:
                    countdown_str = (
                        f"Ошибка: {error_status.prettyPrint()} на "
                        f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    )
                    return JsonResponse({'countdown': countdown_str})

                for name, val in var_binds:
                    oid_str = name.prettyPrint()
                    scn = oid_str[-16:]
                    if scn[2] != ".":
                        scn = oid_str[-19:]
                        if scn[2] == ".":
                            ...
                        else:
                            scn = oid_str[-22:]
                            if scn[2] != ".":
                                print("SCN error:", scn)
                                return 0

                    # print("SCN:", scn)
                    return scn

        community_string = "UTMC"
        oid_get_request = ".1.3.6.1.4.1.13267.3.2.4.2.1.15"
        old_str = await snmp_get_next_request(
            ip_address, community_string, oid_get_request
        )
        # print("old_str", old_str)

        if old_str is not None:
            oid_get_phase = f".1.3.6.1.4.1.13267.3.2.5.1.1.3{old_str}"
            current_phase = await snmp_get_request(
                ip_address, community_string, oid_get_phase
            )

            status_dict = {
                "0x00000000": "Пром",
                "0x01000000": 1,
                "0x02000000": 2,
                "0x04000000": 3,
                "0x08000000": 4,
                "0x10000000": 5,
                "0x20000000": 6,
                "0x40000000": 7,
                "0x80000000": 8,
                "0x00010000": 9,
                "0x00020000": 10,
                "0x00040000": 11,
                "0x00080000": 12,
                "0x00100000": 13,
                "0x00200000": 14,
                "0x00400000": 15,
                "0x00800000": 16,
                "0x00000100": 17,
                "0x00000200": 18,
                "0x00000400": 19,
                "0x00000800": 20,
                "0x00001000": 21,
                "0x00002000": 22,
                "0x00004000": 23,
                "0x00008000": 24,
                "0x00000001": 25,
                "0x00000002": 26,
                "0x00000004": 27,
                "0x00000008": 28,
                "0x00000010": 29,
                "0x00000020": 30,
                "0x00000040": 31,
                "0x00000080": 32,
                "0x00": "Пром",
                "0x01": 1,
                "0x02": 2,
                "0x04": 3,
                "0x08": 4,
                "0x10": 5,
                "0x20": 6,
                "0x40": 7,
                "0x80": 8,
                "0x0100": 9,
                "0x0200": 10,
                "0x0400": 11,
                "0x0800": 12,
                "0x1000": 13,
                "0x2000": 14,
                "0x4000": 15,
                "0x8000": 16,
            }
            status_value = status_dict.get(current_phase, "")
            if status_value:
                countdown_str = f"Фаза: {status_value}"

    if protocol == "UG405":

        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError:
            error_message = "Invalid IP Address"
            return error_message
        else:

            async def snmp_get_request(ip, community, oid):
                (
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ) = await getCmd(
                        SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                        lexicographicMode=True,
                    )


                if error_indication:
                    countdown_str = (f"Ошибка: {error_indication}")
                    return JsonResponse({'countdown': countdown_str})
                if error_status:
                    countdown_str = (
                        f"Ошибка: {error_status.prettyPrint()} на "
                        f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    )
                    return JsonResponse({'countdown': countdown_str})

                for name, val in var_binds:
                    oid_val = val.prettyPrint()
                    # print("current_phase", oid_val)
                    return oid_val

            async def snmp_get_next_request(ip, community, oid):
                (
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ) = await nextCmd(
                        SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                        lexicographicMode=True,
                    )

                if error_indication:
                    print(f"Ошибка: {error_indication}")
                    return None
                if error_status:
                    print(
                        f"Ошибка: {error_status.prettyPrint()} на "
                        f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    )
                    return None


                co = var_binds[0][0][1].prettyPrint()
                len_scn = str(len(co)) + "."
                scn = [str(ord(c)) for c in co]
                scn = ".".join(scn)
                scn = len_scn + scn
                scn = f".1.{scn}"
                # print("SCN: ", co, ", oid: ", scn)
                return scn

        community_string = "UTMC"
        oid_get_request = ".1.3.6.1.4.1.13267.3.2.4.2.1.15"
        old_str = await snmp_get_next_request(
            ip_address, community_string, oid_get_request
        )

        # print("old_str", old_str)
        if old_str is not None:
            oid_get_phase = f".1.3.6.1.4.1.13267.3.2.5.1.1.3{old_str}"
            current_phase = await snmp_get_request(
                ip_address, community_string, oid_get_phase
            )

            phase_mapping = {
                "0x01": 1,
                "0x02": 2,
                "0x04": 3,
                "0x08": 4,
                "0x10": 5,
                " ": 6,
                "@": 7,
                "0x80": 8,
                "0x0100": 9,
                "0x0200": 10,
                "0x0400": 11,
                "0x0800": 12,
                "0x1000": 13,
                "0x2000": 14,
                "0x4000": 15,
                "0x8000": 16,
                "0x010000": 17,
                "0x020000": 18,
                "0x040000": 19,
                "0x080000": 20,
                "0x100000": 21,
                "0x200000": 22,
                "0x400000": 23,
                "0x800000": 24,
                "0x01000000": 25,
                "0x02000000": 26,
                "0x04000000": 27,
                "0x08000000": 28,
                "0x10000000": 29,
                "0x20000000": 30,
                "0x40000000": 31,
                "0x80000000": 32,
                "0x0100000000": 33,
                "0x0200000000": 34,
                "0x0400000000": 35,
                "0x0800000000": 36,
                "0x1000000000": 37,
                "0x2000000000": 38,
                "0x4000000000": 39,
                "0x8000000000": 40,
                "0x010000000000": 41,
                "0x020000000000": 42,
                "0x040000000000": 43,
                "0x080000000000": 44,
                "0x100000000000": 45,
                "0x200000000000": 46,
                "0x400000000000": 47,
                "0x800000000000": 48,
                "0x01000000000000": 49,
                "0x02000000000000": 50,
                "0x04000000000000": 51,
                "0x08000000000000": 52,
                "0x10000000000000": 53,
                "0x20000000000000": 54,
                "0x40000000000000": 55,
                "0x80000000000000": 56,
                "0x0100000000000000": 57,
                "0x0200000000000000": 58,
                "0x0400000000000000": 59,
                "0x0800000000000000": 60,
                "0x1000000000000000": 61,
                "0x2000000000000000": 62,
                "0x4000000000000000": 63,
                "0x8000000000000000": 64,
            }

            status_value = ""
            if 1 <= phase_mapping.get(current_phase, -1) <= 64:
                status_value = phase_mapping.get(current_phase, 1)
            if status_value:
                countdown_str = f"Фаза: {status_value}"

    return JsonResponse({'countdown': countdown_str})


async def stcip(ip_address, phase_value, timeout):
    """Несколько раз повторяю команду STCIP"""
    global current_requests

    # Проверка и обновление current_requests для конкретного IP
    if ip_address in current_requests:
        if current_requests[ip_address] != phase_value:
            current_requests[ip_address] = phase_value
        # Если `phase_value` тот же самый, просто продолжаем выполнение
    else:
        current_requests[ip_address] = phase_value

    if phase_value == 0:
        timeout = 3

    try:
        ipaddress.IPv4Address(ip_address)
    except ipaddress.AddressValueError:
        error_message = "Invalid IP Address"
    else:
        for _ in range(timeout):
            print('timeout ', timeout)
            print(f"Таймер: {_} для IP {ip_address} фаза {phase_value-1}")

            # Прерываем цикл, если phase_value изменился
            if current_requests[ip_address] != phase_value:
                print(f"/////// Отправляем новую фазу на {ip_address} и прерываем отправку предыдущей")
                break

            oid = ObjectIdentity("1.3.6.1.4.1.1618.3.7.2.11.1.0")
            # error_indication, error_status, error_index, var_binds =  await setCmd(
            #     SnmpEngine(),
            #     CommunityData("private", mpModel=0),
            #     UdpTransportTarget((ip_address, 161)),
            #     ContextData(),
            #     ObjectType(oid, Unsigned32(phase_value)),
            # )
            # await asyncio.sleep(1)
            print('dfdfd')

    if current_requests[ip_address] == phase_value and phase_value != 0:
        asyncio.ensure_future(stcip(ip_address, 0, 3))

    # if error_indication:
    #     error_message = f"Ошибка: {error_indication}"
    # else:
    #     error_message = None

    return error_message


async def snmp_set_request_out(ip, timeout, community, oid, data_type_set, msg, stage_set, protocol):
    """Несколько раз повторяю команду UG405"""
    new_request = (ip, stage_set)

    if ip in current_requests:
        if current_requests[ip] != stage_set:
            current_requests[ip] = stage_set
    else:
        current_requests[ip] = stage_set

    if stage_set == "00000000":
        timeout = 3

    for _ in range(timeout):
        if oid.startswith(".1.3.6.1.4.1.13267.3.2.4.2.1.4"):
            print(f"Таймаут: {_} для IP {ip}")

        # Прерываем цикл, если stage_set изменился
        if current_requests[ip] != stage_set:
            print(f"/////// Прерываем текущий запрос для IP {ip} и начинаем новый")
            print(current_requests, new_request)
            break

        error_indication, error_status, error_index, var_binds = await setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid), data_type_set),
        )

        if error_indication:
            print(f"Ошибка: {error_indication}")
        elif error_status:
            print(
                f"Ошибка: {error_status.prettyPrint()} на "
                f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
            )
        else:
            print(msg)

        # Ожидание перед следующей попыткой
        await asyncio.sleep(1)

    if protocol == "UTMC":
        if (
            current_requests[ip] == stage_set
            and stage_set != "00000000"
            and oid.startswith(".1.3.6.1.4.1.13267.3.2.4.2.1.15")
        ):
            print("Таймаут вышел для ", ip)
            asyncio.create_task(
                snmp_set_request_out(
                    ip,
                    3,
                    community,
                    oid,
                    Integer(0),
                    msg,
                    "00000000",
                    protocol,
                )
            )
    elif protocol == "UG405":
        if (
            current_requests[ip] == stage_set
            and stage_set != 0
            and oid.startswith(".1.3.6.1.4.1.13267.3.2.4.1.0")
        ):
            print("Таймаут вышел для ", ip)
            asyncio.create_task(
                snmp_set_request_out(
                    ip,
                    3,
                    community,
                    oid,
                    Integer(1),
                    msg,
                    0,
                    protocol,
                )
            )


async def snmp_set_request_one(ip, community, oid, data_type_set, msg):
    """Асинхронная отправка SNMP-запроса"""
    error_indication, error_status, error_index, var_binds = await setCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid), data_type_set),
    )

    if error_indication:
        print(f"Ошибка: {error_indication}")
    elif error_status:
        print(
            f"Ошибка: {error_status.prettyPrint()} на "
            f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
        )
    else:
        print(msg)


async def set_phase(request):
    ip_address = request.GET.get('ip_address')
    protocol = request.GET.get('protocol')
    phase_value = int(request.GET.get('phase_value', 0))  
    timeout = int(request.GET.get('timeout', 0)) 
    print(f'IP Address: {ip_address}')
    print(f'Protocol: {protocol}')
    print(f'Phase Value: {phase_value}')
    print(f'Timeout: {timeout}')
        
    community_string = "private"



    if protocol == "UG405":
        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError:
            return JsonResponse({'error': 'Invalid IP Address'})
        
        async def snmp_get_request(ip, community, oid):
            (
                error_indication,
                error_status,
                error_index,
                var_binds,
            ) = await getCmd(
                    SnmpEngine(),
                    CommunityData(community),
                    UdpTransportTarget((ip, 161)),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=True,
                )
            if error_indication:
                print(f"Ошибка: {error_indication}")
                return None

            if error_status:
                print(
                    f"Ошибка: {error_status.prettyPrint()} на {error_index and var_binds[int(error_index) - 1][0] or '?'}"
                )
                return None

            for name, val in var_binds:
                oid_val = val.prettyPrint()
                return oid_val

        async def snmp_get_next_request(ip, community, oid):
            (
                error_indication,
                error_status,
                error_index,
                var_binds,
            ) = await nextCmd(
                    SnmpEngine(),
                    CommunityData(community),
                    UdpTransportTarget((ip, 161)),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=True,
                )

            if error_indication:
                print(f"Ошибка: {error_indication}")
                return None

            if error_status:
                print(
                    f"Ошибка: {error_status.prettyPrint()} на {error_index and var_binds[int(error_index) - 1][0] or '?'}"
                )
                return None

            co = var_binds[0][0][1].prettyPrint()
            len_scn = str(len(co)) + "."
            scn = [str(ord(c)) for c in co]
            scn = ".".join(scn)
            scn = len_scn + scn
            scn = f".1.{scn}"
            # print("SCN: ", co, ", oid: ", scn)
            return scn

        community_string = "UTMC"
        oid_get_request = ".1.3.6.1.4.1.13267.3.2.4.2.1.15"
        oid_operation_mode = ".1.3.6.1.4.1.13267.3.2.4.1.0"

        old_str = await snmp_get_next_request(
            ip_address,
            community_string,
            oid_get_request,
        )
        operation_mode = await snmp_get_request(
            ip_address,
            community_string,
            oid_operation_mode,
        )
        print(
            "Operation mode: ",
            operation_mode,
        )

        try:
            if int(operation_mode) != 3:
                oid_to_set_request = ".1.3.6.1.4.1.13267.3.2.4.1.0"
                value_set = 2
                data_type_set = Integer(value_set)
                msg = "Monitor"
                
                # Асинхронный вызов
                await snmp_set_request_one(
                    ip_address,
                    community_string,
                    oid_to_set_request,
                    data_type_set,
                    msg
                )
        except Exception as e:
            print(f"Ошибка: {e}")

        if old_str is not None:

            phase_mapping = {
                0: 0,
                1: 0,
                2: OctetString(hexValue="01"),
                3: OctetString(hexValue="02"),
                4: OctetString(hexValue="04"),
                5: OctetString(hexValue="08"),
                6: OctetString(hexValue="10"),
                7: OctetString(hexValue="20"),
                8: OctetString(hexValue="0040"),
                9: OctetString(hexValue="0080"),
                10: OctetString(hexValue="0100"),
                11: OctetString(hexValue="0200"),
                12: OctetString(hexValue="0400"),
                13: OctetString(hexValue="0800"),
                14: OctetString(hexValue="1000"),
                15: OctetString(hexValue="2000"),
                16: OctetString(hexValue="4000"),
                17: OctetString(hexValue="8000"),
                18: OctetString(hexValue="010000"),
                19: OctetString(hexValue="020000"),
                20: OctetString(hexValue="040000"),
                21: OctetString(hexValue="080000"),
                22: OctetString(hexValue="100000"),
                23: OctetString(hexValue="200000"),
                24: OctetString(hexValue="400000"),
                25: OctetString(hexValue="800000"),
                26: OctetString(hexValue="01000000"),
                27: OctetString(hexValue="02000000"),
                28: OctetString(hexValue="04000000"),
                29: OctetString(hexValue="08000000"),
                30: OctetString(hexValue="10000000"),
                31: OctetString(hexValue="20000000"),
                32: OctetString(hexValue="40000000"),
                33: OctetString(hexValue="80000000"),
                34: OctetString(hexValue="0100000000"),
                35: OctetString(hexValue="0200000000"),
                36: OctetString(hexValue="0400000000"),
                37: OctetString(hexValue="0800000000"),
                38: OctetString(hexValue="1000000000"),
                39: OctetString(hexValue="2000000000"),
                40: OctetString(hexValue="4000000000"),
                41: OctetString(hexValue="8000000000"),
                42: OctetString(hexValue="010000000000"),
                43: OctetString(hexValue="020000000000"),
                44: OctetString(hexValue="040000000000"),
                45: OctetString(hexValue="080000000000"),
                46: OctetString(hexValue="100000000000"),
                47: OctetString(hexValue="200000000000"),
                48: OctetString(hexValue="400000000000"),
                49: OctetString(hexValue="800000000000"),
                50: OctetString(hexValue="01000000000000"),
                51: OctetString(hexValue="02000000000000"),
                52: OctetString(hexValue="04000000000000"),
                53: OctetString(hexValue="08000000000000"),
                54: OctetString(hexValue="10000000000000"),
                55: OctetString(hexValue="20000000000000"),
                56: OctetString(hexValue="40000000000000"),
                57: OctetString(hexValue="80000000000000"),
                58: OctetString(hexValue="0100000000000000"),
                59: OctetString(hexValue="0200000000000000"),
                60: OctetString(hexValue="0400000000000000"),
                61: OctetString(hexValue="0800000000000000"),
                62: OctetString(hexValue="1000000000000000"),
                63: OctetString(hexValue="2000000000000000"),
                64: OctetString(hexValue="4000000000000000"),
                65: OctetString(hexValue="8000000000000000"),
            }

            stage_set = phase_mapping.get(phase_value, 0)

            oid_to_set_request = ".1.3.6.1.4.1.13267.3.2.4.1.0"
            value_set = 3
            data_type_set = Integer(value_set)
            msg = "UTC"
            asyncio.ensure_future(snmp_set_request_out(
                ip_address,
                timeout,
                community_string,
                oid_to_set_request,
                data_type_set,
                msg,
                stage_set,
                protocol,
            ))

            oid_to_set_request = (
                f".1.3.6.1.4.1.13267.3.2.4.2.1.15{old_str}"
            )
            value_set = 1

            if phase_value == 0:
                stage_set = 0

            data_type_set = Integer(value_set)
            msg = f"TO: {oid_to_set_request}"
            asyncio.ensure_future(snmp_set_request_out(
                    ip_address,
                    timeout,
                    community_string,
                    oid_to_set_request,
                    data_type_set,
                    msg,
                    stage_set,
                    protocol,
                ))

            if stage_set == 0:

                oid_to_set_request = ".1.3.6.1.4.1.13267.3.2.4.1.0"
                value_set = 1
                data_type_set = Integer(value_set)
                msg = "Standalone"
                await snmp_set_request_out(
                        ip_address,
                        timeout,
                        community_string,
                        oid_to_set_request,
                        data_type_set,
                        msg,
                        stage_set,
                        protocol,
                    )
            else:

                oid_fn_set_request = (
                    f".1.3.6.1.4.1.13267.3.2.4.2.1.4{old_str}"
                )
                data_type_set = stage_set
                msg = f"Fn: {oid_fn_set_request}"
                asyncio.ensure_future(snmp_set_request_out(
                        ip_address,
                        timeout,
                        community_string,
                        oid_fn_set_request,
                        data_type_set,
                        msg,
                        stage_set,
                        protocol,
                    ))

                oid_dn_set_request = (
                    f".1.3.6.1.4.1.13267.3.2.4.2.1.5{old_str}"
                )
                msg = f"Dn: {oid_dn_set_request}"
                await snmp_set_request_out(
                        ip_address,
                        timeout,
                        community_string,
                        oid_dn_set_request,
                        data_type_set,
                        msg,
                        stage_set,
                        protocol,
                    )


    if protocol == "STCIP":
        print(
            "Команда STCIP",
            ip_address,
            phase_value,
            protocol,
        )
        asyncio.ensure_future(stcip(ip_address, phase_value, timeout))

    # if protocol == "UTMC":

    #     phase = phase_value - 1
    #     # print("Включить UTMC", ip_address, phase, protocol)
    #     audit_logger.info(
    #         f"{request.user.username} / {ip_address}, phase: {phase}, {protocol}"
    #     )
    #     try:
    #         ipaddress.IPv4Address(ip_address)
    #     except ipaddress.AddressValueError:
    #         error_message = "Invalid IP Address"
    #     else:

    #         def snmp_get_request(ip, community, oid):
    #             (
    #                 error_indication,
    #                 error_status,
    #                 error_index,
    #                 var_binds,
    #             ) = next(
    #                 getCmd(
    #                     SnmpEngine(),
    #                     CommunityData(community),
    #                     UdpTransportTarget((ip, 161)),
    #                     ContextData(),
    #                     ObjectType(ObjectIdentity(oid)),
    #                     lexicographicMode=True,
    #                 )
    #             )

    #             if error_indication:
    #                 print(f"Ошибка: {error_indication}")
    #                 return None

    #             if error_status:
    #                 print(
    #                     f"Ошибка: {error_status.prettyPrint()} на {error_index and var_binds[int(error_index) - 1][0] or '?'}"
    #                 )
    #                 return None

    #             for name, val in var_binds:
    #                 oid_val = val.prettyPrint()
    #                 return oid_val

    #         def snmp_get_next_request(ip, community, oid):
    #             (
    #                 error_indication,
    #                 error_status,
    #                 error_index,
    #                 var_binds,
    #             ) = next(
    #                 nextCmd(
    #                     SnmpEngine(),
    #                     CommunityData(community),
    #                     UdpTransportTarget((ip, 161)),
    #                     ContextData(),
    #                     ObjectType(ObjectIdentity(oid)),
    #                     lexicographicMode=True,
    #                 )
    #             )

    #             if error_indication:
    #                 print(f"Ошибка: {error_indication}")
    #                 return None
    #             if error_status:
    #                 print(
    #                     f"Ошибка: {error_status.prettyPrint()} на "
    #                     f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
    #                 )
    #                 return None

    #             for name, val in var_binds:
    #                 oid_str = name.prettyPrint()
    #                 scn = oid_str[-16:]
    #                 if scn[2] != ".":
    #                     scn = oid_str[-19:]
    #                     if scn[2] == ".":
    #                         ...
    #                     else:
    #                         scn = oid_str[-22:]
    #                         if scn[2] != ".":
    #                             print("SCN error:", scn)
    #                             return 0

    #                 return scn

    #         community_string = "UTMC"
    #         oid_get_request = ".1.3.6.1.4.1.13267.3.2.4.2.1.15"
    #         oid_operation_mode = ".1.3.6.1.4.1.13267.3.2.4.1.0"
    #         old_str = await snmp_get_next_request(
    #             ip_address,
    #             community_string,
    #             oid_get_request,
    #         )
    #         operation_mode = await snmp_get_request(
    #             ip_address,
    #             community_string,
    #             oid_operation_mode,
    #         )

    #         # print(
    #         #     "Operation mode: ",
    #         #     operation_mode,
    #         # )

    #         try:
    #             if int(operation_mode) != 3:
    #                 oid_to_set_request = ".1.3.6.1.4.1.13267.3.2.4.1.0"
    #                 value_set = 2
    #                 data_type_set = Integer(value_set)
    #                 msg = "Monitor"
    #                 threading.Thread(
    #                     target=snmp_set_request_one,
    #                     args=(
    #                         ip_address,
    #                         community_string,
    #                         oid_to_set_request,
    #                         data_type_set,
    #                         msg,
    #                     ),
    #                 ).start()

    #         except Exception as e:
    #             print(f"Произошло исключение: {type(e).__name__}: {e}")

    #         if old_str is not None:

    #             stage_dict = {
    #                 1: "00000000",
    #                 2: "01000000",
    #                 3: "02000000",
    #                 4: "04000000",
    #                 5: "08000000",
    #                 6: "10000000",
    #                 7: "20000000",
    #                 8: "40000000",
    #                 9: "80000000",
    #                 10: "00010000",
    #                 11: "00020000",
    #                 12: "00040000",
    #                 13: "00080000",
    #                 14: "00100000",
    #                 15: "00200000",
    #                 16: "00400000",
    #                 17: "00800000",
    #                 18: "00000100",
    #                 19: "00000200",
    #                 20: "00000400",
    #                 21: "00000800",
    #                 22: "00001000",
    #                 23: "00002000",
    #                 24: "00004000",
    #                 25: "00008000",
    #                 26: "00000001",
    #                 27: "00000002",
    #                 28: "00000004",
    #                 29: "00000008",
    #                 30: "00000010",
    #                 31: "00000020",
    #                 32: "00000040",
    #                 33: "00000080",
    #             }
    #             if 1 <= phase_value <= 33:
    #                 stage_set = stage_dict.get(phase_value, "00000000")
    #             else:
    #                 stage_set = "00000000"

    #             oid_to_set_request = ".1.3.6.1.4.1.13267.3.2.4.1.0"
    #             value_set = 3
    #             data_type_set = Integer(value_set)
    #             msg = f"{ip_address} UTC"
    #             threading.Thread(
    #                 target=snmp_set_request_out,
    #                 args=(
    #                     ip_address,
    #                     timeout,
    #                     community_string,
    #                     oid_to_set_request,
    #                     data_type_set,
    #                     msg,
    #                     stage_set,
    #                     protocol,
    #                 ),
    #             ).start()

    #             oid_to_set_request = (
    #                 f".1.3.6.1.4.1.13267.3.2.4.2.1.15{old_str}"
    #             )
    #             value_set = 1
    #             if phase_value == 0:
    #                 value_set = 0
    #             data_type_set = Integer(value_set)
    #             msg = f"{ip_address} TO: {oid_to_set_request}"
    #             threading.Thread(
    #                 target=snmp_set_request_out,
    #                 args=(
    #                     ip_address,
    #                     timeout,
    #                     community_string,
    #                     oid_to_set_request,
    #                     data_type_set,
    #                     msg,
    #                     stage_set,
    #                     protocol,
    #                 ),
    #             ).start()

    #             oid_fn_set_request = (
    #                 f".1.3.6.1.4.1.13267.3.2.4.2.1.4{old_str}"
    #             )
    #             print("phase: ", phase, "stage: ", stage_set, "timeout: ", timeout)
    #             data_type_set = OctetString(hexValue=stage_set)
    #             msg = f"{ip_address} Fn: {oid_fn_set_request}"
    #             threading.Thread(
    #                 target=snmp_set_request_out,
    #                 args=(
    #                     ip_address,
    #                     timeout,
    #                     community_string,
    #                     oid_fn_set_request,
    #                     data_type_set,
    #                     msg,
    #                     stage_set,
    #                     protocol,
    #                 ),
    #             ).start()

    #             oid_dn_set_request = (
    #                 f".1.3.6.1.4.1.13267.3.2.4.2.1.5{old_str}"
    #             )
    #             msg = f"{ip_address} Dn: {oid_dn_set_request}"
    #             threading.Thread(
    #                 target=snmp_set_request_out,
    #                 args=(
    #                     ip_address,
    #                     timeout,
    #                     community_string,
    #                     oid_dn_set_request,
    #                     data_type_set,
    #                     msg,
    #                     stage_set,
    #                     protocol,
    #                 ),
    #             ).start()

    response_data = {
        'status': 'success',
        'message': 'Фаза успешно обновлена',
    }

    return JsonResponse(response_data)


def send_to_async(form, request, timeout):
    """Оборачивает вызов асинхронной функции в синхронный контекст."""
    print('dfsdf')


def phase_control(request):
    """Управление фазой контроллера."""
    template = "tools/phase_control.html"
    error_message = ""
    num_controllers = int(request.GET.get("num_controllers", 1))
    timeout = int(request.GET.get('timeout', 60))
    controller_form_set = modelformset_factory(
        Central, form=ControllerForm, extra=num_controllers
    )
    parameter_sets = UtcParameterSet.objects.all()
    selected_set = None

    # Обработка GET-запроса
    if request.method == 'GET':
        ...

    # Обработка нажатия кнопки загрузки
    elif 'upload_button' in request.GET:
        selected_set_name = request.GET['parameter_set']
        selected_set = UtcParameterSet.objects.get(name=selected_set_name)
        num_controllers = selected_set.num_controllers
        timeout = selected_set.timeout

    # Обработка POST-запроса
    if request.method == "POST":
        formset = controller_form_set(
            request.POST, queryset=Central.objects.none()
        )
        if formset.is_valid():
            for form in formset:
                if form.has_changed():
                    # Вызов функции для отправки данных в асинхронную задачу
                    send_to_async(form, request, timeout)

        else:
            error_message = "Ошибка: Неверные данные в форме"

    else:
        formset = controller_form_set(queryset=Central.objects.none())

    return render(
        request, template, {
            "formset": formset,
            "error_message": error_message,
            "num_controllers": num_controllers,
            "timeout": timeout,
            'num_controllers_options': range(1, 9),
            'timeout_options': range(10, 130, 10),
            'parameter_sets': parameter_sets,
            'selected_set': selected_set,
        }
    )
