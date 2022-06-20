from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Allows access only to superusers.
    """
    #global permissions, that are run against all incoming requests
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
        
    #only run against operations that affect a particular object instance
    def has_object_permission(self,request,view,object):
        return request.user and request.user.is_superuser

class IsSuperUserOrOwner(BasePermission):
    def has_object_permission(self,request,view,object):
        return request.user and (request.user.id== object.id or request.user.is_superuser)

class IsStaffOrOwner(BasePermission):
    def has_object_permission(self,request,view,object):
        return request.user and (request.user.id== object.id or request.user.is_staff)

class IsStaffOrUploader(BasePermission):
    def has_object_permission(self,request,view,object):
        return request.user and (request.user.id== object.uploader.id or request.user.is_staff)

class IsStaffOrRegistrant(BasePermission):
    def has_object_permission(self,request,view,object):
        return request.user and (request.user.id== object.registrant.id or request.user.is_staff)

class IsStaffOrCommiter(BasePermission):
    def has_object_permission(self,request,view,object):
        return request.user and (request.user.id== object.commiter.id or request.user.is_staff)
        