from rest_framework.views import APIView

from db.models import Plan
from shared.utils import CustomResponse


class SubPlans(APIView):
    def post(self, request):

        print("Creating plan")

        data = request.data

        name = data.get("name")
        code = data.get("code")
        price = data.get("price")
        billing_interval = data.get("billing_interval")
        billing_interval_count = data.get(
            "billing_interval_count",
            1
        )
        description = data.get("description")
        is_recommended = data.get(
            "is_recommended",
            False
        )
        razorpay_plan_id = data.get("razorpay_plan_id")

        # Validation
        if not name:
            return CustomResponse.errorResponse(
                description="Plan name is required"
            )

        if not code:
            return CustomResponse.errorResponse(
                description="Plan code is required"
            )

        if not price:
            return CustomResponse.errorResponse(
                description="Plan price is required"
            )

        if billing_interval not in ["month", "year"]:
            return CustomResponse.errorResponse(
                description="Invalid billing interval"
            )

        if not razorpay_plan_id:
            return CustomResponse.errorResponse(
                description="Razorpay plan ID is required"
            )

        # Check duplicate code
        if Plan.objects.filter(
                code=code
        ).exists():
            return CustomResponse.errorResponse(
                description="Plan code already exists"
            )

        # Check duplicate Razorpay plan
        if Plan.objects.filter(
                razorpay_plan_id=razorpay_plan_id
        ).exists():
            return CustomResponse.errorResponse(
                description="Razorpay plan ID already exists"
            )

        # Only one recommended plan
        if is_recommended:
            Plan.objects.filter(
                is_recommended=True
            ).update(
                is_recommended=False
            )

        plan = Plan.objects.create(
            name=name,
            code=code,
            price=price,
            billing_interval=billing_interval,
            billing_interval_count=billing_interval_count,
            description=description,
            is_recommended=is_recommended,
            is_active=True,
            razorpay_plan_id=razorpay_plan_id
        )

        return CustomResponse.successResponse(
            data={
                "id": str(plan.id),
                "name": plan.name,
                "code": plan.code,
                "price": str(plan.price),
                "billing_interval": plan.billing_interval,
                "billing_interval_count": plan.billing_interval_count,
                "description": plan.description,
                "is_recommended": plan.is_recommended,
                "is_active": plan.is_active,
                "razorpay_plan_id": plan.razorpay_plan_id
            },
            description="Plan created successfully"
        )

    def get(self, request):
        print("Fetching all plans")
        plans = Plan.objects.all().order_by("-created_at")
        data = []
        for plan in plans:
            data.append({
                "id": str(plan.id),
                "name": plan.name,
                "code": plan.code,
                "price": str(plan.price),
                "billing_interval": plan.billing_interval,
                "billing_interval_count": plan.billing_interval_count,
                "description": plan.description,
                "is_recommended": plan.is_recommended,
                "is_active": plan.is_active,
                "razorpay_plan_id": plan.razorpay_plan_id,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at
            })
        return CustomResponse.successResponse(
            data=data,
            description="Plans fetched successfully"
        )

    def put(self, request, plan_id):

        print("Updating plan")

        plan = Plan.objects.filter(
            id=plan_id
        ).first()

        if not plan:
            return CustomResponse.errorResponse(
                description="Plan not found"
            )

        data = request.data

        name = data.get("name")
        price = data.get("price")
        billing_interval = data.get("billing_interval")
        billing_interval_count = data.get(
            "billing_interval_count"
        )
        description = data.get("description")
        is_recommended = data.get(
            "is_recommended"
        )
        is_active = data.get(
            "is_active"
        )

        if name is not None:
            plan.name = name

        if price is not None:
            plan.price = price

        if billing_interval is not None:

            if billing_interval not in [
                "month",
                "year"
            ]:
                return CustomResponse.errorResponse(
                    description="Invalid billing interval"
                )

            plan.billing_interval = billing_interval

        if billing_interval_count is not None:
            plan.billing_interval_count = billing_interval_count

        if description is not None:
            plan.description = description

        if is_active is not None:
            plan.is_active = is_active

        if is_recommended is True:

            Plan.objects.filter(
                is_recommended=True
            ).exclude(
                id=plan.id
            ).update(
                is_recommended=False
            )

            plan.is_recommended = True

        elif is_recommended is False:

            plan.is_recommended = False

        plan.save()

        return CustomResponse.successResponse(
            data={
                "id": str(plan.id),
                "name": plan.name,
                "code": plan.code,
                "price": str(plan.price),
                "billing_interval": plan.billing_interval,
                "billing_interval_count": plan.billing_interval_count,
                "description": plan.description,
                "is_recommended": plan.is_recommended,
                "is_active": plan.is_active
            },
            description="Plan updated successfully"
        )

    def delete(self, request, plan_id):
        print("Deactivating plan")
        plan = Plan.objects.filter(
            id=plan_id
        ).first()
        if not plan:
            return CustomResponse.errorResponse(
                description="Plan not found"
            )
        # Soft delete
        plan.is_active = False
        plan.is_recommended = False
        plan.save(
            update_fields=[
                "is_active",
                "is_recommended"
            ]
        )
        return CustomResponse.successResponse(
            data={
                "id": str(plan.id)
            },
            description="Plan deactivated successfully"
        )



