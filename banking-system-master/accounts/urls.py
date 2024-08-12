# urls.py
from django.urls import path
from .views import UserRegistrationView, LogoutView, UserLoginView, dashboard_view

app_name = 'accounts'

urlpatterns = [
    path(
        "login/", UserLoginView.as_view(),
        name="user_login"
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "register/", UserRegistrationView.as_view(),
        name="user_registration"
    ),
    path(
        "dashboard/", dashboard_view,  # Corrected: Use the view function, not its result
        name="dashboard"
    ),
]
