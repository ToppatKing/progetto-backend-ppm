from rest_framework.routers import DefaultRouter

from .views import ReservationViewSet

app_name = "reservations"

router = DefaultRouter()
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = router.urls
