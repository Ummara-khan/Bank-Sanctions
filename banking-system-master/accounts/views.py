from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect, reverse
from django.urls import reverse_lazy
from django.views.generic import FormView, RedirectView
from .forms import UserRegistrationForm

User = get_user_model()

class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('accounts:user_login')  # Redirect to login page after successful registration

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Thank you for creating an account. Please log in.')
        return HttpResponseRedirect(self.get_success_url())  # Redirect to login page

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('home'))  # Redirect to home if user is already authenticated
        return super().dispatch(request, *args, **kwargs)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        messages.success(self.request, 'Login successful.')
        return reverse_lazy('transactions:dashboard')  # Redirect to home page after successful login

class LogoutView(RedirectView):
    pattern_name = 'index'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
            messages.info(self.request, 'You have been logged out.')  # Optional: Show a logout message
        return super().get_redirect_url(*args, **kwargs)

# views.py
from django.shortcuts import render

def dashboard_view(request):
    # Render the template without any context
    return render(request, 'accounts/dashboard.html')


# views.py
from django.shortcuts import render

def home(request):
    return render(request, 'transactions/dashboard_view.html')

from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'core/index.html'
