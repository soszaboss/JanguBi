from django.contrib.admin.apps import AdminConfig as BaseAdminConfig


class CustomAdminConfig(BaseAdminConfig):
    default_site = "apps.custom_admin.sites.AdminSite"
