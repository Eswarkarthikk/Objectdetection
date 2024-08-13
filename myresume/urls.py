from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_image, name='upload_image'),
    path('predict_heart_disease/', views.predict_heart_disease, name='predict_heart_disease'),

    # path('',views.opendigit,name='opendigit'),
    # path('predict/', views.predict, name='predict'),
    path('predict_fraud/', views.predict_fraud, name='predict_fraud'),
    path('task_status/<str:task_id>/', views.task_status, name='task_status'),
]