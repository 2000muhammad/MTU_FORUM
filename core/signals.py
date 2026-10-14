from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IntakeRequest, RequestNotification


@receiver(post_save, sender=IntakeRequest)
def notify_staff_about_new_request(sender, instance, created, **kwargs):
    if not created:
        return

    def create_notifications():
        recipient_ids = User.objects.filter(is_active=True).filter(
            Q(is_superuser=True) | Q(is_staff=True) | Q(profile__roles__can_requests=True)
        ).values_list("id", flat=True).distinct()
        RequestNotification.objects.bulk_create([
            RequestNotification(
                recipient_id=recipient_id,
                request=instance,
                kind=RequestNotification.Kind.CREATED,
                title=f"Новая заявка #{instance.pk}",
                message=instance.platform or instance.company or instance.full_name,
            )
            for recipient_id in recipient_ids
        ])

    transaction.on_commit(create_notifications)
