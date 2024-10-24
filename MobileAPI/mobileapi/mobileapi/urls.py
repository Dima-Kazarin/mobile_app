from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from mobileapp import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/product', views.ProductView, basename='product')
router.register(r'api/userproduct', views.UserProductView, basename='userproduct')
router.register(r'api/purchase', views.PurchaseView, basename='purchase')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/register/', views.register_view, name='register'),
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
] + router.urls