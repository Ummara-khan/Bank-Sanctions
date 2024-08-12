from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('list-management/', views.list_management, name='list_management'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('records-variations/', views.records_variations, name='records_variations'),
    path('view-variations/', views.view_variations, name='view_variations'),
    path('generate-test-data/', views.generate_test_data, name='generate_test_data'),
    path('record/<int:record_id>/', views.view_record, name='view_record'),
    path('update-variation/<uuid:variation_id>/', views.update_variation, name='update_variation'),
    path('delete-variation/<uuid:variation_id>/', views.delete_variation, name='delete_variation'),
    path('do-update-variation/<uuid:variation_id>/', views.do_update_variation, name='do_update_variation'),
    path('toggle_status/', views.toggle_status, name='toggle_status'),
    path('add-variation/<int:record_id>/', views.add_variation, name='add_variation'),
     path('disable_variation/<uuid:variation_id>/', views.disable_variation, name='disable_variation'),
]
