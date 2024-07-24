from . import views
from django.urls import path

urlpatterns=[
    path('',views.upload_image,name='upload_image'),
]

