from django.apps import AppConfig


class AiMatchingScoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessment.ai_matching_scores'
    label = 'assessment_ai_matching_scores'

    def ready(self):
        import apps.assessment.ai_matching_scores.signals
