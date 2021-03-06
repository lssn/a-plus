from django.utils.translation import ugettext_lazy as _

from authorization.permissions import Permission, ObjectVisibleBasePermission
from .models import MenuItem, LTIService


class MenuVisiblePermission(ObjectVisibleBasePermission):
    message = _("Permission denied by menu visibility")
    model = MenuItem
    obj_var = 'menu_item'

    def is_object_visible(self, request, view, menu_item):
        if (not menu_item.enabled
                or (menu_item.service and not menu_item.service.enabled)):
            return False

        if menu_item.access >= MenuItem.ACCESS.TEACHER:
            if not view.is_teacher:
                self.error_msg(request, _("The link is only for teachers."))
                return False

        elif menu_item.access >= MenuItem.ACCESS.ASSISTANT:
            if not view.is_course_staff:
                self.error_msg(request, _("The link is only for course staff."))
                return False

        return True


class LTIServicePermission(Permission):
    message = _("Not LTI service")

    def has_permission(self, request, view):
        return self.has_object_permission(request, view, view.menu_item)

    def has_object_permission(self, request, view, obj):
        return (obj.service
            and isinstance(obj.service.as_leaf_class(), LTIService))
