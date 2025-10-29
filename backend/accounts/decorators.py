from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


def site_admin_required(view_func):
    """
    Декоратор для проверки прав администратора сайта.
    Пользователь должен быть либо суперпользователем, либо иметь флаг is_site_admin=True
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_site_administrator():
            messages.error(request, _('У вас нет прав для доступа к этой странице.'))
            return HttpResponseForbidden()
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def site_admin_or_staff_required(view_func):
    """
    Декоратор для проверки прав администратора сайта или персонала.
    Пользователь должен быть либо суперпользователем, либо иметь флаг is_site_admin=True, либо is_staff=True
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_site_administrator() or request.user.is_staff):
            messages.error(request, _('У вас нет прав для доступа к этой странице.'))
            return HttpResponseForbidden()
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
