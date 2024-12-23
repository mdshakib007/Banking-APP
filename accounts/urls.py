from django.urls import path
from accounts import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('update-profile/', views.UserAccountUpdateView.as_view(), name='update-profile'),
    path('change-password/', views.UserChangePassword.as_view(), name='change_password'),
]

