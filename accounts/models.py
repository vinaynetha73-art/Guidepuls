from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# ================= USER PROFILE =================

class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(max_length=15, blank=True, null=True)

    profile_pic = models.ImageField(upload_to="profiles/", default="profiles/default.jpg")

    rescue_count = models.IntegerField(default=0)

    vehicle = models.CharField(max_length=10, default="bike")

    def __str__(self):
        return self.user.username
# ================= FIRST AID =================

class FirstAidTopic(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=[
        ('Low','Low'), ('Medium','Medium'), ('High','High')
    ])

    def __str__(self):
        return self.title


class FirstAidStep(models.Model):
    topic = models.ForeignKey(FirstAidTopic, related_name="steps", on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return self.description


# ================= EMERGENCY CONTACT =================

class EmergencyContact(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name} - {self.phone}"


# ================= CALL HISTORY =================

class EmergencyCallHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    called_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"


# ================= DONOR =================

class Donor(models.Model):
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100, default="Unknown")
    group = models.CharField(max_length=5, default="O+")
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name} ({self.group})"
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ==========================================
# USER LIVE LOCATION
# ==========================================

class UserLiveLocation(models.Model):

    user = models.OneToOneField(User,on_delete=models.CASCADE)

    latitude = models.FloatField()

    longitude = models.FloatField()

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class EmergencyAlert(models.Model):

    victim = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    latitude = models.FloatField()

    longitude = models.FloatField()

    created_at = models.DateTimeField(
        default=timezone.now
    )

    is_active = models.BooleanField(
        default=True
    )

    accepted_count = models.IntegerField(
        default=0
    )

    max_capacity = models.IntegerField(
        default=5
    )

    def __str__(self):
        return f"{self.victim.username} Emergency"

# ==========================================
# RESCUE MODEL
# ==========================================

class Rescue(models.Model):

    STATUS_CHOICES = (
        ("accepted","Accepted"),
        ("rejected","Rejected"),
        ("completed","Completed")
    )

    alert = models.ForeignKey(
        EmergencyAlert,
        on_delete=models.CASCADE
    )

    rescuer = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    victim_closed = models.BooleanField(
        default=False
    )

    joined_at = models.DateTimeField(
        default=timezone.now
    )

    left_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed = models.BooleanField(
        default=False
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.rescuer.username} helping {self.alert.victim.username}"


# ==========================================
# EMERGENCY LOG
# ==========================================

class EmergencyLog(models.Model):

    victim = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    latitude = models.FloatField()

    longitude = models.FloatField()

    started_at = models.DateTimeField(
        default=timezone.now
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True
    )

    helpers_joined = models.IntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.victim.username} emergency log"