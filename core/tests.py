from __future__ import annotations

from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
	Attendance,
	AttendanceStatus,
	Child,
	ChildStatus,
	Classroom,
	Guardian,
	KindergartenLocation,
	MonthlyBilling,
	MonthlyBillingStatus,
	Tariff,
)
from .forms import KindergartenLocationForm
from .roles import ROLE_ACCOUNTANT, ROLE_ADMIN, ROLE_EDUCATOR


def create_role_user(username: str, role: str, *, password: str = "testpass123"):
	User = get_user_model()
	user = User.objects.create_user(username=username, password=password)
	group, _ = Group.objects.get_or_create(name=role)
	user.groups.add(group)
	return user


class ModelSmokeTests(TestCase):
	def test_can_create_models(self) -> None:
		classroom = Classroom.objects.create(name="Sunflowers", age_group="3-4", capacity=10)
		child = Child.objects.create(
			first_name="Emma",
			last_name="Smith",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			status=ChildStatus.ACTIVE,
		)
		guardian = Guardian.objects.create(
			first_name="Olivia",
			last_name="Smith",
			phone="+11234567890",
			email="olivia.smith@example.com",
			child=child,
			is_primary=True,
		)

		self.assertEqual(str(classroom), "Sunflowers")
		self.assertEqual(str(child), "Emma Smith")
		self.assertEqual(str(guardian), "Olivia Smith")


class ClassroomListViewTests(TestCase):
	def test_list_view_returns_200_when_logged_in(self) -> None:
		user = create_role_user("testuser", ROLE_ADMIN)

		classroom = Classroom.objects.create(name="Rainbows", age_group="4-5", capacity=12)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:classroom_list"))

		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, classroom.name)


class KindergartenLocationTests(TestCase):
	def test_form_requires_latitude_and_longitude_together(self) -> None:
		form = KindergartenLocationForm(
			data={
				"name": "Anvar Bog'cha",
				"address": "Samarkand",
				"latitude": "39.654200",
				"longitude": "",
			}
		)

		self.assertFalse(form.is_valid())
		self.assertIn("Latitude and longitude must be entered together.", form.errors["__all__"])

	def test_location_page_saves_coordinates_when_logged_in(self) -> None:
		User = get_user_model()
		user = User.objects.create_superuser(
			username="locationuser",
			email="location@example.com",
			password="testpass123",
		)

		self.client.force_login(user)
		resp = self.client.post(
			reverse("core:kindergarten_location"),
			{
				"name": "Anvar Bog'cha",
				"address": "Samarkand, Uzbekistan",
				"latitude": "39.654200",
				"longitude": "66.959700",
			},
		)

		self.assertEqual(resp.status_code, 302)
		location = KindergartenLocation.get_solo()
		self.assertEqual(location.address, "Samarkand, Uzbekistan")
		self.assertEqual(str(location.latitude), "39.654200")
		self.assertEqual(str(location.longitude), "66.959700")
		self.assertIn("39.654200,66.959700", location.google_maps_url)

	def test_location_page_uses_map_picker(self) -> None:
		User = get_user_model()
		user = User.objects.create_superuser(
			username="maplocationuser",
			email="maplocation@example.com",
			password="testpass123",
		)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:kindergarten_location"))

		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'id="locationMap"')
		self.assertContains(resp, 'type="hidden" name="latitude"')
		self.assertContains(resp, 'type="hidden" name="longitude"')

	def test_location_page_requires_superuser(self) -> None:
		user = create_role_user("locationadmin", ROLE_ADMIN)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:kindergarten_location"))

		self.assertEqual(resp.status_code, 403)

	def test_landing_page_shows_map_when_location_has_coordinates(self) -> None:
		location = KindergartenLocation.get_solo()
		location.latitude = "39.654200"
		location.longitude = "66.959700"
		location.save()

		resp = self.client.get(reverse("core:home"))

		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'class="landing-location-frame"')
		self.assertContains(resp, "openstreetmap.org/export/embed.html")
		self.assertContains(resp, "marker=39.654200%2C66.959700")
		self.assertNotContains(resp, "39.654200, 66.959700")


class AttendanceTests(TestCase):
	def test_status_choices_include_expected_present_absent_late_half_day(self) -> None:
		values = {value for value, _label in AttendanceStatus.choices}
		self.assertIn(AttendanceStatus.EXPECTED, values)
		self.assertIn(AttendanceStatus.PRESENT, values)
		self.assertIn(AttendanceStatus.ABSENT, values)
		self.assertIn(AttendanceStatus.LATE, values)
		self.assertIn(AttendanceStatus.HALF_DAY, values)

	def test_list_view_autocreates_records_for_empty_date_when_logged_in(self) -> None:
		user = create_role_user("attuser", ROLE_EDUCATOR)
		classroom = Classroom.objects.create(name="Stars", age_group="5-6", capacity=10)
		child = Child.objects.create(
			first_name="Ava",
			last_name="Davis",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			status=ChildStatus.ACTIVE,
		)

		self.assertEqual(Attendance.objects.count(), 0)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:attendance_list"))

		self.assertEqual(resp.status_code, 200)
		self.assertTrue(Attendance.objects.filter(child=child).exists())
		self.assertContains(resp, child.last_name)


class MonthlyBillingTests(TestCase):
	def test_list_view_autocreates_rows_for_month(self) -> None:
		user = create_role_user("mbuser", ROLE_ACCOUNTANT)

		classroom = Classroom.objects.create(name="MB", age_group="3-4", capacity=10)
		tariff = Tariff.objects.create(name="Standard", amount="500.00", is_active=True)
		child = Child.objects.create(
			first_name="Ava",
			last_name="Jones",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			tariff=tariff,
			status=ChildStatus.ACTIVE,
		)

		self.assertEqual(MonthlyBilling.objects.count(), 0)
		self.client.force_login(user)
		resp = self.client.get(reverse("core:billing_monthly_list"), {"month": "2025-12"})
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(MonthlyBilling.objects.filter(child=child, billing_month="2025-12").exists())
		row = MonthlyBilling.objects.get(child=child, billing_month="2025-12")
		self.assertEqual(str(row.amount), "500.00")
		self.assertContains(resp, child.last_name)

	def test_mark_paid_uses_child_and_month(self) -> None:
		user = create_role_user("mbuser2", ROLE_ACCOUNTANT)
		classroom = Classroom.objects.create(name="MB2", age_group="3-4", capacity=10)
		tariff = Tariff.objects.create(name="Premium", amount="600.00", is_active=True)
		child = Child.objects.create(
			first_name="Mason",
			last_name="Smith",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			tariff=tariff,
			status=ChildStatus.ACTIVE,
		)

		self.client.force_login(user)
		resp = self.client.post(
			reverse("core:billing_monthly_mark", kwargs={"status": "paid"}),
			{"child": str(child.pk), "month": "2025-12"},
		)
		self.assertEqual(resp.status_code, 302)
		row = MonthlyBilling.objects.get(child=child, billing_month="2025-12")
		self.assertEqual(str(row.amount), "600.00")
		self.assertEqual(row.status, MonthlyBillingStatus.PAID)
		self.assertIsNotNone(row.paid_at)


class RoleAccessTests(TestCase):
	def setUp(self) -> None:
		self.admin = create_role_user("roleadmin", ROLE_ADMIN)
		self.educator = create_role_user("roleeducator", ROLE_EDUCATOR)
		self.accountant = create_role_user("roleaccountant", ROLE_ACCOUNTANT)

	def test_educator_can_use_attendance_and_see_guardians_only(self) -> None:
		self.client.force_login(self.educator)

		self.assertEqual(self.client.get(reverse("core:attendance_list")).status_code, 200)
		self.assertEqual(self.client.get(reverse("core:guardian_list")).status_code, 200)
		self.assertEqual(self.client.get(reverse("core:billing_monthly_list")).status_code, 403)
		self.assertEqual(self.client.get(reverse("core:child_list")).status_code, 403)

	def test_accountant_can_use_billing_and_tariffs_only(self) -> None:
		self.client.force_login(self.accountant)

		self.assertEqual(self.client.get(reverse("core:billing_monthly_list")).status_code, 200)
		self.assertEqual(self.client.get(reverse("core:tariff_list")).status_code, 200)
		self.assertEqual(self.client.get(reverse("core:attendance_list")).status_code, 403)
		self.assertEqual(self.client.get(reverse("core:guardian_list")).status_code, 403)

	def test_admin_can_open_all_crm_sections(self) -> None:
		self.client.force_login(self.admin)

		for url_name in (
			"core:dashboard",
			"core:attendance_list",
			"core:billing_monthly_list",
			"core:tariff_list",
			"core:classroom_list",
			"core:child_list",
			"core:guardian_list",
		):
			with self.subTest(url_name=url_name):
				self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

	def test_login_redirects_to_role_default_page(self) -> None:
		password = "testpass123"
		user = create_role_user("redirectaccountant", ROLE_ACCOUNTANT, password=password)
		resp = self.client.post(
			reverse("login"),
			{"username": user.username, "password": password},
		)

		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp["Location"], reverse("core:dashboard"))

	def test_landing_shows_dashboard_button_for_logged_in_role(self) -> None:
		self.client.force_login(self.accountant)
		resp = self.client.get(reverse("core:home"))

		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "Dashboard")
		self.assertContains(resp, f'href="{reverse("core:dashboard")}"')
		self.assertNotContains(resp, f'href="{reverse("login")}"')

	def test_dashboard_renders_role_specific_content(self) -> None:
		for user, expected_text in (
			(self.admin, "Tezkor amallar"),
			(self.educator, "Bugungi davomat"),
			(self.accountant, "Moliyaviy holat"),
		):
			with self.subTest(user=user.username):
				self.client.force_login(user)
				resp = self.client.get(reverse("core:dashboard"))
				self.assertEqual(resp.status_code, 200)
				self.assertContains(resp, "Dashboard")
				self.assertContains(resp, expected_text)
				self.client.logout()


class SetupRoleUsersCommandTests(TestCase):
	def test_setup_role_users_creates_admin_superuser(self) -> None:
		call_command("setup_role_users", verbosity=0)

		User = get_user_model()
		admin = User.objects.get(username="adminuser")

		self.assertTrue(admin.is_staff)
		self.assertTrue(admin.is_superuser)
		self.assertTrue(admin.groups.filter(name=ROLE_ADMIN).exists())

# Create your tests here.
