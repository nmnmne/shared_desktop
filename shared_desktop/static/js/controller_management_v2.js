'use strict';

/*------------------------------------------------------------------------
|                            Старт страницы                              |
------------------------------------------------------------------------*/

$(document).ready(function(){
    $(`#table_1`).show();

    $('.immutable_data_snmp').click(function() {
        let num_host;
        num_host = $(this).attr('id').split('_')[1];
        $(`#datahost_${num_host}`).text('--');
    });

    // $('.receive_data').click(function() {
    //     let num_host;
    //     console.log($(this).attr('id'));
    //     num_host = $(this).attr('id').split('_')[1];
    //     $(`#datahost_${num_host}`).text('--');
    // });

    // sendReqGetData();
    sendReqGetDataAxios();
    get_name_configs();
    show_hide_hosts_snmp();

});





/*------------------------------------------------------------------------
|                           Контент различных тегов                      |
------------------------------------------------------------------------*/



/*------------------------------------------------------------------------
|                                Константы                               |
------------------------------------------------------------------------*/

const CONTROLLERS = ['Swarco', 'Поток (S)', 'Поток (P)', 'Peek']
const SELECT_PROTOCOL = {'Swarco': 0, 'Поток (S)': 1, 'Поток (P)': 2, 'Peek': 3};
const TYPE_COMMAND = [''];
const SEARCH_OPTIONS = ['По номеру СО', 'Названию СО'];
//home
// const TOKEN = '7174fa6f9d0f954a92d2a5852a7fc3bcaace7578';
//work
//const TOKEN = 'a090474ab50a6ec440eef021295d5f0e750afa00';
// shared_desktop
const TOKEN = 'fb682e5942fa8ce5c26ab8cd3e8eaba41c4cd961';
const GET_DATA = 'get_data';
const SET_DATA = 'set_data';
const BASIC_DATA = 'basic_data';
const ROOT_ROUTE_API = '/api/v1/'
const ROUTE_API_MANAGE_CONTROLLER = `${ROOT_ROUTE_API}manage-controller/`;
const ROUTE_API_DOWNLOAD_CONFIG = `${ROOT_ROUTE_API}download-config/`;
const ROUTE_CONTROLLER_MANAGEMENT_CONFIGURATIONS = `${ROOT_ROUTE_API}controller-management-configurations/`;

// const SEARCH_OPTIONS = {'По номеру СО': function (value) {
//                                         return Number.isInteger(+value);
//                                         }
//                        }

const CONVERT_OPTION_NAME = {'По номеру СО': 'number', 'Названию СО': 'description'};
const CONVERT_OPTION_NAME2 = {'number': 'number', 'description': 'description'};




// --------------GET REQUEST SNMP------------------
// Отслеживаем нажатие чекбокса, который отвечает за постоянный запрос данных с дк по snmp у хоста 1

// Создаем функции на изменения чекбокс внутри каждого хоста
// for (let i=1; i < 11; i++) {
//     console.log(`Это i: ${i}`)
//     $(`#getdatahost_${i}`).change(function() {
//         console.log(intervalID)

//         console.log(`num_host = ${i}`)

//         if (chkbx[i-1].checked && !intervalID[i]){
//             let id_getData = setInterval(getData, 4000, i);
//             intervalID[i] = id_getData;

//         console.log('if');

//         }
//         else{
//             clearInterval(intervalID[i])
//             intervalID[i] = false;
//         console.log('else');
//         document.getElementById(`datahost_${i}`).textContent="--";

//         }
//         console.log(intervalID)

//         }

//     )
// }


// Клик на #display_hosts_snmp -> Отображение количества хостов

/*------------------------------------------------------------------------
|                            Обработчики событий                         |
------------------------------------------------------------------------*/

// Обработчик нажатие кнопку "Отобразить"(для хостов)
$("#display_hosts_snmp").click( function() {
    show_hide_hosts_snmp();
    }
)

// Обработчик нажатие на чекбокс "Отметить/снять "Получать данные с ДК" для всех хостов"
$('#get_data_for_all_hosts').click(function(){
    select_deselect_hosts_snmp($(this).is(':checked'));
});

// Обработчик нажатие на чекбокс "Получать данные с дк"
$('.receive_data').click( function () {
    let num_host = $(this).attr('id').split('_')[1];
    if (!$(this).is(':checked')){
        $(`#datahost_${num_host}`).text('----');
    }
});

// Обработчик изменения протокола
$(`select[name=select_protocols]`).change( function () {
    let num_host = $(this).attr('id').split('_')[1];
    let protocol = $(`#protocol_${num_host} option:selected`).text();
    make_commands(num_host, protocol);
});



/*------------------------------------------------------------------------
|                     Функции для обработчиков событий                   |
------------------------------------------------------------------------*/

// Функция отображения количества хостов
function show_hide_hosts_snmp (option='standart') {

    const select_visible_hosts = document.querySelector('#visible_hosts');
    const num_hosts_to_view = select_visible_hosts.value;
    console.log(`num_hosts_to_view -> ${num_hosts_to_view}`);

    if (option === 'load_from_db') {
        for(let i = 1; i <= +$('#visible_hosts option:last').val(); i++) {
            if (i <= num_hosts_to_view) {
                $(`#table_${i}`).show();
            }
            else {
                $(`#table_${i}`).hide();
            }

        }
        return;
    }

    if ($('#get_data_for_all_hosts').is(':checked')) {

        for (let i = 1; i <= +$('#visible_hosts option:last').val(); i++) {

            if(i <= num_hosts_to_view) {
                $(`#table_${i}`).show();
                $(`#getdatahost_${i}`).prop('checked', true);
            }
            else {
                $(`#table_${i}`).hide();
                $(`#getdatahost_${i}`).prop('checked', false);
            }
        }
    }
    else {
        for (let i = 1; i <= +$('#visible_hosts option:last').val(); i++) {

            if(i <= num_hosts_to_view) {
                $(`#table_${i}`).show();
            }
            else {
                $(`#getdatahost_${i}`).prop('checked', false);
                $(`#table_${i}`).hide();

            }
        }
    }
}

// Функция снять/выбрать все хосты
function select_deselect_hosts_snmp (condition) {
    console.log(condition);

    if (!condition) {
        $('.receive_data').prop('checked', false);
        $('.label_datahost').text('----');
    }
    else {
        $('.receive_data').each(function () {
        console.log('scsdc');
        if ($(this).is(":visible")) {
            $(this).prop('checked', true);
        }
        else {
            let num_host = $(this).attr('id').split('_')[1];
            $(this).prop('checked', false);
            $(`#datahost_${num_host}`).text('----');
        }
    });
    }
}

function make_commands(num_host, protocol) {
    const protocols = ['Поток (P)', 'Поток (S)', 'Swarco', 'Peek'];
    let commands_content;
    if (protocol === protocols[0]) {
        commands_content = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP', 'Рестарт программы'];
    }
    else if (protocol === protocols[1]) {
        commands_content = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP', 'КК SNMP', 'Рестарт программы'];
    }
    else if (protocol === protocols[2]) {
        commands_content = ['Фаза SNMP', 'Фаза MAN','ЖМ КНОПКА', 'ОС КНОПКА', 'ЖМ MAN', 'ОС MAN',  'ЖМ SNMP', 'ОС SNMP',  'КК SNMP', 'Терминальная команда', 'Перезагрузка ДК'];
    }
    else if (protocol === protocols[3]) {
       commands_content = ['Фаза SNMP', 'Фаза MAN', 'ОС MAN', 'ЖМ MAN', 'КК CP_RED','Вводы', 'Параметры программы', 'Перезагрузка ДК'];
    }
    else {
        $(`#setCommand_${num_host} option`).remove();
        $(`#setCommand_${num_host}`).append(`<option value="1"> Выберите протокол </option>`);
        return;
    }

    $(`#setCommand_${num_host} option`).remove();

    // $.each(commands_content,  function(tag_val, val) {
    //     $(`#setCommand_${num_host}`).append(`<option value="${++tag_val}">${val}</option>`);
    // });
    $.each(commands_content,  function(tag_val, val) {
        $(`#setCommand_${num_host}`).append(`<option value="${val}">${val}</option>`);
    });

}

/*------------------------------------------------------------------------
|                 Сохранение и загрузка конфигурации в БД                 |
------------------------------------------------------------------------*/

// const csrftoken = getCookie('csrftoken');
// function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = jQuery.trim(cookies[i]);
//             if (cookie.startsWith(name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break; // Выходим, как только найдём нужное cookie
//             }
//         }
//     }
//     return cookieValue;
// }


// Сохранение и загрузка конфигурации в БД
$("#send_data_to_db").click( function() {
    if (!confirm('Хотите добавить текущие настройки хостов в базу данных ?')) {
        return false;
    }
    send_data_to_db_ax();
    }
)

$("#get_data_from_db").click( function() {
    get_data_from_db_ax();
    }
)

// Обработчик нажатия на выпадающий список "загрзить конфигурацию из дб"
// $(`select[name=conf_from_db]`).click( function () {
//     get_name_configs();
// });

// Функция получает все конфигурации из БД
 async function get_name_configs(cur_config=undefined) {
    // let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
    try {
        const response = await axios.get(
            ROUTE_CONTROLLER_MANAGEMENT_CONFIGURATIONS,
            {
                headers: {
                    "Authorization": `Token ${TOKEN}`,
                },
            },
        );

        console.log('response.data');
        console.log(response.data);

        // $(`#configuration_from_db option`).remove();

        // for (const [num_host, write_data] of Object.entries(response.data)) {
        //     $(`#configuration_from_db`).append(`<option value="${num_host}">${write_data}</option>`);
        //   }
        // document.querySelectorAll('p').forEach((elem) => elem.remove());
        const configurations = document.querySelector(`#configuration_from_db`);
        configurations.options.length = 0;
        response.data.forEach(function add_name(item, index, array) {
        let new_option = new Option(item.name, item.name)
             configurations.add(new_option, undefined);
            }
        );
        if (cur_config != undefined) {
            configurations.value = cur_config;
        }

      } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        console.log(error.config);
      }

 }

// Функция получает данные настроек хостов из БД и записывает их в соответствующие теги
async function get_data_from_db_ax() {

    let name = $(`#configuration_from_db option:selected`).text();
    try {
        const response = await axios.get(
            `${ROUTE_CONTROLLER_MANAGEMENT_CONFIGURATIONS}${name}`,
            {
                headers: {
                    "Authorization": `Token ${TOKEN}`,
                },
            },

        );
        // console.log('response.data');

        // get_name_configs();

        let resp_data = response.data;
        const data_hosts = JSON.parse(resp_data.data);
        // console.log('console.log(resp_data)');
        // console.log(resp_data);
        // console.log(resp_data.num_visible_hosts);
        // console.log(resp_data.data);
        // console.log(data_hosts);


        // console.log('visible_hosts.data');
        // console.log(resp_data);
        // console.log(resp_data['num_visible_hosts']);
        // console.log(resp_data['data']);

        write_data_from_db_to_all_hosts(resp_data.num_visible_hosts, data_hosts);
        if (name === resp_data.name) {
            alert(`Конфигурация "${name}" загружена из базы`);
        }
        else {
            alert(`Сбой при загрузке конфигурация "${name}" из БД`);
        }

      } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        console.log(error.config);
      }

 }

 // Функция записывает данные в теги инфу из бд
 function write_data_from_db_to_all_hosts (visible_hosts, datahosts) {
    let splited_data;

    $.each(datahosts, function(cur_host, write_data) {
        splited_data = write_data.split(';');
        // console.log(splited_data);
        $(`#ip_${cur_host}`).val(splited_data[0]);
        $(`#scn_${cur_host}`).val(splited_data[1]);
        $(`#protocol_${cur_host} option:contains(${splited_data[2]})`).prop('selected', true);
        make_commands(cur_host, $(`#protocol_${cur_host} option:selected`).text());
        splited_data[3] === 'true' ? $(`#getdatahost_${cur_host}`).trigger('click') : $(`#getdatahost_${cur_host}`).prop('checked', false);
        $(`#setCommand_${cur_host} option:contains(${splited_data[4]})`).prop('selected', true);
        $(`#setval_${cur_host}`).val(splited_data[5]);
        splited_data[6] === 'true' ? $(`#hold_${cur_host}`).prop('checked', true) : $(`#hold_${cur_host}`).prop('checked', false);

    });
    $(`#visible_hosts option[value=${visible_hosts}]`).prop('selected', true);
    show_hide_hosts_snmp('load_from_db');
 }

// Функция проверяет валидность введённого имени в тектовое поле name_configuration_datahosts
function check_valid_data_send_to_db (val_name) {
    if (val_name.replace(/ /g,'').length < 3) {
        return false;
    }
    return true;
}

// Функция собирает данные всех хостов(для отправки в БД)
function collect_data_from_all_hosts () {
    let num_hosts = +$('#visible_hosts option:last').val();
    let curr_config_data = {name: $(`#name_configuration_datahosts`).val(),
                num_visible_hosts: $(`#visible_hosts option:selected`).text(),
                category: 1,
               };
    let data_all_hosts = {};
    for (let cur_host = 1; cur_host <= num_hosts; cur_host++) {
        data_all_hosts[cur_host] =
                                    `${$('#ip_' + cur_host).val()};` +
                                    `${$(`#scn_${cur_host}`).val()};` +
                                    `${$(`#protocol_${cur_host} option:selected`).text()};` +
                                    `${$(`#getdatahost_${cur_host}`).is(":checked")};` +
                                    `${$(`#setCommand_${cur_host} option:selected`).text()};` +
                                    `${$(`#setval_${cur_host}`).val()};` +
                                    `${$(`#hold_${cur_host}`).is(":checked")};`

                    }
    curr_config_data.data = JSON.stringify(data_all_hosts);
    // console.log('dataaa')
    // console.log(curr_config_data)
    return curr_config_data;

}

// Асинхронный скрипт отправки данных конфигурации в БД
 async function send_data_to_db_ax () {

    const name_configuration = document.querySelector('#name_configuration_datahosts').value;

    if (!check_valid_data_send_to_db(name_configuration)) {
        alert('Название конфигурации должно быть более 3 символов');
        return false;
    }

    let select_vals = document.querySelectorAll('#configuration_from_db option');
    // console.log('select_vals');
    // console.log(select_vals);

    for (let element of select_vals) {
        if (element.text === name_configuration) {
            console.log(`Конфигурация с таким названием "${element.text}" уже есть`);
            return false;
        }
    }

    let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
    try {
        const response = await axios.post(
            ROUTE_CONTROLLER_MANAGEMENT_CONFIGURATIONS,
            collect_data_from_all_hosts(),
            {
            headers: {
                "X-CSRFToken": csrfToken,
                "Authorization": `Token ${TOKEN}`
                }
            }
        );

        const res = response.data;
        console.log('res');
        console.log(res);

        if (res['name'] === name_configuration) {
            alert('Конфигурация успешно сохранена');
            get_name_configs(name_configuration);
        }
        else {
            alert('Сбой при сохранении конфигурации');
        }

        // for (const [num_host, write_data] of Object.entries(res)) {
        //     $(`#datahost_${num_host}`).text(write_data);
        //   }

      } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        console.log(error.config);
      }

 }

 /*------------------------------------------------------------------------
|                         GET CURRENT STATE                               |
--------------------------------------------------------------------------*/


function collect_data_from_hosts (){
    let num_visible_hosts = $(`#visible_hosts`).val();
    let hosts = {};
    let data = {};
    let num_checked_checkbox = $('.receive_data:checked').length;
    let all_hosts = 0;
    if (num_checked_checkbox > 0) {
        for(let num_host = 1; num_host <= num_visible_hosts; num_host++) {
            if ($(`#getdatahost_${num_host}`).is(':checked')){
                hosts[`${$('#ip_' + num_host).val()}`] = {
                    host_id: num_host,
                    type_controller:  `${$(`#protocol_${num_host} option:selected`).text()}`,
                    scn: `${$(`#scn_${num_host}`).val()}`,
                    request_entity: ['get_state']
                }
                ++all_hosts;
            }
        }
        data.hosts = hosts;
        data.num_hosts_in_request = all_hosts;
    }
    console.log(data);
    return data;
    }


async function sendReqGetDataAxios() {

    let num_checked_checkbox = $('.receive_data:checked').length;

    if (num_checked_checkbox > 0) {
        let data = collect_data_from_hosts();
        data.type_request = 'get_state';
        // console.log('if (num_checked_checkbox > 0)');
        try {
            let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
            const response = await axios.post(
                ROUTE_API_MANAGE_CONTROLLER,
                data,
                {
                headers: {
                "X-CSRFToken": csrfToken,
                "Authorization": `Token ${TOKEN}`
                // "content-type": "application/json"
                }
                }
            );
            console.log('response.data');
            console.log(response.data);

            for (const ip_addr in response.data) {
            let cur_host_data = response.data[ip_addr]

            // console.log(cur_host['responce_entity']);
            // console.log(cur_host['responce_entity']['current_stage']);
            // console.log(cur_host.responce_entity.raw_data.current_states.basic.current_stage);

            let display = document.querySelector(`#displayGetData_${cur_host_data['host_id']}`);

            write_data_to_display_get(display, BASIC_DATA, cur_host_data, GET_DATA);

            // $displayDatahost.setSelectionRange($displayDatahost.value.length, $displayDatahost.value.length);
            display.scrollTop = display.scrollHeight;
            }

          } catch (error) {
            if (error.response) { // get response with a status code not in range 2xx
              console.log(error.response.data);
              console.log(error.response.status);
              console.log(error.response.headers);
            } else if (error.request) { // no response
              console.log(error.request);
            } else { // Something wrong in setting up the request
              console.log('Error', error.message);
            }
            console.log(error.config);
          }

          let val_interval = +$('#polling_get_interval').val();
          if(Number.isInteger(val_interval)) {
              val_interval = +val_interval;
              if (val_interval === 0) {
                  setTimeout(sendReqGetDataAxios, 1000);
              }
              else {
                  val_interval = val_interval * 1000;
                  setTimeout(sendReqGetDataAxios, val_interval);
              }
          }

          else {
              setTimeout(sendReqGetDataAxios, 1000);
          }
    }

    else {
        let val_interval = +$('#polling_get_interval').val();
        if(Number.isInteger(val_interval)) {
            val_interval = +val_interval;
            if (val_interval === 0) {
                setTimeout(sendReqGetDataAxios, 1000);
            }
            else {
                val_interval = val_interval * 1000;
                setTimeout(sendReqGetDataAxios, val_interval);
            }
        }
        else {
            setTimeout(sendReqGetDataAxios, 1000);
        }
    }

}

 /*------------------------------------------------------------------------
|                               SET REQUEST                                |
--------------------------------------------------------------------------*/

let set_timers = {};
let set_timerID;
let test_timers = [];

$(".set_request").click(function (){
    console.log(`set_timers = ${set_timers}`);
    console.log('Tetss SET');
    let num_host = $(this).attr('id').split('_')[1];

    console.log(`test_timers начало`);
    console.log(test_timers);

    if (set_timers.hasOwnProperty(num_host)) {
        console.log(`set_timers из if первая строчка = ${set_timers}`);
        console.log(set_timers);
        console.log(test_timers);
        clearInterval(set_timers[num_host]);
        $(`#setTimerVal_${num_host}`).text(0);
        set_timers[num_host] = null;

        set_timerID = setInterval(write_setTimerVal, 1000, num_host);
        test_timers.push(set_timerID);
        set_timers[num_host] = set_timerID;
        console.log(`set_timers из if последняя строчка = ${set_timers}`);
        console.log(set_timers);
        console.log(test_timers);
    }

    else {
        console.log(`set_timers из else первая строчка`);
        console.log(set_timers);
        console.log(test_timers);

        set_timerID = setInterval(write_setTimerVal, 1000, num_host);
        set_timers[num_host] = set_timerID;
        test_timers.push(set_timerID);
        console.log(`set_timers из else послдняя строчка`);
        console.log(set_timers);
        console.log(test_timers);
    }
}
);

$(".hold_request").click(function () {
    let num_host = $(this).attr('id').split('_')[1];
    let tags = [`#ip_${num_host}`, `#scn_${num_host}`, `#protocol_${num_host}`,
                `#setCommand_${num_host}`, `#setval_${num_host}`, `#SetToHost_${num_host}`]


    if (check_valid_data_hold_request(num_host) && $(`#hold_${num_host}`).is(':checked')) {
        tags.forEach((element) => document.querySelector(element).disabled = true);
    }
    else {
        tags.forEach((element) => document.querySelector(element).disabled = false);
    }
}
);

// Функция записывает значение, какое количество секунд назад была отправлена команда set_request,
// а также вызывает функцию повторной отправки set_request(удержание)
async function write_setTimerVal (num_host) {

    let curr_val = +$(`#setTimerVal_${num_host}`).text();
    $(`#setTimerVal_${num_host}`).text(++curr_val);

    let dataIsValid = check_valid_data_hold_request(num_host);
    let checkboxIsChecked = $(`#hold_${num_host}`).is(':checked');


    if (curr_val % 20 === 0 && dataIsValid && checkboxIsChecked) {
        console.log('axios');
        set_request_axios (num_host);
}
}

// Отправка set request по id кнопки отправить
 $('.set_request').click(function() {
    let num_host = $(this).attr('id').split('_')[1];;
    // console.log($(this).attr('id'));
    set_request_axios(num_host);
});

// Функиця проверяет валилность данных для отправки команды
function check_valid_data_hold_request (num_host) {

    // console.log('зашел в function check_valid_data_hold_request');

    let allowed_data_to_hold = {};
    allowed_data_to_hold[CONTROLLERS[0]] = ['Фаза SNMP'];
    allowed_data_to_hold[CONTROLLERS[1]] = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP', 'КК SNMP'];
    allowed_data_to_hold[CONTROLLERS[2]] = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP'];
    allowed_data_to_hold[CONTROLLERS[3]] = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP', 'КК SNMP'];
    allowed_data_to_hold[CONTROLLERS[3]] = ['Фаза SNMP'];

    let controller_type = `${$(`#protocol_${num_host} option:selected`).text()}`;
    let type_command = `${$(`#setCommand_${num_host} option:selected`).text()}`;

    const commands_content = ['Фаза SNMP', 'ОС SNMP', 'ЖМ SNMP', 'КК SNMP'];


    if (!CONTROLLERS.includes(controller_type)){
        console.log('1')
        return false;
    };

    if (type_command === commands_content[0]) {
        // console.log('2')
        return true;
    }
    else if (controller_type === CONTROLLERS[1] && allowed_data_to_hold[CONTROLLERS[1]].includes(type_command)) {
        console.log('3')
        return true;
    }
    else if (controller_type === CONTROLLERS[2] && allowed_data_to_hold[CONTROLLERS[2]].includes(type_command)) {
        console.log('4')
        return true;
    }
    else {
        console.log('5')
        return false;
    }
};

function sendRequstCommon (num_host) {
    $.ajax({

        type: "POST",
        url: `set_snmp_ajax/${num_host}/`,
        data: {values: 'ТЕСТ ПОСТ ЗАПРОСА',
               csrfmiddlewaretoken:$("input[name=csrfmiddlewaretoken]").val(),
        },

        dataType: 'text',
        cache: false,
        success: function (data) {
        console.log(data)
        if (data == 'yes'){
        console.log(data);
            }
        else if (data == 'no'){
                }
            }
        }
    );
 }

// Отправка запроса команды с помощью библиотеки axios
async function set_request_axios(num_host) {

    const display = document.querySelector(`#displaySendCommand_${num_host}`);
    const button = document.querySelector(`#SetToHost_${num_host}`);
    button.setAttribute('disabled', true);

    let ip, type_controller, type_command, set_val, scn;
    let data_request = {};

    ip = `${$('#ip_' + num_host).val()}`;
    type_controller = `${$(`#protocol_${num_host} option:selected`).text()}`;
    type_command = `${$(`#setCommand_${num_host} option:selected`).text()}`;
    set_val = `${$('#setval_' + num_host).val()}`;
    scn = `${$(`#scn_${num_host}`).val()}`;


    data_request[ip] = {'host_id': num_host,
                       'type_controller':  type_controller,
                       'request_entity': {[type_command]: set_val},
                    //    'type_command': type_command,
                    //    'set_val': set_val,
                       'scn': scn
                       }

   // data_request[`${$('#ip_' + num_host).val()}`] = {
    //                                                 host_id: num_host,
    //                                                 type_controller:  `${$(`#protocol_${num_host} option:selected`).text()}`,
    //                                                 type_command: `${$(`#setCommand_${num_host} option:selected`).text()}`,
    //                                                 set_val: `${$('#setval_' + num_host).val()}`,
    //                                                 scn: `${$(`#scn_${num_host}`).val()}`
    // }

    let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
    try {
        display.textContent += '\n\nИдёт отправка команды...'
        const response = await axios.post(ROUTE_API_MANAGE_CONTROLLER,
            {
              hosts: data_request,
              type_request: 'set_command'
            },
            {
              headers: {
              "X-CSRFToken": csrfToken,
            //
              "Authorization": `Token ${TOKEN}`
              }
            }
        );

      const res = response.data;
        // console.log('res[result]');
        // console.log(res['result']);

        console.log('response.data');
        console.log(response.data);
        // write_data_to_display_set(display, BASIC_DATA, res[ip], data_request[ip], num_host);
        write_data_to_display_set(display, BASIC_DATA, res, ip, data_request[ip], num_host);
        display.scrollTop = display.scrollHeight;



    } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        // console.log(error.config);
        display.textContent += '\nКоманда не отправлена, сервер недоступен';

      }

      finally {
        button.removeAttribute('disabled');
      }
}

 /*------------------------------------------------------------------------
|                        Запись полученых данных в дисплей                 |
--------------------------------------------------------------------------*/

// Запись в "дисплей" полученного состояния ДК(get request)

function write_data_to_display_get(display, type, data) {
    // Шапка, общая для всех "дисплеев"
    const dateObj = new Date(+(data.start_time) * 1000);
    const humanDateFormat = dateObj.toLocaleString();
    display.textContent += `\n\nВремя запроса: ${humanDateFormat}`;
    let content = '';
    if (data.request_errors) {
        content = `\nОшибка запроса: ${data.request_errors}`;
        // display.textContent  += `\nОшибка запроса: ${data.request_errors}`;
    }
    // BASIC_DATA -> общие данные о режиме"
    else if (type === BASIC_DATA) {
        // Отображение для контроллера Пик(с учётом количества потоков(xp))
        if (data.type_controller === CONTROLLERS[3]) {
            content = createContentPeekGet_Display(data);
        }
        else if (data.type_controller === CONTROLLERS[0]) {
            content = createContentSwarcoGet_Display(data);
        }
        // Отображение для контроллера для остальных типов дк
        else {
            content = `\nФаза=${data.responce_entity.raw_data.current_states.basic.current_stage} ` +
                      `План=${data.responce_entity.raw_data.current_states.basic.current_plan} ` +
                      `Режим=${data.responce_entity.raw_data.current_states.basic.current_mode}`
        }
    }
    display.textContent += content;
}

function createContentPeekGet_Display(data_resp_json) {
    let content = '';
    if (typeof data_resp_json.responce_entity.raw_data.current_states.basic != 'undefined') {

        const basic = data_resp_json.responce_entity.raw_data.current_states.basic;
        const streams = basic.streams;

            content += `\nПлан=${data_resp_json.responce_entity.raw_data.current_states.basic.current_plan} `;
            for (let i = 1; i <= streams; i++) {
                const curr_stream = basic.stream_info[i.toString()];
                content += `\nПоток ${i}: ${curr_stream.current_state} ` +
                           `Фаза=${curr_stream.current_stage} `+
                           `Режим=${curr_stream.current_mode}`
            }
        };
        console.log(content);
    return content;
}

function createContentSwarcoGet_Display(data_resp_json) {
    let content = '';

    if (typeof data_resp_json.responce_entity.raw_data.current_states.basic.web_content != 'undefined') {
        const web_content_itc = data_resp_json.responce_entity.raw_data.current_states.basic.web_content;
        content += `\n${web_content_itc[1]}` + `\n` + web_content_itc[2] + `\n` +
                    web_content_itc[3] + `\n` + web_content_itc[5];
    }

    console.log(content);
    return content;
}

// Запись в "дисплей" состояния ДК после отправки команды(set request)

function write_data_to_display_set(display, type, data_resp_json, ip, data_request_from_tags, num_host) {

    let content = '';
    const type_command = document.querySelector(`#setCommand_${num_host}`).value;
    const val_command = document.querySelector(`#setval_${num_host}`).value;

    if (typeof data_resp_json.detail === 'string') {
        content += `\nОшибка запроса: ${data_resp_json.detail}`  +
                   `\nКоманда: ${type_command}=${val_command}`;
    return false;
    }

    data_resp_json = data_resp_json[ip];
    const dateObj = new Date(+(data_resp_json.start_time) * 1000);
    const humanDateFormat = dateObj.toLocaleString();
    display.textContent  += `\nВремя запроса: ${humanDateFormat}` +
                            `\nКоманда: ${type_command}=${val_command}`;

    if (typeof data_resp_json.request_errors === 'string') {
        content += `\nОшибка запроса: ${data_resp_json.request_errors}`
    return false;
    }

    if (type === BASIC_DATA) {
        // content += `\nРезультат запроса: ${data_resp_json.responce_entity.result}`;
        content += `\nРезультат запроса: Успешно отправлена`;

        if (data_request_from_tags.type_controller === CONTROLLERS[0]) {
            content += createContentSwarcoSet_Display(data_resp_json);
        }
        else if (data_request_from_tags.type_controller === CONTROLLERS[3]) {
            content += createContentPeekSet_Display(data_resp_json);
        }
        display.textContent  += content;
    }
}

function createContentSwarcoSet_Display(data_resp_json) {
    let content = '';
    if (typeof data_resp_json.responce_entity.raw_data.current_states.inputs != 'undefined') {
        let inps_num, inps_val;
        for (inps_num in data_resp_json.responce_entity.raw_data.current_states.inputs) {
            inps_val = data_resp_json.responce_entity.raw_data.current_states.inputs[inps_num];
        };
            content += `\nРежим: ${data_resp_json.responce_entity.raw_data.current_states.itc.State}` +
                       `\nСостояние входов:\n${inps_num}\n${inps_val}`;
        };
    return content;
}

function createContentPeekSet_Display(data_resp_json) {
    let content = '';
    if (typeof data_resp_json.responce_entity.raw_data.current_states.basic != 'undefined') {
        if (typeof data_resp_json.responce_entity.raw_data.current_states.inputs != 'undefined') {
            content += `\nСостояние входов MPP:\n${data_resp_json.responce_entity.raw_data.current_states.inputs.join('; ')}`;
        }
        else if (typeof data_resp_json.responce_entity.raw_data.current_states.user_parameters != 'undefined') {
            content += `\nСостояние параметров программы:\n${data_resp_json.responce_entity.raw_data.current_states.user_parameters.join('; ')}`;
        }
            // content += `\nРежим: ${data_resp_json.responce_entity.raw_data.current_states.basic.current_mode}` +
            //            `\nСостояние входов:\n${data_resp_json.responce_entity.raw_data.current_states.inputs}`;
        else {
            content += ' ';
        }
        };
    return content;
}

function createContentPotokSet_Display(data_resp_json) {
    let content = '';
}

 /*------------------------------------------------------------------------
|                               SEARCH HOST                                |
--------------------------------------------------------------------------*/

let search_inputs = document.querySelectorAll('.search_host');

search_inputs.forEach((item) => {
    item.addEventListener('input', search_host_get_data);
});

// document.querySelectorAll('.search_host').addEventListener('input', function(event) {
//     let num_host = $(this).attr('id').split('_')[1];
//     search_host_get_data(event.target.value, num_host);
//     console.log('SEARCH HOST');
//     console.log(event.target.value);
//     console.log(num_host);
// });

// async function search_host_get_data(event) {

//     console.log('search_host_get_data');
//     // console.log(event.target.value);
//     // console.log(event.target);
//     // console.log(event.target.id);

    
//     const value = event.target.value;
//     let num_host = event.target.id.split('_');
//     num_host = num_host.at(-1);
//     const val_option = document.querySelector(`#searchoptions_${num_host}`).value;
//     const converted_option_name = CONVERT_OPTION_NAME[val_option];

    
//     if (val_option === SEARCH_OPTIONS[0] && !Number.isInteger(+value)) {
//         return false;
//     }

//     try {
//         const response = await axios.get(            
//             `/api/v1/search-controller/`,
//             {
//                 params: {
//                     [converted_option_name]: value,
//                 },
//             },

//         );
//         console.log('response.data');
//         console.log(response.data);

//         const data = response.data;
//         if (!(typeof data[converted_option_name] === 'undefined')) {
//             const ip_adress = data['ip_adress'];
//             const protocol = data['type_controller'];

//             document.querySelector(`#ip_${num_host}`).value = ip_adress;
//             document.querySelector(`#protocol_${num_host}`).value = protocol;
//             make_commands(num_host, protocol);
//         }

//         // if (Array.isArray(response.data)) {
//         //     const data = response.data.at(-1);
//         //     const ip_adress = data['ip_adress'];
//         //     const protocol = data['type_controller'];

//         //     document.querySelector(`#ip_${num_host}`).value = ip_adress;
//         //     document.querySelector(`#protocol_${num_host}`).value = protocol;
//         //     make_commands(num_host, protocol);

//         // }

//       } catch (error) {
//         if (error.response) { // get response with a status code not in range 2xx
//           console.log(error.response.data);
//           console.log(error.response.status);
//           console.log(error.response.headers);
//         } else if (error.request) { // no response
//           console.log(error.request);
//         } else { // Something wrong in setting up the request
//           console.log('Error', error.message);
//         }
//         console.log(error.config);
//       }
    
//  }

async function search_host_get_data(event) {

    console.log('search_host_get_data');
    // console.log(event.target.value);
    // console.log(event.target);
    // console.log(event.target.id);

    
    const value = event.target.value;
    let num_host = event.target.id.split('_');
    num_host = num_host.at(-1);
    const val_option = document.querySelector(`#searchoptions_${num_host}`).value;
    const converted_option_name = CONVERT_OPTION_NAME[val_option];

    
    if (!(val_option === SEARCH_OPTIONS[0])) {
        return false;
    }

    try {
        const response = await axios.get(            
            `/api/v1/trafficlight-objects/${value}`,
            {
            headers: {
                "Authorization": `Token ${TOKEN}`,
            },
            },

        );
        console.log('response.data');
        console.log(response.data);

        const data = response.data;
        if (!(typeof data[converted_option_name] === 'undefined')) {
            const ip_adress = data['ip_adress'];
            let protocol = data['type_controller'];
            
            console.log(protocol);
            if (protocol == 'Поток S') {
                protocol = 'Поток (S)';
            }
            else if (protocol == 'Поток') {
                protocol = 'Поток (P)';
            }

            console.log(protocol);

            document.querySelector(`#ip_${num_host}`).value = ip_adress;
            document.querySelector(`#protocol_${num_host}`).value = protocol;
            make_commands(num_host, protocol);
        }

        // if (Array.isArray(response.data)) {
        //     const data = response.data.at(-1);
        //     const ip_adress = data['ip_adress'];
        //     const protocol = data['type_controller'];

        //     document.querySelector(`#ip_${num_host}`).value = ip_adress;
        //     document.querySelector(`#protocol_${num_host}`).value = protocol;
        //     make_commands(num_host, protocol);

        // }

      } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        console.log(error.config);
      }
    
 }

/*--------------------------------------------------------------------------
|                            UPDATE TRAFFIC_LIGHTS                          |
--------------------------------------------------------------------------*/
 
async function updateTrafficlights(event) {
    const file = document.querySelector('#file_trafficlihgtdata_update');
    console.log('updateTrafficlights');
    // console.log(file.files[0]);
    const form_data = new FormData();
    if (file.files.length) {
        
        form_data.append('file', file.files[0]);
    }
    else {
        return false;
    }

    const csrfToken = $("input[name=csrfmiddlewaretoken]").val();
    try {
        const responce = await axios.post('/api/v1/update_trafficlihgtdata/', form_data, {
            headers: {
                "X-CSRFToken": csrfToken, 
                "Content-Type": "multipart/form-data",
                "Authorization": `Bearer ${TOKEN}`,
            }
        });
        console.log(responce);
    } catch (error) {
        if (error.response) { // get response with a status code not in range 2xx
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.headers);
        } else if (error.request) { // no response
          console.log(error.request);
        } else { // Something wrong in setting up the request
          console.log('Error', error.message);
        }
        console.log(error.config);
        
      }
      file.value = null;
    }
    
const button_update_trafficlihgtdata = document.querySelector('#update_trafficlihgtdata');
button_update_trafficlihgtdata.addEventListener('click', updateTrafficlights);

