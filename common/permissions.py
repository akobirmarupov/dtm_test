from rest_framework.permissions import BasePermission, SAFE_METHODS

from common.models import Role


# studentlar uchun
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.STUDENT
        )


# ustozlar uchun test yaratadi va tekshiradi
class IsMentor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.MENTOR
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsMentorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.MENTOR, Role.ADMIN)
        )


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        return owner is not None and owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None)
        return owner is not None and owner == request.user

# ---------------------------------------------------------------------------
# Obuna darajasi bo'yicha ruxsatlar
# ---------------------------------------------------------------------------
# Qoidalar `billing.entitlements` da jamlangan: bu klasslar faqat o'sha
# yagona manbadan o'qiydi. Shuning uchun admin panelda tarif cheklovi
# o'zgarsa, bu yerdagi kod tegilmaydi.
class _EntitlementPermission(BasePermission):
    message = "Bu imkoniyat sizning tarifingizda mavjud emas."

    def entitlements(self, request):
        from billing.entitlements import entitlements_for_request
        return entitlements_for_request(request)


class IsRegistered(_EntitlementPermission):
    """Ro'yxatdan o'tgan har qanday foydalanuvchi (Free ham, Pro ham).

    Guest uchun natija, statistika va reyting yopiq.
    """

    message = "Buning uchun ro'yxatdan o'tishingiz kerak."

    def has_permission(self, request, view):
        return self.entitlements(request).is_authenticated


class IsPro(_EntitlementPermission):
    """Faol Pro obunasi bor foydalanuvchi (Pro-Basic yoki Pro-Full)."""

    message = "Bu imkoniyat Pro tarifda ochiladi."

    def has_permission(self, request, view):
        return self.entitlements(request).is_pro


class CanViewExplanations(_EntitlementPermission):
    """Yechim izohlarini ko'rish huquqi.

    Aynan `is_pro` EMAS: admin Pro-Basic da izohni yoqib/o'chirib qo'yishi
    mumkin, va kelajakda Free uchun ham cheklangan holda ochilishi mumkin.
    """

    message = "Yechim izohlari sizning tarifingizda mavjud emas."

    def has_permission(self, request, view):
        return self.entitlements(request).can_view_explanations


class HasFeature(_EntitlementPermission):
    """Nomlangan flag bo'yicha ruxsat (`Plan.features` JSON).

    Ishlatilishi:

        class AITutorView(APIView):
            permission_classes = [IsAuthenticated, HasFeature.named('ai_tutor')]
    """

    feature_name = None

    @classmethod
    def named(cls, feature_name, message=None):
        return type(
            f'HasFeature_{feature_name}',
            (cls,),
            {
                'feature_name': feature_name,
                'message': message or cls.message,
            },
        )

    def has_permission(self, request, view):
        if not self.feature_name:
            return False
        return bool(self.entitlements(request).feature(self.feature_name, False))
