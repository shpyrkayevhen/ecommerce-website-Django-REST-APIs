from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return bool(request.user and request.user.is_staff)
# Then apply this to ProductViewSet


class ViewCustomerHistoryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Return True if the user has this permission
        return request.user.has_perm('store.view_history')


# class FullDjangoModelPermissions(permissions.DjangoModelPermissions):
#     def __init__(self):
#         # To send GET user must to have view_ permission in Group
#         self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']


# BasePermission: all permissions extends from this class
# Crate Custom Permissions. All users can get products
# but only admin can post, update, delete products
