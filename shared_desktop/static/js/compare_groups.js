'use strict';

/*------------------------------------------------------------------------
|                            Старт страницы                              |
------------------------------------------------------------------------*/

$(document).ready(function(){
  textAreaTableGroup.placeholder = placeholderTableGroups;
  textAreaTableStages.placeholder = placeholderTableStages;
  textAreaResultCalcGroupsInStages.placeholder = placeholderGroupsInStagesResult;
  hideElements([tableResultCompareGroups, btnCalculate, tableCompareGroups, tableResultCalcGroupsInStages]);
});


/*------------------------------------------------------------------------
|                                Константы                               |
------------------------------------------------------------------------*/

// home
// const TOKEN = '7174fa6f9d0f954a92d2a5852a7fc3bcaace7578';
//work
//const TOKEN = 'a090474ab50a6ec440eef021295d5f0e750afa00';
//shared_desktop
const TOKEN = 'fb682e5942fa8ce5c26ab8cd3e8eaba41c4cd961';
const ROOT_ROUTE_API = '/api/v1/'
const ROOT_ROUTE_API_COMPARE_GROUPS = `/api/v1/compare-groups/`;

const placeholderTableGroups = `В данное поле скопируйте из "Таблицы направлений" паспорта содержимое трёх колонок:
"№ нап.", "Тип направления", "Фазы, в кот. участ. направ."
Важно! Необходимо копировать содержимое напрямую из паспорта.
Пример для копирования в данное поле:\n
1	Транспортное	1,2,6
2	Транспортное	1,2,3,6
3	Общ. трансп.	1,2,3,6
4	Транспортное	1,2,3,4,6
5	Поворотное	1,2
6	Пешеходное	1,2,3,6
7	Транспортное	4,5
8	Пешеходное	4,5
9	Пешеходное	4,5
10	Пешеходное	3,6
11	Пешеходное	5
12	Транспортное	Пост. красное`; 
const placeholderTableStages = `В данное поле скопируйте из "Программа x" содержимое двух колонок:
"№ фазы", "Направления"
Важно! Необходимо копировать содержимое напрямую из паспорта.
Пример для копирования в данное поле:\n
1	1,2,3,4,5,6
2	1,2,3,4,5,6
3	2,3,4,6,10
4	4,7,8,9
5	7,8,9,11
6	1,2,3,4,6,10`;
const placeholderGroupsInStagesResult = `В данном поле будет выведен результат расчёта привязки направлений к фазам
для "Таблицы направлений"`;


// Элементы html страницы
const div = document.querySelector('#main_div');
const tableCompareGroups = document.querySelector("#table_compare_groups");
const tableResultCompareGroups = document.querySelector("#table_result_compare_groups");
const tableResultCalcGroupsInStages = document.querySelector('#table_result_calc_groups_in_stages');
const textAreaTableGroup = document.querySelector('#table_groups');
const textAreaTableStages = document.querySelector('#table_stages');
const textAreaResultCalcGroupsInStages = document.querySelector('#textarea_result_calc_groups_in_stages');
const btnCalculate = document.querySelector('#calculate');
const selectChooseOption = document.querySelector('#choose_option');
const optionsSelectChooseOption = {
  nothing: '-',
  compare_groups: 'compare_groups',
  calc_groups_in_stages: 'calc_groups_in_stages'
}

/*------------------------------------------------------------------------
|                               Events                                   |
------------------------------------------------------------------------*/

btnCalculate.addEventListener('click', compare_groups_axios);
selectChooseOption.addEventListener('change', chooseOption);

 /*------------------------------------------------------------------------
|                      Запрос в api и обработка запроса                   |
--------------------------------------------------------------------------*/

// Отправка запроса команды с помощью библиотеки axios
async function compare_groups_axios(event) {

  const content_table_groups = document.querySelector(`#table_groups`).value;
  const content_table_stages = document.querySelector(`#table_stages`).value;
  
  const checkValidOption = optionIsChecked();
  if (!checkValidOption) {
    return false;
  }

  let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
  try {

      const response = await axios.post(ROOT_ROUTE_API_COMPARE_GROUPS,          
          { 
            options: [selectChooseOption.value],
            content_table_groups: content_table_groups,
            content_table_stages: content_table_stages
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
      make_result(selectChooseOption.value, res);

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
      
    }

    finally {
      // button.removeAttribute('disabled');  
    }
}

// Общая функция для обработки responce и формирования контента на странице
function make_result(option, responce) {
  if (option === optionsSelectChooseOption.compare_groups) {
    displayResultCompareGroups(responce);
  }
  else if (option === optionsSelectChooseOption.calc_groups_in_stages) {
    displayResultCalcGroupsInStages(responce);
  }
}

 /*------------------------------------------------------------------------
|            Запись полученых на странице в различные элементы            |
--------------------------------------------------------------------------*/

// Функция формирует и записывает данные на странице для опции "Сравнить напрвления"
function displayResultCompareGroups (responce_data) {
  
  const groups_info = responce_data.compare_groups.groups_info;
  const num_cols = tableCompareGroups.rows[0].cells.length;
  const userDataIsValid = responce_data.compare_groups.error_in_user_data;
  remove_rows(tableResultCompareGroups, tableResultCompareGroups.rows.length, 1);
  
  if (typeof userDataIsValid === 'string') {
    alert('Проверьте корректность данных:\n' + userDataIsValid);
    return false;
  }

  for (const group in groups_info) {
    tableResultCompareGroups.append(create_row_content(num_cols, group, groups_info[group]));
  }
}

// Функция формирует и записывает данные на странице для опции "Рассчитать направления в фазах"
function displayResultCalcGroupsInStages(responce_data) {
    textAreaResultCalcGroupsInStages.value = '';
  const userDataIsValid = responce_data.make_groups_in_stages.error_in_user_data;
  if (typeof userDataIsValid === 'string') {
    alert('Проверьте корректность данных:\n' + userDataIsValid);
    return false;
  }

  const result = responce_data.make_groups_in_stages.calculate_result;

  for(const key in result) {
    textAreaResultCalcGroupsInStages.value += `${key}\tНаправление\t${result[key].join(',')}\n`;
  }
}

// Удаляет строки таблицы
function remove_rows(table, rows_length, row_num_start) { 
  if (rows_length > row_num_start) {
    for (let i=rows_length-row_num_start; i>=row_num_start; i--) {
      table.deleteRow(i);
    }
  }
}

// Функция формирует строку с контентом для таблицы table_result(результат сравнения групп)
function create_row_content(num_cols, num_group, group_content) {

  let tr = document.createElement('tr');

  let td_num_group = document.createElement('td');
  let td_type_group = document.createElement('td');
  let td_stages = document.createElement('td');
  let td_errors = document.createElement('td');
  td_errors.setAttribute("class", "errors_content");

  td_num_group.textContent = num_group;
  td_type_group.textContent = group_content.type_group;
  td_stages.textContent = group_content.stages;
  const errors = group_content.errors;
  if (errors.length > 0) {
    errors.forEach((element, idx) => {
      td_errors.innerHTML += `${idx + 1}. ${element}`  + '<br>';
      td_errors.setAttribute("bgcolor", "red");
    });
  }

  tr.append(td_num_group);
  tr.append(td_type_group);
  tr.append(td_stages);
  tr.append(td_errors);
  return tr;
}

// Формирует контент элементов на странице в зависимости от выбранной опции в элементе select
function chooseOption(event) {
  // this.textContent --> получает все option!
  document.querySelectorAll('textarea').forEach((el) => {
    el.value = '';
  });
  remove_rows(tableResultCompareGroups, tableResultCompareGroups.rows.length, 1);
  if (this.value === optionsSelectChooseOption.nothing) {
    hideElements([tableCompareGroups, tableResultCompareGroups, btnCalculate, tableCompareGroups, tableResultCalcGroupsInStages]);
    return;
  }
  showElements([tableCompareGroups, tableResultCompareGroups, btnCalculate]);
  if (this.value === optionsSelectChooseOption.compare_groups) {
    textAreaTableGroup.disabled  = false;
    showElements([btnCalculate, tableCompareGroups, tableResultCompareGroups]);
    hideElements([tableResultCalcGroupsInStages]);
  }
  else if (this.value === optionsSelectChooseOption.calc_groups_in_stages) {
    textAreaTableGroup.disabled  = true;
    hideElements([tableResultCompareGroups]);
    showElements([tableResultCalcGroupsInStages]);
  }
}

// Проверяет выбрана ли опция перед отправкой запроса в api
function optionIsChecked() {
  if (selectChooseOption.value === optionsSelectChooseOption.nothing) {
    alert("Для отправки запроса выберите опцию");
    return false;
  }
  return true;
}

// Скрывает на странице переданные элементы
function hideElements(elements) {
  elements.forEach((elem) => elem.style.display = "none");
}

// Показывает на странице переданные элементы
function showElements(elements) {
  elements.forEach((elem) => elem.removeAttribute("style"));
}