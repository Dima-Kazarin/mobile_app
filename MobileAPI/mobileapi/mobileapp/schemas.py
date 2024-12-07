from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .serializers import UserProductSerializer, PurchaseSerializer, RecommendationSerializer, UnitSerializer, ReminderSerializer

user_product_docs = extend_schema(
    responses=UserProductSerializer,
    parameters=[
        OpenApiParameter(
            name='by_user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='filter products by user id'
        )
    ], tags=['UserProduct']
)

purchase_docs = extend_schema(
    responses=PurchaseSerializer,
    parameters=[
        OpenApiParameter(
            name='by_user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='filter purchases by user id'
        )
    ], tags=['Purchase']
)

recommendation_docs = extend_schema(
    responses=RecommendationSerializer,
    parameters=[
        OpenApiParameter(
            name='by_user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='filter recommendation by user id'
        )
    ], tags=['Recommendation']
)

unit_docs = extend_schema(
    responses=UnitSerializer,
    parameters=[
        OpenApiParameter(
            name='by_unit_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='filter units by id'
        )
    ], tags=['Unit']
)

reminder_docs = extend_schema(
    responses=ReminderSerializer,
    parameters=[
        OpenApiParameter(
            name='by_user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='filter reminders by user id'
        )
    ], tags=['Reminder']
)