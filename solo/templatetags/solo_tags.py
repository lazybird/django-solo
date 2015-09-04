from django import template
from django.db import models
from django.utils.translation import ugettext as _

try:
    from django.apps import get_model
except ImportError:
    from django.db.models import get_model

from solo import settings as solo_settings


register = template.Library()


@register.assignment_tag(name=solo_settings.GET_SOLO_TEMPLATE_TAG_NAME)
def get_solo(model_path):
    try:
        app_label, model_name = model_path.rsplit('.', 1)
    except ValueError:
        raise template.TemplateSyntaxError(_(
            "Templatetag requires the model dotted path: 'app_label.ModelName'. "
            "Received '%s'." % model_path
        ))
    model_class = get_model(app_label, model_name)
    if not model_class:
        raise template.TemplateSyntaxError(_(
            "Could not get the model name '%(model)s' from the application "
            "named '%(app)s'" % {
                'model': model_name,
                'app': app_label,
            }
        ))
    return model_class.get_solo()
