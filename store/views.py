from .serializer import CartItemSerializer, ProductSerializer, CollectionSerializer, ReviewSerializer, CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer, CustomerSerializer, OrderSerializer, CreateOrderSerializer, UpdateOrderSerializer
from .models import Collection, Customer, Product, OrderItem, Review, Cart, CartItem, Order
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, DjangoModelPermissions
from core.permissions import IsAdminOrReadOnly, ViewCustomerHistoryPermission

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .pagination import DefaultPagination
from .filters import ProductFilter


from rest_framework.response import Response
from django.db.models import Count
from rest_framework import status

from store import serializer


# --- ModelViewSet ---

class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    # FILTERING & SEARCHING & SORTING
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['collection_id', 'unit_price']
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'collection__title']
    ordering_fields = ['-unit_price', 'last_update']

    def destroy(self, request, *args, **kwargs):
        if OrderItem.products.filter(id=kwargs['pk']) > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']) > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):  # Register as Nested Router
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs.get('product_pk'))

    # Read product_pk from URL parametr and using context object paste to serializer
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  GenericViewSet):

    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):  # Register as Nested Router

    # exclude PUT method from ViewSet
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    # Pass this data to serializer
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    # We want get CartItem only certain Cart
    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs.get('cart_pk')).select_related('product')


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    # Add new endpoint/action for getting current_user: store/customers/me
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):

        # request.user.id: data from JSON payload if user is logged
        (customer, created) = Customer.objects.get_or_create(
            user_id=request.user.id)

        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    # Applying Custom Model Permissions. Add additional endpoint  store/customers/1/history
    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response("Ok")


class OrderViewSet(ModelViewSet):

    # exclude PUT method from ViewSet
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    # When we create an order we put cart_id into
    # CreateOrderSerializer but Response OrderSerializer
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)

        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer

        return OrderSerializer

    def get_serializer_context(self):

        return {'user_id': self.request.user.id}

    def get_queryset(self):

        user = self.request.user

        # Admin can see all orders
        if user.is_staff:
            return Order.objects.all()

        # User will see only his orders
        (customer_id, created) = Customer.objects.only('id').get_or_create(
            customer_id=user.id)
        return Order.objects.filter(customer_id=customer_id)


# --- GenericAPIViews ---
'''
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

class ProductList(ListCreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    # If we need some logic for getting queryset or serializer
    # For example depending from user pernissions
    def get_queryset(self):
        if not user.is_authentificated:
            return Product.objects.filter(...)
        return Product.objects.all()


class ProductDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def destroy(self, request, *args, **kwargs):
        if self.product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return self.product.delete()
'''


# --- Class-based API Views ---
'''
class ProductList(APIView):

from rest_framework.views import APIView

    def get(self, request):
        queryset = Product.objects.all()
        serializer = ProductSerializer(
            queryset, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetail(APIView):

    def get(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
'''


# --- Function-based API Views --- #
'''

from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])
def product_list(request):

    if request.method == 'GET':
        queryset = Product.objects.all()
        serializer = ProductSerializer(
            queryset, many=True)

        return Response(serializer.data)

    elif request.method == 'POST':
        # Desirializing Objects. Data which we get from user (body request)
        serializer = ProductSerializer(data=request.data)
        # We can overwrite the validate & create method in serializer
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def product_detail(request, pk):

    product = get_object_or_404(Product, id=pk)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        # We can overwrite the validate & update method in serializer
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    elif request.method == 'DELETE':
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def collection_list(request):

    if request.method == 'GET':
        queryset = Collection.objects.annotate(
            products_count=Count('products')).all()
        serializer = CollectionSerializer(
            queryset, many=True)

        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CollectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def collection_detail(request, pk):

    collection = get_object_or_404(Collection.objects.annotate(
        products_count=Count('products')), id=pk)

    if request.method == 'GET':
        serializer = CollectionSerializer(collection)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CollectionSerializer(collection, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    elif request.method == 'DELETE':
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
'''
