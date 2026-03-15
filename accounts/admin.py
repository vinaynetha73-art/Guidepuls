from django.contrib import admin
from .models import UserProfile, EmergencyContact, EmergencyCallHistory, Donor, FirstAidTopic, FirstAidStep
from .models import UserLiveLocation

admin.site.register(EmergencyContact)
admin.site.register(EmergencyCallHistory)
admin.site.register(Donor)
from django.contrib import admin
from .models import FirstAidTopic, FirstAidStep

class FirstAidStepInline(admin.TabularInline):
    model = FirstAidStep
    extra = 3   # show 3 step fields by default

@admin.register(FirstAidTopic)
class FirstAidTopicAdmin(admin.ModelAdmin):
    inlines = [FirstAidStepInline]

admin.site.register(FirstAidStep)
admin.site.register(UserLiveLocation)