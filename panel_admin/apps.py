import os
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class PanelAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'panel_admin'
    verbose_name = 'Panel Admin'
