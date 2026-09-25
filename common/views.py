from rest_framework import status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from common.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'type', 'rating', 'title', 'message', 'created_at']


class FeedbackCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            feedback = serializer.save(user=user)
            return Response({
                "status": "success",
                "message": "Fikr va taklifingiz qabul qilindi",
                "data": FeedbackSerializer(feedback).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
