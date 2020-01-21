from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('import/', views.importCSV, name='importCSV'),
    path('export/', views.exportCalendar, name='exportCalendar'),
    path('help/', views.helpPage, name='helpPage'),

]
