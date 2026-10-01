from django.urls import path 
from . import views 
  
urlpatterns = [ 
    path('categories/', views.CategoryView.as_view()),

    path('menu-items/', views.MenuItemView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>/', views.SingleMenuItemView.as_view()),

    path('groups/manager/users/', views.GroupViewSet.as_view(),{'group_name': 'Manager'}),
    path('groups/manager/users/<int:pk>/', views.GroupUserDeleteView.as_view(),{'group_name': 'Manager'}),
    path('groups/delivery-crew/users/', views.GroupViewSet.as_view(),{'group_name': 'Delivery crew'}),
    path('groups/delivery-crew/users/<int:pk>/', views.GroupUserDeleteView.as_view(),{'group_name': 'Delivery crew'}),

    path('cart/menu-items/', views.CartView.as_view(), name= 'cart-menu-items'),
    path('cart/menu-items/<int:menuitem>/', views.CartMenuItemDeleteView.as_view(), name= 'cart-menu-items-delete'),

    path('orders/', views.OrderView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', views.SingleOrderView.as_view(), name='order-detail'),

] 