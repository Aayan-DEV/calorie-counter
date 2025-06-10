from django.apps import AppConfig

class MystorelinkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mystorelink'
    
    def ready(self):
        import mystorelink.signals