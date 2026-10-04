from django.contrib import admin
from .models import Trainee, ConsentLedger, VerificationEvent, Provider

admin.site.register(Trainee)
admin.site.register(ConsentLedger)
admin.site.register(VerificationEvent)
admin.site.register(Provider)
