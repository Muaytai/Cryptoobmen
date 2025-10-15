from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


class SiteAdminRequiredMixin(LoginRequiredMixin):
    """
    Миксин для проверки прав администратора сайта в представлениях на основе классов.
    Пользователь должен быть либо суперпользователем, либо иметь флаг is_site_admin=True
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_site_administrator():
            messages.error(request, _('У вас нет прав для доступа к этой странице.'))
            raise PermissionDenied()
        
        return super().dispatch(request, *args, **kwargs)


class SiteAdminOrStaffRequiredMixin(LoginRequiredMixin):
    """
    Миксин для проверки прав администратора сайта или персонала в представлениях на основе классов.
    Пользователь должен быть либо суперпользователем, либо иметь флаг is_site_admin=True, либо is_staff=True
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_site_administrator() or request.user.is_staff):
            messages.error(request, _('У вас нет прав для доступа к этой странице.'))
            raise PermissionDenied()
        
        return super().dispatch(request, *args, **kwargs)
