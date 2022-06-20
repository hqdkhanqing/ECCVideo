from django.contrib import admin
from .models import User,App,Agent,ContainerData, AgentData

# Register your models here.

admin.site.register(User)
admin.site.register(Agent)
admin.site.register(App)
admin.site.register(ContainerData)
admin.site.register(AgentData)