
default_app_config = "djangoProject.apps.djangoProject"

# your_app_name/apps.py
from django.apps import AppConfig

class YourAppNameConfig(AppConfig):
    name = 'djangoProject'

    def ready(self):
        import djangoProject.signals
