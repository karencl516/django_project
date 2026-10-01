from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from djoser.serializers import UserSerializer
from .models import MenuItem,Category,Cart,Order,OrderItem
from .serializers import CategorySerializer,MenuItemSerializer,CartSerializer, OrderItemsSerializer,OrderSerializer
from .permissions import IsManager, is_manager, is_delivery_crew


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if(self.request.method=='GET'):
            return [AllowAny()]

        return [(IsAdminUser| IsManager)()]

class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['title','category__title']
    ordering_fields = ['price','category']

    def get_permissions(self):
        if(self.request.method=='GET'):
            return [AllowAny()]
        
        return [(IsAdminUser| IsManager)()]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if(self.request.method=='GET'):
            return [AllowAny()]

        return [(IsAdminUser| IsManager)()]

class GroupViewSet(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager ]

    def get_queryset(self):
        group_name = self.kwargs['group_name']
        return User.objects.filter(groups__name=group_name)

    def post(self, request, *args, **kwargs):
        group_name = self.kwargs ['group_name']
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            group = get_object_or_404(Group, name=group_name)

            if group in user.groups.all():
                return Response(
                    {'message': f'User is already in group: {group_name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            group.user_set.add(user)
            return Response({'message': f' user added to group:{group_name} '}, status=status.HTTP_201_CREATED)

        return Response({'message': f'Error resquest for group:{group_name} '}, status=status.HTTP_400_BAD_REQUEST)

class GroupUserDeleteView(generics.DestroyAPIView):

    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager ]

    def delete(self, request, *args, **kwargs):
        group_name = self.kwargs['group_name']
        user_id = self.kwargs['pk']

        user = get_object_or_404(User,id=user_id)
        group = get_object_or_404(Group,name=group_name)

        if group in user.groups.all():
            group.user_set.remove(user)
            return Response({'message': 'User removed from the group'}, status=status.HTTP_200_OK)

        return Response({'message': 'User is not a member of this group'}, status=status.HTTP_404_NOT_FOUND)

class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=self.request.user).delete()
        return Response(
            {"message": "All items in the cart have been removed."},
            status=status.HTTP_200_OK
        )   

class CartMenuItemDeleteView(generics.RetrieveDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'menuitem'

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return Response(
            {"message": "The item in the cart have been removed."},
            status=status.HTTP_200_OK
        )   

class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes =[IsAuthenticated]
    search_fields = ['menuitem']
    ordering_fields = ['date','price']

    def get_queryset(self):
        user = self.request.user

        if is_manager(user):
            return Order.objects.all()

        if is_delivery_crew(user):
            return Order.objects.filter(delivery_crew=user)

        return Order.objects.filter(user=user)

    def create(self, request, *args, **kwargs):

        if is_manager(request.user) or is_delivery_crew(request.user):
            return Response(
                {'message':'Managers and delivery crew members cannot place a order'}, 
                status=status.HTTP_403_FORBIDDEN
                ) 

        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response(
            {"message": "Your cart is empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

        with transaction.atomic():
            total = sum(item.price for item in cart_items)

            order = Order.objects.create(
                user=request.user,
                total=total
            )

            order_items = [
                OrderItem(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
                for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            cart_items.delete()

        serializer = self.get_serializer(order)
        return Response(
            {
                "message": "Order created successfully.",
                "order": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes =[IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if is_manager(user):
            return Order.objects.all()

        if is_delivery_crew(user):
            return Order.objects.filter(delivery_crew=user)

        return Order.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        user = request.user

        if is_manager(user):
            allowed_fields = {'status', 'delivery_crew'}
        elif is_delivery_crew(user):
            if request.method == 'PUT':
                return Response(
                    {'message': 'Delivery crew can only use PATCH to update status.'},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                )
            allowed_fields = {'status'}
        else:
            return Response(
                {'message': 'You are not allowed to update this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        extra_fields = set(request.data.keys()) - allowed_fields
        if extra_fields:
            return Response(
                {'message': f'You are not allowed to update: {", ".join(extra_fields)}'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return Response(
                {'message': 'You are not allowed to delete this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


