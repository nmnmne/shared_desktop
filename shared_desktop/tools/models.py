"""tools models configuration."""

from django.db import models
from django.utils import timezone


class Central(models.Model):
    """Модель координации."""

    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address",
        protocol="both",
        unique=True,
    )
    phase_value = models.PositiveSmallIntegerField(
        verbose_name="phase_value",
        choices=[
            (0, "LOCAL"),
            (2, "1 фаза"),
            (3, "2 фаза"),
            (4, "3 фаза"),
            (5, "4 фаза"),
            (6, "5 фаза"),
            (7, "6 фаза"),
            (8, "7 фаза"),
            (9, "8 фаза"),
            (10, "9 фаза"),
            (11, "10 фаза"),
            (12, "11 фаза"),
            (13, "12 фаза"),
            (14, "13 фаза"),
            (15, "14 фаза"),
            (16, "15 фаза"),
            (17, "16 фаза"),
            (18, "17 фаза"),
            (19, "18 фаза"),
            (20, "19 фаза"),
            (21, "20 фаза"),
            (22, "21 фаза"),
            (23, "22 фаза"),
            (24, "23 фаза"),
            (25, "24 фаза"),
            (26, "25 фаза"),
            (27, "26 фаза"),
            (28, "27 фаза"),
            (29, "28 фаза"),
            (30, "29 фаза"),
            (31, "30 фаза"),
            (32, "31 фаза"),
            (33, "32 фаза"),
            (34, "33 фаза"),
            (35, "34 фаза"),
            (36, "35 фаза"),
            (37, "36 фаза"),
            (38, "37 фаза"),
            (39, "38 фаза"),
            (40, "39 фаза"),
            (41, "40 фаза"),
            (42, "41 фаза"),
            (43, "42 фаза"),
            (44, "43 фаза"),
            (45, "44 фаза"),
            (46, "45 фаза"),
            (47, "46 фаза"),
            (48, "47 фаза"),
            (49, "48 фаза"),
            (50, "49 фаза"),
            (51, "50 фаза"),
            (52, "51 фаза"),
            (53, "52 фаза"),
            (54, "53 фаза"),
            (55, "54 фаза"),
            (56, "55 фаза"),
            (57, "56 фаза"),
            (58, "57 фаза"),
            (59, "58 фаза"),
            (60, "59 фаза"),
            (61, "60 фаза"),
            (62, "61 фаза"),
            (63, "62 фаза"),
            (64, "63 фаза"),
            (65, "64 фаза"),
        ],
        default=0,
    )
    protocol = models.CharField(
        verbose_name="protocol",
        max_length=5,
        choices=[
            (0, "-"),
            ("UTMC", "UTMC"),
            ("STCIP", "STCIP"),
            ("UG405", "UG405"),
        ],
        default=0,
    )

    def __str__(self):
        return self.ip_address

    class Meta:
        verbose_name = "Техническая координация."
        verbose_name_plural = "Техническая координация"


class PhaseParameterSet(models.Model):
    name = models.CharField(max_length=255, unique=True)
    data = models.JSONField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сохранение полей excel скрипта"
        verbose_name_plural = "Сохранение полей excel скрипта"


class UtcParameterSet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    num_controllers = models.IntegerField()
    timeout = models.IntegerField()
    data = models.JSONField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сохранение полей phase_control"
        verbose_name_plural = "Сохранение полей phase_control"


class SaveConflictsTXT(models.Model):
    source = models.CharField(max_length=20)
    file = models.FileField(upload_to='conflicts/txt/', null=True)
    time_create = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SaveConflictsTXT"
        verbose_name_plural = "SaveConflictsTXT"
