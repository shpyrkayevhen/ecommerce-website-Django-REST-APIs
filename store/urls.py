# ~$ pip install drf-nested-routers
from rest_framework_nested import routers
from . import views


# Create router and Register endpoins(URLConf) for our ViewSets
router = routers.DefaultRouter()

# basename for generating URLpatterns: products-list, products-detail
# use it when we overwriting the queryset in specific ViewSet
router.register('products', views.ProductViewSet, basename='products')
router.register('collections', views.CollectionViewSet)
router.register('carts', views.CartViewSet, basename='carts')
router.register('customers', views.CustomerViewSet)
router.register('orders', views.OrderViewSet, basename='orders')

products_router = routers.NestedDefaultRouter(
    router, 'products', lookup='product')  # product_pk
products_router.register('reviews', views.ReviewViewSet,
                         basename='product-reviews')


carts_router = routers.NestedDefaultRouter(
    router, 'carts', lookup='cart')  # cart_pk
carts_router.register('items', views.CartItemViewSet, basename='cart-items')

# URLConf
urlpatterns = router.urls + products_router.urls + carts_router.urls

# If we have another path we can include to them our routers
# urlpatterns = ['', include(router.urls),
#                '', include(products_router)]


# URLConf For GenericAPIView & Class-based Views
'''
urlpatterns = [
    path('products/', views.ProductList.as_view(), name='products'),
    path('products/<int:pk>', views.ProductDetail.as_view(), name='products'),
]
'''


# URLConf For Function-based Views
'''
urlpatterns = [
    path('products/', views.product_list, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product'),
    path('collections/', views.collection_list, name='collections'),
    path('collections/<int:pk>/', views.collection_detail, name='collection'),
]
'''
