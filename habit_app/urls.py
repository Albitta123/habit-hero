from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, HabitViewSet, HabitCheckinViewSet, debug_auth

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'habits', HabitViewSet, basename='habit')
router.register(r'checkins', HabitCheckinViewSet, basename='checkin')

urlpatterns = [
    path('', include(router.urls)),
    path('debug-auth/', debug_auth),
]
