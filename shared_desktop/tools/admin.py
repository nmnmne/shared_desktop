from django.contrib import admin

from .models import PhaseParameterSet, UtcParameterSet, Central


class ToolsAdmin(admin.ModelAdmin): ...


admin.site.register(Central, ToolsAdmin)
admin.site.register(PhaseParameterSet, ToolsAdmin)
admin.site.register(UtcParameterSet, ToolsAdmin)
# admin.site.register(SaveConfigFiles, ToolsAdmin)
# admin.site.register(SaveConflictsTXT, ToolsAdmin)
