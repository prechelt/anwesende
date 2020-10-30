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

    def is_datenverwalter(self) -> bool:
        return self.is_authenticated \
            and self.groups.filter(pk=get_datenverwalter_group().pk).exists()

    @classmethod
    def get_datenverwalter_group(cls) -> djcam.Group:
        if cls._datenverwalter_group is None:
            cls._datenverwalter_group = djcam.Group.objects.get_by_natural_key(
                cls.STAFF_GROUP)
        return cls._datenverwalter_group
