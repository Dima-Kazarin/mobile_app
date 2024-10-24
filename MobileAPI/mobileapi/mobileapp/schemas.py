from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .serializers import UserProductSerializer, PurchaseSerializer

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