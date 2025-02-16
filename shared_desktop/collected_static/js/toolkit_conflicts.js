'use strict';

// Ловим событие изменения состояния radio типов дк
$('input[type=radio][name=controller_type]').change(function() {
  if ($('#undefind').is(':checked')) {
      $('#make_config').prop('checked', false);
      $('#binval_swarco').prop('checked', false);
      $('#binval_swarco').attr('disabled', true);
      $('#make_config').attr('disabled', true);
      $('#config_file').attr('disabled', true);   
  }
  else if ($('#swarco').is(':checked')) {
      $('#binval_swarco').attr('disabled', false);
      $('#make_config').attr('disabled', false);      
  }
  else {
      $('#binval_swarco').attr('disabled', true);
      $('#make_config').attr('disabled', false);
      $('#binval_swarco').prop('checked', false);
  }; 
});

// Ловим событие изменения чекбокса Создать файл конфигурации
$('#make_config').change( function() {
  if ($(this).is(':checked')){
    $('#config_file').attr('disabled', false);
  }
  else {
      $('#config_file').attr('disabled', true);
    };
    
});

// При нажатии на кнопку выбор файлов, установим необходимое раширение(для выбранного типа ДК) в браузере
$('#config_file').click( function (){
  if ($('#swarco').is(':checked')) {
    $(this).attr('accept', '.PTC2');
  }
  else if ($('#peek').is(':checked')){
    $(this).attr('accept', '.DAT');
  }

});


// Проверка валидности введенных/заполненных данных
$("form").submit(function () {
  const text_area = {
    text: $('#stages_from_area').val(),
    lines: $('#stages_from_area').val().split('\n'),
    num_lines: $('#stages_from_area').val().split('\n').length,
  };

  if (text_area.num_lines < 2) {
    alert('Количество фаз не может быть менее 2');
    return false;
  }

  // Проверка на корректность символов
  if (!check_text_area(text_area.lines)){
    return false;
  }
 
  // Проверка на количество фаз
  if (($('#swarco').is(':checked') && text_area.num_lines > 8)) {
    alert(`Количество фаз для Swarco не должно превышать 8. Вы ввели: ${text_area.num_lines}`);
    return false;
  }
  else if (($('#peek').is(':checked') && text_area.num_lines > 32)) {
    alert(`Количество фаз для Peek не должно превышать 32. Вы ввели: ${text_area.num_lines}`);
    return false;
  }

  else if (text_area.num_lines > 128) {
    alert(`Количество фаз для неопределённого типа ДК не должно превышать 128. Вы ввели: ${text_area.num_lines}`);
    return false;
  }

  // Проверка валидности данных при условии что выбран чекбокс "Создать файл конфигурации"
  if ($('#make_config').is(':checked')) {
    // Проверка на наличие файла
    if ($('#config_file')[0].files.length < 1) {
      alert('Вы не выбрали файл конфигурации');
      return false;
    }
    // Проверка на корректное расширение файла для каждого типа ДК
    let file_name = $('#config_file')[0].files[0].name;
    if ($('#swarco').is(':checked') && file_name.slice(-5).toUpperCase() != '.PTC2'){
      alert('Вы выбрали неверный формат файла конфигурации для Swarco. Выберите файл с раширением .PTC2');
      return false;
    }
    else if ($('#peek').is(':checked') && file_name.slice(-4).toUpperCase() != '.DAT'){
      alert('Вы выбрали неверный формат файла конфигурации для Peek. Выберите файл с раширением .DAT');
      return false;
    }
  }
  
});



// Проверка всего поля text_area на валидные символы
function check_text_area (stages) {
  for (let i = 0; i < stages.length; i++) {
    if (!check_string(stages[i], i + 1)) {
      return false;
    }
  }
  return true;

}
// Проверка строки на валидные символы
function check_string (stage_string, num_string, sep1=':', sep2=',') {
  if (stage_string.includes(sep1)) {
    stage_string = stage_string.replace(' ', '').split(sep1)[1];
  }
  let isNumber_last_char = /^\d+$/.test(stage_string.slice(-1));
  if (!isNumber_last_char) {
    alert(`Строка должна заканчиваться числовым номером направления. Проверьте строку ${num_string}`);
    return false;
  }
  let splited_string = stage_string.replace(' ', '').split(sep2);
  for(let ii = 0; ii < splited_string.length; ii++) {  
    let isNumber = /^\d+$/.test(splited_string[ii]);
    if (!isNumber) {
      alert(`Вы ввели не число в строке ${num_string}`);
      return false; 
    }
    else if (isNumber && (+splited_string[ii] > 128)) {
      alert(`Количество направлений не должно превышать 128. Вы ввели: ${splited_string[ii]} в строке ${num_string}`);
      return false;
    }
  }
  return true;
}
