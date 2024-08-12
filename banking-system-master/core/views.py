from django.views.generic import TemplateView





class HomeView(TemplateView):
    template_name = 'transactions/dashboard_view.html'