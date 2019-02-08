from django.db import models


class Search(models.Model):
    query = models.CharField(
        verbose_name='',
        blank=True,
        max_length=128)
    toptext = models.CharField(
        verbose_name='Text top',
        blank=True,
        max_length=128)
    bottomtext = models.CharField(
        verbose_name='Text bottom',
        blank=True,
        max_length=128)
