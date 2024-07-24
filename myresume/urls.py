from . import views
from django.urls import path

urlpatterns=[
    #path('',views.mainpage,name='mainpage'), 
    path('',views.upload_image,name='upload_image')
]

