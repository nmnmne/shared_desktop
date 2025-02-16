import io
import pandas as pd

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render


def excel_phase_count(request):
    if request.method == "POST" and request.FILES.get("file"):
        # Чтение загруженного файла
        uploaded_file = request.FILES["file"]
        try:
            df = pd.read_excel(
                uploaded_file
            )  # Чтение Excel файла в DataFrame)

            # Извлечение групп фаз из данных формы
            phase_groups = []
            for i in range(1, 9):
                group_name = request.POST.get(f"group{i}")
                phases = request.POST.get(f"phases{i}")
                if group_name and phases:
                    phases_list = [
                        int(phase.strip()) for phase in phases.split(",")
                    ]
                    phase_groups.append((group_name, phases_list))

            # Добавление специальной группы -1
            phase_groups.append(("-1", [-1]))

            # Использование имени первой группы для специального условия
            if phase_groups:
                first_group_name = phase_groups[0][0]
            else:
                return HttpResponseBadRequest("Ошибка: не заданы фазы.")

            # Преобразование столбца "Начало" в формат даты и времени
            df["Начало"] = pd.to_datetime(df["Начало"])
            current_group = None
            duration_sum = 0
            cycle_count = 0
            results = []

            # Функция для обработки перехода между группами
            def handle_transition(new_group, duration_sum, cycle_count):
                nonlocal current_group
                if new_group != current_group and current_group is not None:
                    results.append(
                        (current_group, duration_sum, cycle_count, end_index)
                    )
                    duration_sum = 0
                    if new_group == first_group_name or new_group == "-1":
                        cycle_count += 1
                return new_group, duration_sum, cycle_count

            # Основной цикл по строкам DataFrame
            for index in range(len(df)):
                row = df.iloc[index]
                stat_value = row["Stat Value"]
                duration = row["Длительность"]
                current_hour = row["Начало"].strftime("%Y-%m-%d %H")

                new_group = None
                for group_name, phases in phase_groups:
                    if stat_value in phases:
                        new_group = group_name
                        break

                if new_group is None:
                    continue

                current_group, duration_sum, cycle_count = handle_transition(
                    new_group, duration_sum, cycle_count
                )
                duration_sum += duration
                end_index = index

            # Добавление результатов последней группы
            if current_group is not None:
                results.append(
                    (current_group, duration_sum, cycle_count, len(df) - 1)
                )

            # Инициализация новых столбцов
            df["Группа"] = None
            df["Общая длительность"] = None
            df["Счетчик циклов"] = None

            # Заполнение новых столбцов по результатам
            for result in results:
                group, total_duration, cycle_count, end_index = result
                df.at[end_index, "Группа"] = group
                df.at[end_index, "Общая длительность"] = total_duration
                df.at[end_index, "Счетчик циклов"] = cycle_count

            # Инициализация столбцов для каждой группы, кроме -1
            for group_name, _ in phase_groups:
                if group_name != "-1":
                    df[f"Время {group_name} (сек)"] = None

            # Подсчет количества циклов за каждый час
            hourly_cycle_counts = (
                df.groupby(df["Начало"].dt.floor("h"))["Счетчик циклов"]
                .apply(
                    lambda x: x.ffill().bfill().max() - x.ffill().bfill().min()
                )
                .reset_index()
            )

            # Заполнение данных по часам
            for index, row in hourly_cycle_counts.iterrows():
                hour = row["Начало"]
                cycle_count = row["Счетчик циклов"]
                first_index = df[df["Начало"].dt.floor("h") == hour].index[0]
                df.at[first_index, "Количество циклов"] = cycle_count

                hour_data = df[df["Начало"].dt.floor("h") == hour]
                for group_name, _ in phase_groups:
                    if group_name != "-1":
                        total_group_time = hour_data[
                            hour_data["Группа"] == group_name
                        ]["Общая длительность"].sum()
                        df.at[first_index, f"Время {group_name} (сек)"] = (
                            total_group_time
                        )

                total_hour_time = sum(
                    df.at[first_index, f"Время {group_name} (сек)"]
                    for group_name, _ in phase_groups
                    if group_name != "-1"
                )
                df.at[first_index, "Общее время за час (сек)"] = (
                    total_hour_time
                )

                # Общая длительность за час (сек)
                total_duration_for_hour = hour_data["Длительность"].sum()
                df.at[first_index, "Общая длительность за час (сек)"] = (
                    total_duration_for_hour
                )

            # Создание итогового DataFrame
            summary_df = df[
                ["Начало", "Количество циклов"]
                + [
                    f"Время {group_name} (сек)"
                    for group_name, _ in phase_groups
                    if group_name != "-1"
                ]
                + ["Общее время за час (сек)"]
            ].dropna(subset=["Количество циклов"])

            # Добавление столбцов для среднего времени направления
            for group_name, _ in phase_groups:
                if group_name != "-1":
                    summary_df[f"Среднее время {group_name} (сек)"] = (
                        summary_df.apply(
                            lambda row: (
                                int(
                                    round(
                                        row[f"Время {group_name} (сек)"]
                                        / row["Количество циклов"]
                                    )
                                )
                                if row["Количество циклов"] > 0
                                else 0
                            ),
                            axis=1,
                        )
                    )

            # Добавление столбца, который суммирует все столбцы среднего времени
            summary_df["Среднее время цикла (сек)"] = summary_df[
                [
                    f"Среднее время {group_name} (сек)"
                    for group_name, _ in phase_groups
                    if group_name != "-1"
                ]
            ].sum(axis=1)

            # Добавление столбца "Период"
            summary_df["Период"] = summary_df["Начало"].apply(
                lambda x: f"{x.strftime('%Y-%m-%d')} с {x.strftime('%H')}:00 до {int(x.strftime('%H')) + 1}:00"
            )

            # Удаление столбца "Начало"
            summary_df = summary_df.drop(columns=["Начало"])

            # Переупорядочение столбцов, чтобы "Период" был первым
            columns_order = ["Период"] + [col for col in summary_df.columns if col != "Период"]
            summary_df = summary_df[columns_order]

            summary_simple_df = summary_df[
                ["Период", "Количество циклов", "Среднее время цикла (сек)"]
                + [
                    f"Среднее время {group_name} (сек)"
                    for group_name, _ in phase_groups
                    if group_name != "-1"
                ]
            ]

            # Сохранение данных в новый Excel файл
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Данные", index=False)
                summary_df.to_excel(
                    writer, sheet_name="Расширенный итог", index=False
                )
                summary_simple_df.to_excel(
                    writer, sheet_name="Итого", index=False
                )

                wb = writer.book
                ws_data = wb["Данные"]
                ws_summary_extended = wb["Расширенный итог"]
                ws_summary = wb["Итого"]

                # Автоматическое изменение ширины столбцов
                for ws in [ws_data, ws_summary_extended, ws_summary]:
                    for col in ws.columns:
                        max_length = 0
                        column = col[0].column_letter
                        for cell in col:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except:
                                pass
                        adjusted_width = max_length + 2
                        if column == "A" and ws == ws_data:
                            adjusted_width *= 2.5
                        ws.column_dimensions[column].width = adjusted_width

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
            return HttpResponseBadRequest(f"Ошибка обработки файла: {e}")
    return render(request, "tools/excel_phase_count.html")
