'use strict';

/*------------------------------------------------------------------------
|                            Старт страницы                              |
------------------------------------------------------------------------*/

$(document).ready(function(){

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
const ROUTE_API_TLC = `/api/v1/potok-tlc/`;

const input_condition = document.querySelector('#condition');
const idTableTokensFunctions = 'table_functions';
const idCreateFunctions = 'create_functions';
const idGetConditionResult = 'get_condition_result';
const idConditionResult = 'condition_result';
let   tableTokensFunctions = document.querySelector(`#${idTableTokensFunctions}`);
const btnCreateButtons = document.querySelector(`#${idCreateFunctions}`);
const btnGetConditionResult = document.querySelector(`#${idGetConditionResult}`);
const labelConditionResult = document.querySelector(`#${idConditionResult}`)
// const table_create_functions = document.querySelector('#table_functions');


/*------------------------------------------------------------------------
|                               Events                                   |
------------------------------------------------------------------------*/

btnCreateButtons.addEventListener('click', requestToApiAxios);
btnGetConditionResult.addEventListener('click', requestToApiAxios);


 /*------------------------------------------------------------------------
|                      Запрос в api и обработка запроса                   |
--------------------------------------------------------------------------*/

// Отправка запроса команды с помощью библиотеки axios
async function requestToApiAxios(event) {
  const condition = input_condition.value;
  console.log('condition: ' + condition);
  let get_functions_from_condition_string = false, get_condition_result = false;

  const data = {};
  let requestEntity;
  if (this.id == idCreateFunctions) {
    get_functions_from_condition_string = true;
  }
  else if (this.id == idGetConditionResult) {
    get_condition_result = true;
    data.get_condition_result = collectDataGetResultCondition();
  }

  const options = {
    get_functions_from_condition_string: get_functions_from_condition_string,
    get_condition_result: get_condition_result
  };

  
  let csrfToken = $("input[name=csrfmiddlewaretoken]").val();
  try {

      const response = await axios.post(ROUTE_API_TLC,          
          { 
            options: options,
            condition: condition,
            payload: data,
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

    if (this.id == idCreateFunctions) {
      createTableFunctions(res);
    }
    else if (this.id == idGetConditionResult) {
      createGetConditionResult(res);
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
      
    }

    finally {
      
    }
}

// Общая функция для обработки responce и формирования контента на странице


 /*------------------------------------------------------------------------
|            Запись полученых на странице в различные элементы            |
--------------------------------------------------------------------------*/

 /*------------------------------------------------------------------------
|   Создать таблицу с функциями из строки условия перехода/продления      |
--------------------------------------------------------------------------*/

// Создает <table> с функциями, полученными из строки "Условие перехода/продления"
function createTableFunctions(response) {
  console.log(response);
  const tokensFunctions = response.functions;
  const len_tr = Math.sqrt(tokensFunctions.length);
  // Если повторное нажатие на кнопку "Сформировать функции и условия", удаляем имеющуюся таблицу и формируем новую

  console.log(tableTokensFunctions);
  if (tableTokensFunctions !== null) {
    tableTokensFunctions.remove();
  }
  tableTokensFunctions = document.createElement('table');
  tableTokensFunctions.setAttribute('id', idTableTokensFunctions);

  let tr, td, chkbx, label;
  tr = document.createElement('tr');

  tokensFunctions.forEach((element, index, array) => {  
  td = document.createElement('td');
  chkbx = document.createElement('input');
  label = document.createElement('label');

  if (Math.floor(index % len_tr) == 0) {
    tableTokensFunctions.append(tr);
    tr = document.createElement('tr');
  }

  chkbx.setAttribute('type', 'checkbox');
  chkbx.id = element;
  label.setAttribute('for', element);
  label.innerHTML = element;

  td.append(chkbx);
  td.append(label);
  tr.append(td);
  });

  tableTokensFunctions.append(tr);
  console.log(tableTokensFunctions);  
  btnCreateButtons.after(tableTokensFunctions);
}

function createGetConditionResult(responce) {
  let res = responce.result
  labelConditionResult.innerHTML = `Результат условия с заданными значениями: ${res.toString().toUpperCase()}`;
}

function collectDataGetResultCondition() {
  let dataReq = {};
  let func_values = {};
  console.log(document.querySelectorAll(`#${idTableTokensFunctions} td`));
  document.querySelectorAll(`#${idTableTokensFunctions} td`).forEach((el) => {
    // console.log('elem text --> ' + el.textContent);
    // console.log('elem id --> ' + el.firstChild.id);
    // console.log('elem  firstChild --> ' + el.firstChild);
    // console.log('elem firstChild.checked  --> ' + el.firstChild.checked);
    if (el.firstChild.id != el.textContent) {
      alert('Произошла ошибка в расчёте. Нажмите еще раз копку "Сформировать функции из условия"')
      return false;
    }
    func_values[el.textContent] = Number(el.firstChild.checked);
    // conditionWithFuncValues = conditionWithFuncValues.replace(el.textContent, Number(el.firstChild.checked));

  });

  dataReq.func_values = func_values;
  console.log(dataReq);
  return dataReq;
}