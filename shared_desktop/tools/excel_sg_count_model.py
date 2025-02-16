import io
import pandas as pd

from tools.models import PhaseParameterSet

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect


def excel_sg_count_model(request):
    parameter_sets = PhaseParameterSet.objects.all()
    selected_set = None
    data = {}

    if request.method == "POST":
        if "upload_button" in request.POST:
            selected_set_name = request.POST.get("parameter_set")

            # Если выбрана опция "Выберите сохраненные настройки" (пустое значение), не выполнять дальнейшие действия
            if not selected_set_name:
                print("Пожалуйста, выберите сохраненные настройки.")
            else:
                try:
                    selected_set = PhaseParameterSet.objects.get(
                        name=selected_set_name
                    )
                    data = selected_set.data
                except PhaseParameterSet.DoesNotExist:
                    print("Выбранные настройки не найдены.")

            # Заполните контекст данными для предварительного заполнения формы
            context = {
                "parameter_sets": parameter_sets,
                "selected_set": selected_set,
                "data": data,
                "selected_set_name": selected_set_name,
            }
            return render(request, "tools/excel_sg_count_model.html", context)

        elif "save_button" in request.POST:
            name = request.POST.get("name")
            base_name = name
            counter = 1

            # Проверка на существование имени и добавление суффикса
            while PhaseParameterSet.objects.filter(name=name).exists():
                name = f"{base_name}_"

            primary_group = request.POST.get("primary_group")
            groups = {
                f"group{i}": request.POST.get(f"group{i}")
                for i in range(1, 21)
            }
            phases = {
                f"phases{i}": request.POST.get(f"phases{i}")
                for i in range(1, 21)
            }

            data = {"primary_group": primary_group, **groups, **phases}

            # Сохраните экземпляр PhaseParameterSet
            PhaseParameterSet.objects.create(name=name, data=data)
            return redirect("/tools/excel_sg_count_model/")

        elif "process_button" in request.POST:
            print("Pressed: Загрузить и обработать")

            if request.FILES.get("file"):
                uploaded_file = request.FILES["file"]
                try:
                    df = pd.read_excel(
                        uploaded_file
                    )  # Чтение Excel файла в DataFrame

                    # Извлечение групп фаз из данных формы
                    phase_groups = []
                    primary_group = request.POST.get(
                        "primary_group"
                    )  # Извлечение основной группы
                    for i in range(1, 21):
                        group_name = request.POST.get(f"group{i}")
                        phases = request.POST.get(f"phases{i}")
                        if group_name and phases:
                            phases_list = [
                                int(phase.strip())
                                for phase in phases.split(",")
                            ]
                            phase_groups.append((group_name, phases_list))

                    # Добавление специальной группы -1 -2
                    phase_groups.append(("-1", [-1, -2]))

                    # Использование имени основной группы для специального условия
                    if phase_groups and primary_group:
                        primary_group_name = next(
                            (
                                name
                                for name, _ in phase_groups
                                if f"group{phase_groups.index((name, _)) + 1}"
                                == primary_group
                            ),
                            None,
                        )
                        if not primary_group_name:
                            return HttpResponseBadRequest(
                                "Ошибка: не выбрана основная группа."
                            )
                    else:
                        return HttpResponseBadRequest(
                            "Ошибка: не заданы фазы или не выбрана основная группа."
                        )

                    # Преобразование столбца "Начало" в формат даты и времени
                    df["Начало"] = pd.to_datetime(df["Начало"])
                    current_group = None
                    duration_sum = 0
                    cycle_count = 0
                    results = []

                    # Функция для обработки перехода между группами
                    def handle_transition(
                        new_group, duration_sum, cycle_count
                    ):
                        nonlocal current_group
                        if (
                            new_group != current_group
                            and current_group is not None
                        ):
                            results.append(
                                (
                                    current_group,
                                    duration_sum,
                                    cycle_count,
                                    end_index,
                                )
                            )
                            duration_sum = 0
                            # Проверка, что основная группа есть в текущей группе, но отсутствует в предыдущей
                            if (
                                primary_group_name in new_group
                                and primary_group_name not in current_group
                            ):
                                cycle_count += 1
                            # Увеличиваем счетчик циклов, если фаза -1 или -2
                            if any(phase in ["-1", "-2"] for phase in new_group):
                                cycle_count += 1
                        return new_group, duration_sum, cycle_count

                    # Основной цикл по строкам DataFrame
                    for index in range(len(df)):
                        row = df.iloc[index]
                        stat_value = row["Stat Value"]
                        duration = row["Длительность"]
                        current_hour = row["Начало"].strftime("%Y-%m-%d %H")

                        new_group = []
                        for group_name, phases in phase_groups:
                            if stat_value in phases:
                                new_group.append(group_name)

                        if not new_group:
                            continue

                        # Сортировка групп по числовым значениям
                        new_group = sorted(
                            new_group,
                            key=lambda x: (int("".join(filter(str.isdigit, x))) if any(map(str.isdigit, x)) else 0, x),
                        )


                        current_group, duration_sum, cycle_count = (
                            handle_transition(
                                new_group, duration_sum, cycle_count
                            )
                        )
                        duration_sum += duration
                        end_index = index

                    # Добавление результатов последней группы
                    if current_group is not None:
                        results.append(
                            (
                                current_group,
                                duration_sum,
                                cycle_count,
                                len(df) - 1,
                            )
                        )

                    # Инициализация новых столбцов
                    df["Группы"] = None
                    df["Общая длительность"] = None
                    df["Счетчик циклов"] = None

                    # Заполнение новых столбцов по результатам
                    for result in results:
                        groups, total_duration, cycle_count, end_index = result
                        df.at[end_index, "Группы"] = ", ".join(groups)
                        df.at[end_index, "Общая длительность"] = total_duration
                        df.at[end_index, "Счетчик циклов"] = cycle_count

                    # Инициализация столбцов для каждой группы, кроме -1
                    for group_name, _ in phase_groups:
                        if group_name != "-1":
                            df[f"Время {group_name} группы"] = None

                    # Подсчет количества циклов за каждый час
                    hourly_cycle_counts = (
                        df.groupby(df["Начало"].dt.floor("h"))[
                            "Счетчик циклов"
                        ]
                        .apply(
                            lambda x: x.ffill().bfill().max()
                            - x.ffill().bfill().min()
                        )
                        .reset_index()
                    )

                    # Заполнение данных по часам
                    summary_data = []
                    for index, row in hourly_cycle_counts.iterrows():
                        hour = row["Начало"]
                        cycle_count = row["Счетчик циклов"]
                        first_index = df[
                            df["Начало"].dt.floor("h") == hour
                        ].index[0]
                        df.at[first_index, "Количество циклов"] = cycle_count

                        hour_data = df[df["Начало"].dt.floor("h") == hour]

                        hour_summary = {
                            "Начало": hour,
                            "Количество циклов": cycle_count,
                        }
                        for group_name, _ in phase_groups:
                            if group_name != "-1":
                                # Проверка наличия группы {group_name} в точности в списке фаз для каждой строки в hour_data
                                total_group_time = hour_data[
                                    hour_data.apply(
                                        lambda x: (
                                            group_name
                                            in x["Группы"].split(", ")
                                            if isinstance(x["Группы"], str)
                                            else False
                                        ),
                                        axis=1,
                                    )
                                ]["Общая длительность"].sum()
                                df.at[
                                    first_index, f"Время {group_name} группы"
                                ] = total_group_time
                                hour_summary[f"Время {group_name} группы"] = (
                                    total_group_time
                                )
                        summary_data.append(hour_summary)

                    # Создание итогового DataFrame для суммарного времени
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.rename(
                        columns={"Начало": "Период"}, inplace=True
                    )
                    summary_df["Период"] = summary_df["Период"].apply(
                        lambda x: f"{x.strftime('%Y-%m-%d')} с {x.strftime('%H:%M')} до {(x + pd.Timedelta(hours=1)).strftime('%H:%M')}"
                    )

                    # Создание итогового DataFrame для среднего времени за цикл
                    average_data = []
                    for index, row in summary_df.iterrows():
                        hour_summary = {
                            "Период": row["Период"],
                            "Количество циклов": row["Количество циклов"],
                        }
                        for group_name, _ in phase_groups:
                            if group_name != "-1":
                                total_group_time = row.get(
                                    f"Время {group_name} группы", 0
                                )
                                cycle_count = row["Количество циклов"]
                                average_time_per_cycle = (
                                    total_group_time / cycle_count
                                    if cycle_count > 0
                                    else 0
                                )
                                hour_summary[f"{group_name} н"] = round(
                                    average_time_per_cycle
                                )
                        average_data.append(hour_summary)

                    average_df = pd.DataFrame(average_data)

                    # Сохранение данных в новый Excel файл
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        # Сохранение исходных данных на первый лист
                        df.to_excel(writer, sheet_name="Данные", index=False)

                        # Создание второго листа "Время работы направлений за час"
                        summary_df.to_excel(
                            writer,
                            sheet_name="Время работы направлений за час",
                            index=False,
                        )

                        # Сохранение данных в третий лист "Среднее время за цикл"
                        average_df.to_excel(
                            writer,
                            sheet_name="Среднее время за цикл",
                            index=False,
                        )

                        wb = writer.book

                        # Автоматическое изменение ширины столбцов
                        for sheet_name in [
                            "Данные",
                            "Время работы направлений за час",
                            "Среднее время за цикл",
                        ]:
                            ws = wb[sheet_name]
                            for col in ws.columns:
                                max_length = 0
                                column = col[0].column_letter
                                for cell in col:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(str(cell.value))
                                    except:
                                        pass
                                adjusted_width = max_length + 2
                                ws.column_dimensions[column].width = (
                                    adjusted_width
                                )

                    # Возврат файла пользователю
                    output.seek(0)
                    response = HttpResponse(
                        output,
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    response["Content-Disposition"] = (
                        "attachment; filename=processed_data.xlsx"
                    )
                    return response
                except Exception as e:
                    return HttpResponseBadRequest(
                        f"Ошибка обработки файла: {e}"
                    )

    context = {
        "parameter_sets": parameter_sets,
        "selected_set": selected_set,
        "data": data,
    }

    return render(request, "tools/excel_sg_count_model.html", context)
