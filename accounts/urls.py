from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, RegisterView, CustomLogoutView, ProfileView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Password Change Views
    path('password/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('password_change_done')
    ), name='password_change'),
    path('password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
]
