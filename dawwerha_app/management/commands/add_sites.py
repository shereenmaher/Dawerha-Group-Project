from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dawwerha_app.models import Profile, Collector, Material, CollectorPrice


SITES = [
    {
        'email': 'ammar.alard@dawwerha.test',
        'name': 'Ammar Al-Ard Recycling',
        'address': 'Al-Bireh',
        'lat': 31.9097,
        'lng': 35.2157,
        'hours': 'Sat–Thu 8:00–5:00',
        'is_available': True,
    },
    {
        'email': 'ramallah.center@dawwerha.test',
        'name': 'Ramallah Recycling Center',
        'address': 'Al-Masyoun, Ramallah',
        'lat': 31.9070,
        'lng': 35.1930,
        'hours': 'Sun–Thu 9:00–4:00',
        'is_available': False,
    },
    {
        'email': 'beitunia.center@dawwerha.test',
        'name': 'Beitunia Recycling Center',
        'address': 'Beitunia',
        'lat': 31.8930,
        'lng': 35.1700,
        'hours': 'Sat–Wed 7:30–3:00',
        'is_available': True,
    },
]


class Command(BaseCommand):
    help = "Add the demo recycling sites"

    def handle(self, *args, **options):
        for data in SITES:
            # Each site needs its own user account
            user, created = User.objects.get_or_create(
                username=data['email'],
                defaults={
                    'email': data['email'],
                    'first_name': data['name'],
                },
            )

            if created:
                user.set_unusable_password()
                user.save()

            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': "collector",
                    'phone': "0590000000",
                },
            )

            # Save the site as a recycling site ("point")
            site, created = Collector.objects.update_or_create(
                user=user,
                defaults={
                    'name': data['name'],
                    'kind': "point",
                    'phone': "0590000000",
                    'address': data['address'],
                    'lat': data['lat'],
                    'lng': data['lng'],
                    'hours': data['hours'],
                    'is_available': data['is_available'],
                },
            )

            # The site accepts every recyclable material in the database.
            # The demo price is the middle of the allowed range for each material.
            for material in Material.objects.filter(recyclable=True):
                CollectorPrice.objects.update_or_create(
                    collector=site,
                    material=material,
                    defaults={
                        'price_per_kg': (
                            material.min_price + material.max_price
                        ) / 2,
                    },
                )

            # A site doesn't buy materials that can't be recycled
            CollectorPrice.objects.filter(
                collector=site,
                material__recyclable=False,
            ).delete()

            self.stdout.write(f"Added: {site.name}")

        self.stdout.write(
            self.style.SUCCESS("The recycling sites are ready.")
        )