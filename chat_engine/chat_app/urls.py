from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path("chat/<str:session_id>/", views.index, name="index"),
    path('api/get_script/', views.get_script, name="get_script"),
    path('static/<path:path>', views.get_static_file, name="get_static_file")
]