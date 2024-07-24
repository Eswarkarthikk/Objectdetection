from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_image, name='upload_image'),
    path('task_status/<str:task_id>/', views.task_status, name='task_status'),
]