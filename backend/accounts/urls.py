from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserDocumentViewSet, UserProfileViewSet, SocialLoginCallbackView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'documents', UserDocumentViewSet, basename='document')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('social/callback/', SocialLoginCallbackView.as_view(), name='social_login_callback'),
] 