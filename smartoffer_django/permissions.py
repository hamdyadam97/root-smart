from rest_framework import permissions


class CanManageOffers(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='can_manage_offers').exists()
        )


class CanSendOffers(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='can_send_offers').exists()
        )


class CanViewReports(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class CanManageEmployees(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='can_manage_employees').exists()
        )
