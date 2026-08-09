from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle, AnonRateThrottle


class OTPRequestThrottle(SimpleRateThrottle):
    scope = "otp_request"

    def get_cache_key(self, request, view):
        phone_number = request.data.get("phone_number")
        if not phone_number:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": phone_number,
        }


class BurstUserRateThrottle(UserRateThrottle):
    scope = "burst"


class SustainedUserRateThrottle(UserRateThrottle):

    scope = "sustained"


class AnonBurstRateThrottle(AnonRateThrottle):
    scope = "anon_burst"


class SubscriptionRequestThrottle(UserRateThrottle):
    scope = "subscription_request"