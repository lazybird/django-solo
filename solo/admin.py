from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
try:
    from django.utils.encoding import force_unicode
except ImportError:
    from django.utils.encoding import force_text as force_unicode 
from django.utils.translation import ugettext as _


class SingletonModelAdmin(admin.ModelAdmin):
    object_history_template = "admin/solo/object_history.html"
    change_form_template = "admin/solo/change_form.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super(SingletonModelAdmin, self).get_urls()

        # _meta.model_name only exists on Django>=1.6 -
        # on earlier versions, use module_name.lower()
        try:
            model_name = self.model._meta.model_name
        except AttributeError:
            model_name = self.model._meta.module_name.lower()

        self.model._meta.verbose_name_plural = self.model._meta.verbose_name
        url_name_prefix = '%(app_name)s_%(model_name)s' % {
            'app_name': self.model._meta.app_label,
            'model_name': model_name,
        }
        custom_urls = [
            url(r'^history/$',
                self.admin_site.admin_view(self.history_view),
                {'object_id': '1'},
                name='%s_history' % url_name_prefix),
            url(r'^$',
                self.admin_site.admin_view(self.change_view),
                {'object_id': '1'},
                name='%s_change' % url_name_prefix),
        ]
        # By inserting the custom URLs first, we overwrite the standard URLs.
        return custom_urls + urls

    def response_change(self, request, obj):
        msg = _('%(obj)s was changed successfully.') % {'obj': force_unicode(obj)}
        if '_continue' in request.POST:
            self.message_user(request, msg + ' ' + _('You may edit it again below.'))
            return HttpResponseRedirect(request.path)
        else:
            self.message_user(request, msg)
            return HttpResponseRedirect("../../")

    def change_view(self, request, object_id, extra_context=None):
        if object_id == '1':
            self.model.objects.get_or_create(pk=1)
        return super(SingletonModelAdmin, self).change_view(
            request,
            object_id,
            extra_context=extra_context,
        )
