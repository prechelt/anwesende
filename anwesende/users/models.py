import django.contrib.auth.models as djcam
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(djcam.AbstractUser):
    """Default user for anwesende."""
    STAFF_GROUP = "datenverwalter"
    _datenverwalter_group = None  # cache
    #: First and last name do not cover name patterns around the globe:
    name = CharField(_("Name of User"), blank=True, max_length=255)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def assign_datenverwalter_group(self) -> None:
        self.groups.add(self.get_datenverwalter_group())

    def is_datenverwalter(self) -> bool:
        return self.groups.filter(pk=self.get_datenverwalter_group().pk).exists()

    @classmethod
    def get_datenverwalter_group(cls) -> djcam.Group:
        if cls._datenverwalter_group is None:
            if not djcam.Group.objects.filter(name=cls.STAFF_GROUP).exists():
                djcam.Group.objects.create(name=cls.STAFF_GROUP)
            cls._datenverwalter_group = djcam.Group.objects.get_by_natural_key(
                cls.STAFF_GROUP)
        return cls._datenverwalter_group
