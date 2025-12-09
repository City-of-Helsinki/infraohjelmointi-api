"""
ClassProgrammerAssignment model for IO-756.

This model provides direct User to ProjectClass assignments for restricted programmers,
replacing the email to name matching approach.
"""
import uuid
from django.conf import settings
from django.db import models


class ClassProgrammerAssignment(models.Model):
    """
    Direct mapping from User to ProjectClass for restricted programmer permissions.
    
    This provides a direct database relationship for permission checks.
    
    Usage:
        - Assign users via Django admin
        - Permission class checks this table for access
        - Multiple users can be assigned to the same class
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="class_programmer_assignments",
        help_text="The user who can edit projects in this class"
    )
    project_class = models.ForeignKey(
        "ProjectClass",
        on_delete=models.CASCADE,
        related_name="programmer_assignments",
        help_text="The project class this user can edit"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'project_class']]
        verbose_name = "Class Programmer Assignment"
        verbose_name_plural = "Class Programmer Assignments"
        indexes = [
            models.Index(fields=['user'], name='idx_cpa_user'),
            models.Index(fields=['project_class'], name='idx_cpa_class'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.project_class.name}"


# Admin configuration
from django.contrib import admin


class ClassProgrammerAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing restricted programmer assignments.
    
    This allows admins to assign users to specific project classes
    for the restricted programmer permission system.
    """
    list_display = ['get_user_email', 'get_class_name', 'created_date']
    list_filter = ['project_class']
    search_fields = ['user__email', 'project_class__name', 'project_class__path']
    raw_id_fields = ['user', 'project_class']
    ordering = ['user__email', 'project_class__name']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_class_name(self, obj):
        return obj.project_class.name
    get_class_name.short_description = 'Project Class'
    get_class_name.admin_order_field = 'project_class__name'
