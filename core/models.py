"""
Models for RBAC system.
Reference: LR5 - Building the Django Models
Reference: LR2 - Multi-Tenant Data Isolation & Roles
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Org(models.Model):
    """Organization with immutable admin."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    admin = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="admin_of_org",
        help_text="The ORG_ADMIN (immutable at creation)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if not self.pk:
            return

        old_org = Org.objects.only("admin_id").get(pk=self.pk)

        if old_org.admin_id != self.admin_id:
            raise ValidationError({
                "admin": "Organization admin cannot be changed after creation."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Admin: {self.admin.username})"


class UserOrgRole(models.Model):
    """
    Track PI and READ_ONLY users inside an organization.

    ORG_ADMIN is not stored here.
    ORG_ADMIN is stored in Org.admin and is immutable after Org creation.
    """

    ROLE_CHOICES = [
        ("PI", "Principal Investigator"),
        ("READ_ONLY", "Read-Only User"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="org_roles",
        limit_choices_to={"is_superuser": False},
    )

    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "org"],
                name="unique_user_role_per_org",
            )
        ]

    def clean(self):
        if self.user_id and self.user.is_superuser:
            raise ValidationError({
                "user": "Superuser cannot be assigned an organization role."
            })

        if self.org_id and self.user_id and self.org.admin_id == self.user_id:
            raise ValidationError({
                "user": "Organization admin cannot also be assigned PI or READ_ONLY role."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} → {self.org.name} ({self.role})"


class Project(models.Model):
    """Project within an organization."""
    name = models.CharField(max_length=100)
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['org', 'name'],
                name='unique_project_name_per_org'
            )
        ]

    def __str__(self):
        return f"{self.org.name} / {self.name}"
