import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preloved.settings')
django.setup()

from ads.models import State, Ads
from django.utils.text import slugify

INDIAN_STATES_AND_UTS = [
    # 28 States
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # 8 Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry"
]

print(f"Total states & UTs to seed: {len(INDIAN_STATES_AND_UTS)}")

# First, ensure Gujarat exists so any legacy ad pointing to non-Indian states can be migrated safely
gujarat, _ = State.objects.get_or_create(state_name="Gujarat", defaults={"slug": "gujarat"})

# Migrate existing ads from foreign/non-Indian states
non_indian_states = State.objects.exclude(state_name__in=INDIAN_STATES_AND_UTS)
for old_s in non_indian_states:
    print(f"Migrating ads from non-Indian state '{old_s.state_name}' to 'Gujarat'...")
    Ads.objects.filter(state=old_s).update(state=gujarat)
    old_s.delete()

# Create or update all Indian states & UTs
created_count = 0
existing_count = 0

for name in sorted(INDIAN_STATES_AND_UTS):
    slug = slugify(name)
    state_obj, created = State.objects.get_or_create(
        state_name=name,
        defaults={"slug": slug}
    )
    if not created and state_obj.slug != slug:
        state_obj.slug = slug
        state_obj.save()
    if created:
        created_count += 1
    else:
        existing_count += 1

print(f"Seeding completed successfully!")
print(f"Created: {created_count}, Existing: {existing_count}")
print(f"Total States in DB: {State.objects.count()}")

all_states = list(State.objects.all().order_by("state_name").values_list("state_name", flat=True))
print("States in DB:")
for i, s in enumerate(all_states, start=1):
    print(f"{i}. {s}")
