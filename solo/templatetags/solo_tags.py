from django import template
from django.apps import apps
from django.utils.translation import gettext as _

from solo import settings as solo_settings
from solo.models import SingletonModel

register = template.Library()


@register.simple_tag(name=solo_settings.GET_SOLO_TEMPLATE_TAG_NAME)
def get_solo(model_path: str) -> SingletonModel:
    try:
        app_label, model_name = model_path.rsplit(".", 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            _(
                "Templatetag requires the model dotted path: 'app_label.ModelName'. "
                "Received '{model_path}'."
            ).format(model_path=model_path)
        )
    try:
        model_class: type[SingletonModel] = apps.get_model(app_label, model_name)
    except LookupError:
        raise template.TemplateSyntaxError(
            _("Could not get the model name '{model}' from the application named '{app}'").format(
                model=model_name, app=app_label
            )
        )
    return model_class.get_solo()
