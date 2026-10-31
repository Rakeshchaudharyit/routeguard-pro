from django.urls import path
from routing.views import health,geocode,analyze
urlpatterns=[path('api/health/',health),path('api/geocode/',geocode),path('api/routes/analyze/',analyze)]
