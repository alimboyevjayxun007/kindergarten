from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import QuerySet
from datetime import date

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import AttendanceForm, ChildForm, ClassroomForm, GuardianForm, KindergartenLocationForm, TariffForm, SearchQuery, child_search_filter, classroom_search_filter
from .models import (
	Attendance,
	AttendanceStatus,
	Child,
	ChildStatus,
	Classroom,
	Guardian,
	KindergartenLocation,
	Tariff,
	MonthlyBilling,
	MonthlyBillingStatus,
)
from .roles import ROLE_ACCOUNTANT, ROLE_ADMIN, ROLE_EDUCATOR, RoleRequiredMixin, SuperuserRequiredMixin
from .roles import default_url_for_user, primary_role


class PageTitleMixin:
	page_title: str | None = None

	def get_page_title(self) -> str:
		if self.page_title:
			return self.page_title
		model = getattr(self, "model", None)
		if model is None:
			return "Forma"
		return str(model._meta.verbose_name).title()

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["page_title"] = self.get_page_title()
		return ctx


class HomeView(TemplateView):
	template_name = "core/home.html"

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["kindergarten_location"] = KindergartenLocation.get_solo()
		return ctx


def health_check(request: HttpRequest) -> JsonResponse:
	return JsonResponse({"status": "ok"})


class RoleAwareLoginView(LoginView):
	template_name = "registration/login.html"

	def get_success_url(self) -> str:
		redirect_to = self.get_redirect_url()
		if redirect_to:
			return redirect_to
		return reverse(default_url_for_user(self.request.user))


class DashboardView(LoginRequiredMixin, TemplateView):
	template_name = "core/dashboard.html"

	def _attendance_stats(self) -> dict[str, int]:
		today = timezone.localdate()
		qs = Attendance.objects.filter(attendance_date=today)
		return {
			"present": qs.filter(status=AttendanceStatus.PRESENT).count(),
			"late": qs.filter(status=AttendanceStatus.LATE).count(),
			"absent": qs.filter(status=AttendanceStatus.ABSENT).count(),
			"expected": qs.filter(status=AttendanceStatus.EXPECTED).count(),
		}

	def _billing_stats(self) -> dict[str, int | Decimal | str]:
		month = timezone.localdate().strftime("%Y-%m")
		qs = MonthlyBilling.objects.filter(billing_month=month)
		return {
			"month": month,
			"paid": qs.filter(status=MonthlyBillingStatus.PAID).count(),
			"unpaid": qs.filter(status=MonthlyBillingStatus.UNPAID).count(),
			"paid_amount": qs.filter(status=MonthlyBillingStatus.PAID).aggregate(total=models.Sum("amount"))["total"] or Decimal("0"),
			"unpaid_amount": qs.filter(status=MonthlyBillingStatus.UNPAID).aggregate(total=models.Sum("amount"))["total"] or Decimal("0"),
		}

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		role = primary_role(self.request.user)
		if not role:
			raise PermissionDenied("Rol biriktirilmagan.")
		ctx["page_title"] = "Dashboard"
		ctx["dashboard_role"] = role
		ctx["attendance_stats"] = self._attendance_stats()
		ctx["billing_stats"] = self._billing_stats()
		ctx["classroom_count"] = Classroom.objects.count()
		ctx["active_child_count"] = Child.objects.filter(status=ChildStatus.ACTIVE).count()
		ctx["guardian_count"] = Guardian.objects.count()
		ctx["tariff_count"] = Tariff.objects.count()
		ctx["location"] = KindergartenLocation.get_solo()
		return ctx


class KindergartenLocationUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, PageTitleMixin, UpdateView):
	model = KindergartenLocation
	form_class = KindergartenLocationForm
	template_name = "core/kindergarten_location_form.html"
	success_url = reverse_lazy("core:kindergarten_location")
	page_title = "Bog'cha GPS joylashuvi"

	def get_object(self, queryset: QuerySet[KindergartenLocation] | None = None) -> KindergartenLocation:
		return KindergartenLocation.get_solo()

	def form_valid(self, form: KindergartenLocationForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Bog'cha GPS joylashuvi saqlandi.")
		return response


class ClassroomListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN,)
	model = Classroom
	template_name = "core/classroom_list.html"
	context_object_name = "classrooms"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Classroom]:
		qs: QuerySet[Classroom] = Classroom.objects.all().order_by("name")
		search = SearchQuery.from_request(self.request)
		if search.q:
			qs = qs.filter(classroom_search_filter(search.q))
		return qs

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ClassroomCreateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, CreateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Classroom
	form_class = ClassroomForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:classroom_list")
	page_title = "Guruh yaratish"

	def form_valid(self, form: ClassroomForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Guruh yaratildi.")
		return response


class ClassroomUpdateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, UpdateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Classroom
	form_class = ClassroomForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:classroom_list")
	page_title = "Guruhni tahrirlash"

	def form_valid(self, form: ClassroomForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Guruh yangilandi.")
		return response


class ClassroomDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
	allowed_roles = (ROLE_ADMIN,)
	model = Classroom
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:classroom_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Guruh o‘chirildi.")
		return super().form_valid(form)


class ChildListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN,)
	model = Child
	template_name = "core/child_list.html"
	context_object_name = "children"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Child]:
		qs: QuerySet[Child] = Child.objects.select_related("classroom").all()
		search = SearchQuery.from_request(self.request)
		if search.q:
			qs = qs.filter(child_search_filter(search.q))
		return qs.order_by("last_name", "first_name")

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ChildCreateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, CreateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Child
	form_class = ChildForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:child_list")
	page_title = "Bola qo‘shish"

	def form_valid(self, form: ChildForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Bola qo‘shildi.")
		return response


class ChildUpdateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, UpdateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Child
	form_class = ChildForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:child_list")
	page_title = "Bolani tahrirlash"

	def form_valid(self, form: ChildForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Bola yangilandi.")
		return response


class ChildDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
	allowed_roles = (ROLE_ADMIN,)
	model = Child
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:child_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Bola o‘chirildi.")
		return super().form_valid(form)


class GuardianListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	model = Guardian
	template_name = "core/guardian_list.html"
	context_object_name = "guardians"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Guardian]:
		return Guardian.objects.select_related("child", "child__classroom").order_by(
			"last_name", "first_name"
		)


class GuardianCreateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, CreateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Guardian
	form_class = GuardianForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:guardian_list")
	page_title = "Vasiy qo‘shish"

	def form_valid(self, form: GuardianForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Vasiy qo‘shildi.")
		return response


class GuardianUpdateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, UpdateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Guardian
	form_class = GuardianForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:guardian_list")
	page_title = "Vasiyni tahrirlash"

	def form_valid(self, form: GuardianForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Vasiy yangilandi.")
		return response


class GuardianDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
	allowed_roles = (ROLE_ADMIN,)
	model = Guardian
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:guardian_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Vasiy o‘chirildi.")
		return super().form_valid(form)


class TariffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN, ROLE_ACCOUNTANT)
	model = Tariff
	template_name = "core/tariff_list.html"
	context_object_name = "tariffs"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Tariff]:
		qs: QuerySet[Tariff] = Tariff.objects.all().order_by("-is_active", "name")
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))
		return qs

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class TariffCreateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, CreateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Tariff
	form_class = TariffForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:tariff_list")
	page_title = "Tarif yaratish"

	def form_valid(self, form: TariffForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Tarif yaratildi.")
		return response


class TariffUpdateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, UpdateView):
	allowed_roles = (ROLE_ADMIN,)
	model = Tariff
	form_class = TariffForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:tariff_list")
	page_title = "Tarifni tahrirlash"

	def form_valid(self, form: TariffForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Tarif yangilandi.")
		return response


class TariffDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
	allowed_roles = (ROLE_ADMIN,)
	model = Tariff
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:tariff_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Tarif o‘chirildi.")
		return super().form_valid(form)


def _parse_date(value: str | None) -> date:
	if not value:
		return timezone.localdate()
	try:
		return datetime.strptime(value, "%Y-%m-%d").date()
	except ValueError:
		return timezone.localdate()


class AttendanceListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	model = Attendance
	template_name = "core/attendance_list.html"
	context_object_name = "attendances"
	paginate_by = 25

	def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
		self.attendance_date = _parse_date(request.GET.get("date"))
		return super().dispatch(request, *args, **kwargs)

	def _auto_create_expected_if_empty(self) -> None:
		if Attendance.objects.filter(attendance_date=self.attendance_date).exists():
			return
		active_children = Child.objects.filter(status=ChildStatus.ACTIVE)
		Attendance.objects.bulk_create(
			[
				Attendance(child=child, attendance_date=self.attendance_date, status=AttendanceStatus.EXPECTED)
				for child in active_children
			],
			ignore_conflicts=True,
		)

	def get_queryset(self) -> QuerySet[Attendance]:
		self._auto_create_expected_if_empty()

		qs: QuerySet[Attendance] = Attendance.objects.select_related(
			"child", "child__classroom"
		).filter(attendance_date=self.attendance_date)

		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(child_search_filter(q))

		classroom_id = (self.request.GET.get("classroom") or "").strip()
		if classroom_id:
			qs = qs.filter(child__classroom_id=classroom_id)

		status = (self.request.GET.get("status") or "").strip()
		if status:
			qs = qs.filter(status=status)

		return qs.order_by("child__last_name", "child__first_name")

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["page_title"] = "Davomat"
		ctx["date"] = self.attendance_date
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		ctx["classrooms"] = Classroom.objects.all().order_by("name")
		ctx["selected_classroom"] = (self.request.GET.get("classroom") or "").strip()
		ctx["selected_status"] = (self.request.GET.get("status") or "").strip()
		ctx["statuses"] = AttendanceStatus.choices

		base_qs = Attendance.objects.filter(attendance_date=self.attendance_date)
		ctx["count_present"] = base_qs.filter(status=AttendanceStatus.PRESENT).count()
		ctx["count_late"] = base_qs.filter(status=AttendanceStatus.LATE).count()
		ctx["count_absent"] = base_qs.filter(status=AttendanceStatus.ABSENT).count()
		ctx["count_not_marked"] = base_qs.filter(status=AttendanceStatus.EXPECTED).count()
		return ctx


class AttendanceUpdateView(LoginRequiredMixin, RoleRequiredMixin, PageTitleMixin, UpdateView):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	model = Attendance
	form_class = AttendanceForm
	template_name = "core/attendance_form.html"
	page_title = "Davomatni tahrirlash"

	def get_success_url(self) -> str:
		date_str = self.object.attendance_date.strftime("%Y-%m-%d")
		return f"{reverse_lazy('core:attendance_list')}?date={date_str}"

	def form_valid(self, form: AttendanceForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Davomat yangilandi.")
		return response


class AttendanceQuickMarkView(LoginRequiredMixin, RoleRequiredMixin, View):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	allowed = {
		AttendanceStatus.PRESENT,
		AttendanceStatus.ABSENT,
		AttendanceStatus.LATE,
		AttendanceStatus.HALF_DAY,
		AttendanceStatus.EXPECTED,
	}

	def post(self, request: HttpRequest, pk: int, status: str) -> HttpResponse:
		if status not in self.allowed:
			return HttpResponseBadRequest("Noto‘g‘ri holat")
		try:
			attendance = Attendance.objects.select_related("child").get(pk=pk)
		except Attendance.DoesNotExist:
			return HttpResponseBadRequest("Davomat topilmadi")

		attendance.status = status
		attendance.save(update_fields=["status", "updated_at"])
		messages.success(request, f"{attendance.child} holati: {attendance.get_status_display()}.")

		date_str = attendance.attendance_date.strftime("%Y-%m-%d")
		return_url = request.META.get("HTTP_REFERER") or f"{reverse_lazy('core:attendance_list')}?date={date_str}"
		return HttpResponseRedirect(return_url)


class AttendanceSetTimeView(LoginRequiredMixin, RoleRequiredMixin, View):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	def post(self, request: HttpRequest, pk: int, field: str) -> HttpResponse:
		if field not in {"check_in_time", "check_out_time"}:
			return HttpResponseBadRequest("Noto‘g‘ri maydon")
		value = (request.POST.get("time") or "").strip()
		if not value:
			return HttpResponseBadRequest("Vaqt kiritilmadi")
		try:
			time_value = datetime.strptime(value, "%H:%M").time()
		except ValueError:
			return HttpResponseBadRequest("Noto‘g‘ri vaqt")

		attendance = Attendance.objects.get(pk=pk)
		setattr(attendance, field, time_value)
		attendance.save(update_fields=[field, "updated_at"])
		messages.success(request, "Vaqt yangilandi.")
		date_str = attendance.attendance_date.strftime("%Y-%m-%d")
		return_url = request.META.get("HTTP_REFERER") or f"{reverse_lazy('core:attendance_list')}?date={date_str}"
		return HttpResponseRedirect(return_url)


class AttendanceBulkMarkPresentView(LoginRequiredMixin, RoleRequiredMixin, View):
	allowed_roles = (ROLE_ADMIN, ROLE_EDUCATOR)
	def post(self, request: HttpRequest) -> HttpResponse:
		date_val = _parse_date(request.POST.get("date"))
		classroom_id = (request.POST.get("classroom") or "").strip()
		if not classroom_id:
			return HttpResponseBadRequest("Guruh tanlanmadi")

		children = Child.objects.filter(status=ChildStatus.ACTIVE, classroom_id=classroom_id)
		if not children.exists():
			messages.info(request, "Tanlangan guruhda faol bolalar yo‘q.")
			return HttpResponseRedirect(
				f"{reverse_lazy('core:attendance_list')}?date={date_val.strftime('%Y-%m-%d')}&classroom={classroom_id}"
			)

		# Ensure records exist, then mark Present.
		Attendance.objects.bulk_create(
			[
				Attendance(child=child, attendance_date=date_val, status=AttendanceStatus.EXPECTED)
				for child in children
			],
			ignore_conflicts=True,
		)
		Attendance.objects.filter(attendance_date=date_val, child__in=children).update(
			status=AttendanceStatus.PRESENT
		)
		messages.success(request, "Tanlangan guruh 'Keldi' deb belgilandi.")
		return HttpResponseRedirect(
			f"{reverse_lazy('core:attendance_list')}?date={date_val.strftime('%Y-%m-%d')}&classroom={classroom_id}"
		)




def _parse_billing_month(value: str | None) -> str:
	if not value:
		return timezone.localdate().strftime("%Y-%m")
	val = value.strip()
	# Accept a date picker value (YYYY-MM-DD) and normalize to YYYY-MM.
	if len(val) == 10 and val[4] == "-" and val[7] == "-":
		val = val[:7]
	try:
		year = int(val[0:4])
		month = int(val[5:7])
	except Exception:
		return timezone.localdate().strftime("%Y-%m")
	if len(val) != 7 or val[4] != "-" or month < 1 or month > 12 or year < 1900:
		return timezone.localdate().strftime("%Y-%m")
	return val


class MonthlyBillingListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
	allowed_roles = (ROLE_ADMIN, ROLE_ACCOUNTANT)
	model = MonthlyBilling
	template_name = "core/billing_monthly_list.html"
	context_object_name = "rows"
	paginate_by = 25

	def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
		self.billing_month = _parse_billing_month(request.GET.get("month"))
		return super().dispatch(request, *args, **kwargs)

	def _auto_create_if_missing(self) -> None:
		active_children = Child.objects.filter(status=ChildStatus.ACTIVE).select_related("tariff")
		existing = set(
			MonthlyBilling.objects.filter(billing_month=self.billing_month).values_list("child_id", flat=True)
		)
		to_create: list[MonthlyBilling] = []
		for child in active_children:
			if child.pk in existing:
				continue
			amount = child.tariff.amount if child.tariff else Decimal("0")
			to_create.append(
				MonthlyBilling(
					child=child,
					billing_month=self.billing_month,
					amount=amount,
					status=MonthlyBillingStatus.UNPAID,
				)
			)
		if to_create:
			MonthlyBilling.objects.bulk_create(to_create, ignore_conflicts=True)

	def get_queryset(self) -> QuerySet[MonthlyBilling]:
		self._auto_create_if_missing()
		qs: QuerySet[MonthlyBilling] = MonthlyBilling.objects.select_related(
			"child", "child__classroom", "child__tariff"
		).filter(
			billing_month=self.billing_month
		)
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(child_search_filter(q))
		classroom_id = (self.request.GET.get("classroom") or "").strip()
		if classroom_id:
			qs = qs.filter(child__classroom_id=classroom_id)
		status = (self.request.GET.get("status") or "").strip()
		if status:
			qs = qs.filter(status=status)
		return qs.order_by("child__last_name", "child__first_name")

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["page_title"] = "Oylik to‘lov"
		ctx["month"] = self.billing_month
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		ctx["classrooms"] = Classroom.objects.all().order_by("name")
		ctx["selected_classroom"] = (self.request.GET.get("classroom") or "").strip()
		ctx["selected_status"] = (self.request.GET.get("status") or "").strip()
		ctx["statuses"] = MonthlyBillingStatus.choices

		base_qs = MonthlyBilling.objects.filter(billing_month=self.billing_month)
		ctx["count_paid"] = base_qs.filter(status=MonthlyBillingStatus.PAID).count()
		ctx["count_unpaid"] = base_qs.filter(status=MonthlyBillingStatus.UNPAID).count()
		return ctx


class MonthlyBillingMarkView(LoginRequiredMixin, RoleRequiredMixin, View):
	allowed_roles = (ROLE_ADMIN, ROLE_ACCOUNTANT)
	def post(self, request: HttpRequest, status: str) -> HttpResponse:
		if status not in {MonthlyBillingStatus.PAID, MonthlyBillingStatus.UNPAID}:
			return HttpResponseBadRequest("Noto‘g‘ri holat")
		child_id = (request.POST.get("child") or "").strip()
		month = _parse_billing_month(request.POST.get("month"))
		if not child_id:
			return HttpResponseBadRequest("Bola tanlanmadi")
		child = get_object_or_404(Child.objects.select_related("tariff"), pk=child_id)
		default_amount = child.tariff.amount if child.tariff else Decimal("0")
		row, _ = MonthlyBilling.objects.get_or_create(
			child_id=child_id,
			billing_month=month,
			defaults={"amount": default_amount, "status": MonthlyBillingStatus.UNPAID},
		)
		if status == MonthlyBillingStatus.PAID:
			row.mark_paid()
			messages.success(request, "To‘langan deb belgilandi.")
		else:
			row.mark_unpaid()
			messages.success(request, "To‘lanmagan deb belgilandi.")

		return_url = request.META.get("HTTP_REFERER") or f"{reverse('core:billing_monthly_list')}?month={month}"
		return HttpResponseRedirect(return_url)

# Create your views here.
