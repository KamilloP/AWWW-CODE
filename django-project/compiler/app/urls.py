from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('delete/folder', views.deleteFolder, name="deleteFolder"),
    path('delete/file', views.deleteFile, name="deleteFile"),
    path('file', views.file, name="fileInfo"),
    path('postFolderForm', views.postFolderForm, name="postFolderForm"),
    path('postFileForm', views.postFileForm, name="postFileForm"),
    path('save/file', views.saveFile, name="saveFile"),
    path('compile', views.compileFile, name="compileFile"),
]
