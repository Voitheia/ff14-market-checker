from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("build_market_data", views.build_market_data, name="build_market_data"),
    path("calc_item_stats", views.calc_item_stats, name="calc_item_stats")
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)