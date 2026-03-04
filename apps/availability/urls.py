from django.urls import path
from apps.availability.views import (
    ParishListApi, ParishDetailApi,
    MinisterListApi, MinisterDetailApi,
    MinisterWeeklyApi, MinisterAvailableSlotsApi,
    AvailableMinistersApi, MinisterCalendarApi,
    ServiceTypeListApi, ServiceTypeDetailApi
)

urlpatterns = [
    path('parishes/', ParishListApi.as_view(), name='parish-list'),
    path('parishes/<slug:slug>/', ParishDetailApi.as_view(), name='parish-detail'),
    
    path('services/', ServiceTypeListApi.as_view(), name='service-type-list'),
    path('services/<slug:slug>/', ServiceTypeDetailApi.as_view(), name='service-type-detail'),
    
    path('ministers/', MinisterListApi.as_view(), name='minister-list'),
    path('ministers/<slug:slug>/', MinisterDetailApi.as_view(), name='minister-detail'),
    
    path('ministers/<slug:slug>/weekly/', MinisterWeeklyApi.as_view(), name='minister-weekly'),
    path('ministers/<slug:slug>/available/', MinisterAvailableSlotsApi.as_view(), name='minister-available'),
    
    path('available/', AvailableMinistersApi.as_view(), name='available-ministers'),
    path('calendar/<slug:slug>/', MinisterCalendarApi.as_view(), name='minister-calendar'),
]
