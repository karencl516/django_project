from rest_framework import permissions


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff:
                return True
            return request.user.groups.filter(name='Manager').exists()
        return False

def is_manager(user):
    return user.is_staff or user.groups.filter(name='Manager').exists()

def is_delivery_crew(user):
    return user.groups.filter(name='Delivery crew').exists()
