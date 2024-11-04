from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Product, Purchase, Recommendation, UserProduct
from .serializers import (ProductSerializer, UserProductSerializer, PurchaseSerializer, RecommendationSerializer,
                          RegisterSerializer)
from .schemas import user_product_docs, purchase_docs


class ProductView(viewsets.ViewSet):
    @extend_schema(responses=ProductSerializer, tags=['Product'])
    def list(self, request):
        query_set = Product.objects.all()
        serializer = ProductSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=ProductSerializer, tags=['Product'])
    def create(self, request):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class PurchaseView(viewsets.ViewSet):
    @purchase_docs
    def list(self, request):
        query_set = Purchase.objects.all()
        by_user_id = request.query_params.get('by_user_id')

        if by_user_id:
            query_set = query_set.filter(user=by_user_id)

        serializer = PurchaseSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=PurchaseSerializer, tags=['Purchase'])
    def create(self, request):
        serializer = PurchaseSerializer(data=request.data)
        serializer_user_product = UserProductSerializer(data=request.data)

        if serializer.is_valid() and serializer_user_product.is_valid():
            serializer.save()
            serializer_user_product.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProductView(viewsets.ViewSet):
    @user_product_docs
    def list(self, request):
        query_set = UserProduct.objects.all()
        by_user_id = request.query_params.get('by_user_id')

        if by_user_id:
            query_set = query_set.filter(user=by_user_id)

        serializer = UserProductSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=UserProductSerializer, tags=['UserProduct'])
    def create(self, request):
        serializer = UserProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=UserProductSerializer, tags=['UserProduct'])
    def destroy(self, request, pk=None):
        obj = get_object_or_404(UserProduct, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_200_OK)


class RecommendationView(viewsets.ViewSet):
    @extend_schema(responses=RecommendationSerializer, tags=['Recommendation'])
    def list(self, request):
        query_set = Recommendation.objects.all()
        serializer = RecommendationSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=RecommendationSerializer, tags=['Recommendation'])
    def create(self, request):
        serializer = RecommendationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=RegisterSerializer, tags=['Auth'])
@api_view(['POST'])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string'},
            },
            'required': ['username', 'password'],
        }
    },
    tags=['Auth']
)
@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)

        request.session['username'] = username

        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, tags=['Auth'])
@api_view(['POST'])
def logout_view(request):
    logout(request)

    Session.objects.filter(session_key=request.session.session_key).delete()

    return Response(status=status.HTTP_200_OK)
