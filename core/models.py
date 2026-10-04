from django.db import models


class Provider(models.Model):
    FRAUD_CHOICES = [
        ('clean', 'Clean'),
        ('suspicious', 'Suspicious'),
        ('red_flag', 'Red Flag'),
    ]
    name = models.CharField(max_length=200)
    provider_id = models.CharField(max_length=20, unique=True)
    placement = models.FloatField(default=0.0)
    retention = models.FloatField(default=0.0)
    fraud_status = models.CharField(max_length=20, choices=FRAUD_CHOICES, default='clean')
    confidence = models.FloatField(default=0.0)
    trainees_count = models.IntegerField(default=0)

    @property
    def is_red_flag(self):
        return self.placement >= 80 and self.retention <= 20

    def __str__(self):
        return f"{self.name} ({self.provider_id})"


class Trainee(models.Model):
    DISTRICT_CHOICES = [
        ('Pune', 'Pune'), ('Mumbai', 'Mumbai'), ('Nagpur', 'Nagpur'),
        ('Nashik', 'Nashik'), ('Aurangabad', 'Aurangabad'), ('Nanded', 'Nanded'),
        ('Amravati', 'Amravati'), ('Solapur', 'Solapur'), ('Kolhapur', 'Kolhapur'),
        ('Thane', 'Thane'), ('Ratnagiri', 'Ratnagiri'), ('Latur', 'Latur'),
    ]
    COURSE_CHOICES = [
        ('Electrician', 'Electrician'), ('Welder', 'Welder'), ('Plumber', 'Plumber'),
        ('Tailoring', 'Tailoring'), ('Refrigeration', 'Refrigeration & AC'),
        ('Automotive', 'Automotive'), ('IT Support', 'IT Support'),
        ('Carpentry', 'Carpentry'), ('Beauty', 'Beauty & Wellness'),
    ]
    SCORE_LEVELS = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]

    master_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15)
    district = models.CharField(max_length=50)
    course = models.CharField(max_length=50)
    company_name = models.CharField(max_length=200, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    salary_slip = models.FileField(upload_to='salary_slips/', blank=True, null=True)
    shop_photo = models.FileField(upload_to='shop_photos/', blank=True, null=True)
    confidence_score = models.IntegerField(default=20)
    score_level = models.CharField(max_length=10, choices=SCORE_LEVELS, default='LOW')
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True)
    bank_verified = models.BooleanField(default=False)
    udyam_verified = models.BooleanField(default=False)
    employer_otp_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.confidence_score = min(100, self.confidence_score)
        if self.confidence_score >= 85:
            self.score_level = 'HIGH'
        elif self.confidence_score >= 60:
            self.score_level = 'MEDIUM'
        else:
            self.score_level = 'LOW'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.master_id})"


class ConsentLedger(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Revoked', 'Revoked')]
    consent_id = models.CharField(max_length=20, unique=True)
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='consents')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    duration_months = models.IntegerField(default=12)

    def __str__(self):
        return f"{self.consent_id} - {self.status}"


class VerificationEvent(models.Model):
    TYPE_CHOICES = [
        ('self_declaration', 'Self Declaration'),
        ('salary_slip', 'Salary Slip Upload'),
        ('bank', 'Bank Verification'),
        ('udyam', 'Udyam Verification'),
        ('employer_otp', 'Employer OTP Verification'),
    ]
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='verification_events')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainee.master_id} - {self.type} (+{self.points})"
