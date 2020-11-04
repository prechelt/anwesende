import django.contrib.auth.models as djcam
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(djcam.AbstractUser):
    """Default user for anwesende."""
    STAFF_GROUP = "datenverwalter"
    #: First and last name do not cover name patterns around the globe:
    name = CharField(_("Name of User"), blank=True, max_length=255)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def assign_datenverwalter_group(self) -> None:
        group = self.get_datenverwalter_group()
        assert group.id == 1
        self.groups.add(group)

    def is_datenverwalter(self) -> bool:
        return self.groups.filter(id=self.get_datenverwalter_group().id).exists()

    @classmethod
    def get_datenverwalter_group(cls) -> djcam.Group:
        if not djcam.Group.objects.filter(name=cls.STAFF_GROUP).exists():
            fresh_group = djcam.Group.objects.create(name=cls.STAFF_GROUP)  # noqa
        return djcam.Group.objects.get_by_natural_key(cls.STAFF_GROUP)
