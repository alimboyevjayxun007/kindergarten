from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.roles import ROLE_ACCOUNTANT, ROLE_ADMIN, ROLE_EDUCATOR


ROLE_USERS = [
	("adminuser", "admin@example.local", "Adminuser@12345", ROLE_ADMIN, True, True),
	("educator", "educator@example.local", "Educator@12345", ROLE_EDUCATOR, False, False),
	("accountant", "accountant@example.local", "Accountant@12345", ROLE_ACCOUNTANT, False, False),
]


class Command(BaseCommand):
	help = "Create application role groups and demo users for admin, educator, and accountant."

	def handle(self, *args: object, **options: object) -> None:
		User = get_user_model()
		groups = {name: Group.objects.get_or_create(name=name)[0] for name in (ROLE_ADMIN, ROLE_EDUCATOR, ROLE_ACCOUNTANT)}

		for username, email, password, role, is_staff, is_superuser in ROLE_USERS:
			user, created = User.objects.get_or_create(username=username, defaults={"email": email})
			user.email = email
			user.is_active = True
			user.is_staff = is_staff
			user.is_superuser = is_superuser
			user.set_password(password)
			user.save()
			user.groups.set([groups[role]])
			status = "created" if created else "updated"
			self.stdout.write(
				self.style.SUCCESS(
					f"{status}: {username} role={role} staff={user.is_staff} superuser={user.is_superuser}"
				)
			)
