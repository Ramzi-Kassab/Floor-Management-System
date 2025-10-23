from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

VIEW = ["view"]
CRUD = ["view", "add", "change", "delete"]

GROUPS = {
    "Ops Lead": {
        "floor_app.Employee": CRUD,
        # add your real models here…
    },
    "Inventory": {
        # "floor_app.Batches": CRUD,
    },
    "QC": {
        # "floor_app.BitEvaluation": CRUD,
    },
    "HR": {
        "floor_app.Employee": CRUD,
    },
    "Viewer": {
        "floor_app.Employee": VIEW,
    },
}

def get_ct(model_path):
    app_label, model_name = model_path.split(".")
    model = apps.get_model(app_label, model_name)
    return ContentType.objects.get_for_model(model)

def perms_for(model_path, actions):
    ct = get_ct(model_path)
    codes = [f"{a}_{ct.model}" for a in actions]
    return Permission.objects.filter(content_type=ct, codename__in=codes)

class Command(BaseCommand):
    help = "Create/update default groups and permissions"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Replace group's permissions instead of adding")

    def handle(self, *args, **opts):
        reset = opts["reset"]
        for gname, mapping in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=gname)
            wanted = []
            for model_path, actions in mapping.items():
                try:
                    wanted += list(perms_for(model_path, actions))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping {model_path}: {e}"))
            if reset:
                group.permissions.set(wanted)
            else:
                group.permissions.add(*wanted)
            self.stdout.write(self.style.SUCCESS(
                f"{gname}: {len(wanted)} permissions {'replaced' if reset else 'added'}."
            ))
        self.stdout.write(self.style.SUCCESS("All groups seeded."))
