from django.shortcuts import render


def prog(request):
    """Программирование ДК."""
    template = "prog/prog.html"
    prog = "programs"
    context = {
        "prog": prog,
    }
    return render(request, template, context)


def equipment_layout(request):
    """Схема расположения оборудования."""
    template = "prog/equipment_layout.html"
    return render(request, template)


def table_of_directions(request):
    """Таблица направлений."""
    template = "prog/table_of_directions.html"
    return render(request, template)


def phase_images(request):
    """Изображения фаз."""
    template = "prog/phase_images.html"
    return render(request, template)


def fixed_program_tables(request):
    """Таблицы фиксированных программ."""
    template = "prog/fixed_program_tables.html"
    return render(request, template)


def the_layout_of_the_detectors(request):
    """Схема расположения детекторов."""
    template = "prog/the_layout_of_the_detectors.html"
    return render(request, template)


def table_of_detectors(request):
    """Таблица детекторов."""
    template = "prog/table_of_detectors.html"
    return render(request, template)


def monitoring_of_peripheral_equipment(request):
    """Контроль периферийного оборудования."""
    template = "prog/monitoring_of_peripheral_equipment.html"
    return render(request, template)


def phase_alternation(request):
    """Чередование фаз."""
    template = "prog/phase_alternation.html"
    return render(request, template)


def adaptive_program_tables(request):
    """Таблицы адаптивных программ."""
    template = "prog/adaptive_program_tables.html"
    return render(request, template)
