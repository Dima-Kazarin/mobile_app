from deep_translator import GoogleTranslator

from django.contrib.auth import authenticate, login, logout
from .models import User
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from word2number import w2n
import speech_recognition as sr
from django.db.models import F
from itertools import combinations
from datetime import timedelta
from django.utils.timezone import now, is_aware, make_aware

from .models import Product, Purchase, Recommendation, UserProduct, Unit, Reminder, PurchaseCounter
from .serializers import (ProductSerializer, UserProductSerializer, PurchaseSerializer, RecommendationSerializer,
                          RegisterSerializer, UnitSerializer, LoginSerializer, ReminderSerializer, PurchaseCounterSerializer)
from .schemas import user_product_docs, purchase_docs, unit_docs, reminder_docs
from .tasks import daily_reminder_task


class PurchaseCounterView(viewsets.ViewSet):
    @extend_schema(responses=PurchaseCounterSerializer, tags=['Purchase'])
    def list(self, request):
        query_set = PurchaseCounter.objects.all()
        serializer = PurchaseCounterSerializer(query_set, many=True)
        return Response(serializer.data)


class UnitView(viewsets.ViewSet):
    @unit_docs
    def list(self, request):
        query_set = Unit.objects.all()

        by_unit_id = request.query_params.get('by_unit_id')

        if by_unit_id:
            query_set = query_set.filter(id=by_unit_id)

        serializer = UnitSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=UnitSerializer, tags=['Unit'])
    def create(self, request):
        serializer = UnitSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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
        serializer1 = UserProductSerializer(data=request.data)

        if serializer.is_valid() and serializer1.is_valid():
            self.process_purchase(request.user)

            purchase = serializer.save()

            user_product = serializer1.save()

            return Response({"status": "success", "message": "Purchase created successfully."}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def process_purchase(self, user):
        current_time = now()

        recent_purchases = Purchase.objects.filter(user=user, purchase_date__gte=current_time - timedelta(minutes=30))

        last_purchase = Purchase.objects.filter(user=user).order_by('-purchase_date').first()

        if last_purchase:
            last_purchase_date = last_purchase.purchase_date
            if not is_aware(last_purchase_date):
                last_purchase_date = make_aware(last_purchase_date)

            if (current_time - last_purchase_date).total_seconds() > 30 * 60:
                purchase_counter, created = PurchaseCounter.objects.get_or_create(id=1, defaults={'total_purchases': 0})
                purchase_counter.total_purchases += 1
                purchase_counter.save()

        recent_product_ids = [purchase.product.id for purchase in recent_purchases]

        pairs = self.group_product_pairs(recent_product_ids)

        for id_product1, id_product2 in pairs:
            if id_product1 == id_product2:
                continue

            recommendation, created = Recommendation.objects.get_or_create(
                product1=Product.objects.get(id=id_product1),
                product2=Product.objects.get(id=id_product2),
            )

            if created:
                recommendation.quantity = 1
            else:
                recommendation.quantity = F('quantity') + 1

            recommendation.save()

        purchase_counter = PurchaseCounter.objects.get(id=1)
        recommendations = Recommendation.objects.all()

        for rec in recommendations:
            rec.probability = rec.quantity / purchase_counter.total_purchases
            rec.save()

    def group_product_pairs(self, product_ids):
        return [(min(a, b), max(a, b)) for a, b in combinations(product_ids, 2)]


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
    def update(self, request, pk=None):
        obj = get_object_or_404(UserProduct, pk=pk)
        serializer = UserProductSerializer(obj, data=request.data)

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


@extend_schema(request=LoginSerializer, tags=['Auth'])
@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            response = Response({'success': 'Login success'}, status=status.HTTP_200_OK)
            response.set_cookie('user_id', request.user.id)
            return response

        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, tags=['Auth'])
@api_view(['POST'])
def logout_view(request):
    logout(request)
    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('user_id')
    return response


class VoiceInputView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        audio_file = request.FILES['audio']

        recognizer = sr.Recognizer()
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        with sr.AudioFile(audio_file) as source:
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio, language="uk")
            translated = GoogleTranslator(source='uk', target='en').translate(text)

            response = self.process_purchase_request(translated, request.user)

            return Response(response, status=status.HTTP_200_OK)

        except sr.UnknownValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except sr.RequestError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def process_purchase_request(self, text, user):
        products_queryset = Product.objects.all()
        products = {product.name: product.id for product in products_queryset}

        names_product = list(products.keys())

        data = []
        words = text.split()

        for word in words:
            try:
                number = w2n.word_to_num(word)
                data.append(number)
            except ValueError:
                if word in names_product:
                    data.append(word)

        if len(data) > 1:
            value_to_find = data[1]
            found_key = next((key for key, value in products.items() if key == value_to_find), None)

            if found_key:
                self.process_p(user)

                product = Product.objects.get(name=found_key)
                purchase = Purchase.objects.create(
                    user=User.objects.get(id=user.id),
                    product=product,
                    quantity=data[0]
                )
                userproduct = UserProduct.objects.create(
                    user=User.objects.get(id=user.id),
                    product=product,
                    quantity=data[0]
                )
                return {"status": "success", "message": "Purchase created successfully."}
            else:
                return {"status": "error", "message": "Product not found."}

        if 'my' in words and 'products' in words:
            my_index = words.index("my")
            products_index = words.index("products")
            if abs(my_index - products_index) == 1:
                return self.get_user_product_list(user.id)

        if "my" in words and "reminders" in words:
            my_index = words.index("my")
            reminders_index = words.index("reminders")
            if abs(my_index - reminders_index) == 1:
                return self.get_user_reminders(user.id)


    def get_user_reminders(self, user_id):
        reminders = Reminder.objects.filter(user_id=user_id).select_related('product', 'product__unit')

        if reminders.exists():
            user_reminder_list = [
                {
                "id": reminder.id,
                "name": reminder.product.name,
                "unit": reminder.product.unit.name,
                "created_at": reminder.created_at,
                }
                for reminder in reminders
            ]
        else:
            return {"status": "info", "message": f"User {user_id} has no reminders."}

        return {'reminders': user_reminder_list}


    def get_user_product_list(self, user_id):
        user_products = UserProduct.objects.filter(user_id=user_id).select_related('product')

        if not user_products.exists():
            return {"status": "info", "message": f"User {user_id} has no products."}

        user_product_list = [
            {
                "id": user_product.id,
                "name": user_product.product.name,
                "unit": user_product.product.unit.name,
                "quantity": user_product.quantity
            }
            for user_product in user_products
        ]

        return {"products": user_product_list}

    def process_p(self, user):
        current_time = now()

        recent_purchases = Purchase.objects.filter(user=user, purchase_date__gte=current_time - timedelta(minutes=30))

        last_purchase = Purchase.objects.filter(user=user).order_by('-purchase_date').first()

        if last_purchase:
            last_purchase_date = last_purchase.purchase_date
            if not is_aware(last_purchase_date):
                last_purchase_date = make_aware(last_purchase_date)

            if (current_time - last_purchase_date).total_seconds() > 30 * 60:
                purchase_counter, created = PurchaseCounter.objects.get_or_create(id=1, defaults={'total_purchases': 0})
                purchase_counter.total_purchases += 1
                purchase_counter.save()

        recent_product_ids = [purchase.product.id for purchase in recent_purchases]

        pairs = self.group_product_pairs(recent_product_ids)

        for id_product1, id_product2 in pairs:
            if id_product1 == id_product2:
                continue

            recommendation, created = Recommendation.objects.get_or_create(
                product1=Product.objects.get(id=id_product1),
                product2=Product.objects.get(id=id_product2),
            )

            if created:
                recommendation.quantity = 1
            else:
                recommendation.quantity = F('quantity') + 1

            recommendation.save()

        purchase_counter = PurchaseCounter.objects.get(id=1)
        recommendations = Recommendation.objects.all()

        for rec in recommendations:
            rec.probability = rec.quantity / purchase_counter.total_purchases
            rec.save()

    def group_product_pairs(self, product_ids):
        return [(min(a, b), max(a, b)) for a, b in combinations(product_ids, 2)]


class ReminderView(viewsets.ViewSet):
    @reminder_docs
    def list(self, request):
        query_set = Reminder.objects.all()
        by_user_id = request.query_params.get('by_user_id')

        if by_user_id:
            query_set = query_set.filter(user=by_user_id)

        serializer = ReminderSerializer(query_set, many=True)
        return Response(serializer.data)

    @extend_schema(request=ReminderSerializer, tags=['Reminder'])
    def create(self, request):
        serializer = ReminderSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


daily_reminder_task(repeat=86400)
