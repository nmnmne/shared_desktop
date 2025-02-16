"""board models configuration."""
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Rule(models.Model):
    """Модель правил."""

    name = models.CharField(max_length=200)
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rules"
    )
    responsible = models.TextField()
    comment = models.TextField()
    on_main = models.BooleanField(default=True)

    class Meta:
        """Метакласс модели правил."""

        verbose_name = "Правила"
        verbose_name_plural = "Правила"

    def __str__(self):
        """Возвращает название."""
        return self.name
