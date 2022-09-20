from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from .models import CartItem, Customer, Order, OrderItem, Product, Collection, Review, Cart


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']

    products_count = serializers.IntegerField(read_only=True)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory',
                  'unit_price', 'price_with_tax', 'collection']

    # Add field wich does not exist in Product model
    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date', 'name', 'description', 'product']

    def create(self, validated_data):
        product_id = self.context.get('product_id')
        return Review.objects.create(product_id=product_id, **validated_data)


# For Cart. Basic information about Product.
class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(
        method_name='get_total_price')

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):

    # read_only = True: We don't want to send this id value to the browser
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(
        method_name='get_total_price')

    def get_total_price(self, cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):

    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                'No product with the given ID was found.')
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        try:
            cart_item = CartItem.objects.get(
                cart_id=cart_id, product_id=product_id)
            # Update an existing item
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            # Create a new item
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)  # product_id and quantity

        return self.instance

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


# Building the Profile API
class CustomerSerializer(serializers.ModelSerializer):

    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']


class OrderItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'placed_at', 'payment_status', 'items']


class CreateOrderSerializer(serializers.Serializer):

    cart_id = serializers.UUIDField()

    # Users can't create an order with empty cart and with invalid cart_id
    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError(
                'No cart with given ID was found')
        elif CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValueError('The cart is empty')

        return cart_id

    def save(self, **kwargs):

        with transaction.atomic():

            cart_id = self.validated_data['cart_id']

            (customer, created) = Customer.objects.get_or_create(
                user_id=self.context['user_id'])

            # Create Oreder
            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects.select_related('product').filter(
                cart_id=cart_id)

            # Create OrderItems (Convert Each CartItems to OrderItems)
            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.unit_price,
                ) for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            # Deleting a cart because we created an order
            Cart.objects.filter(pk=cart_id).delete()

            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']

    # Then change def get_serializer_class() in OrderViewSets


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# USEFUL INFORMATION
'''
# We can rename model field
price = serializers.DecimalField(
    max_digits=6, decimal_places=2, source='unit_price')


# We can owerwrite validate method
def validate(self, data):
    if data['password'] != data['confirm_password']:
        return serializers.ValidationError('Passwords do not match')
    return data


# We can owerwrite create method (POST method)
def create(self, validated_data):
     # Create a product object
    product = Product(**validated_data)
    product.new_field = 1
    product.save()
    return product


# We can owerwrite update method (PUT/PATCH method)
def update(self, instance, validated_data):
    instance.unit_price = validated_data.get('unit_price') * 100
    instance.save()
    return instance
'''


# SERIALIZING RELATIONSHIPS
'''
1: By Primary Key. Default in ModelSerializer

collection = serializers.PrimaryKeyRelatedField(
    queryset=Collection.objects.all()
)

--------------------------------------------------------------

2. By String Representation. Title each collection

collection = serializers.StringRelatedField()

But should in views.py when we get quryset all products
and apply this ProductSerializer 

queryset = Product.objects.select_related('collection').all()

--------------------------------------------------------------

3: By Hyperlink.

(1) 

collection = serializers.HyperlinkedRelatedField(
    queryset=Collection.objects.all(),
    view_name='collection-detail'
)

(2) urls.py

path('collection/<int:pk>', views.collection, name=collection-detail)

'''
