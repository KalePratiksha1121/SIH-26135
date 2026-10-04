from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trainee-form/', views.trainee_form, name='trainee_form'),
    path('consent-ledger/', views.consent_ledger, name='consent_ledger'),
    path('consent/<int:consent_id>/revoke/', views.revoke_consent, name='revoke_consent'),
    path('verification/', views.verification, name='verification'),
    path('verification/<int:trainee_id>/', views.verification, name='verification_detail'),
    path('verify-otp/<int:trainee_id>/', views.verify_otp, name='verify_otp'),
    path('confidence-engine/', views.confidence_engine, name='confidence_engine'),
    path('provider-ranking/', views.provider_ranking, name='provider_ranking'),
    path('fraud-detection/', views.fraud_detection, name='fraud_detection'),
    path('seed/', views.seed_data, name='seed'),
]
