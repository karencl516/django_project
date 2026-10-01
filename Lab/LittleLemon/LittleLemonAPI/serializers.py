from rest_framework import serializers
from .models import MenuItem,Category, Cart, Order,OrderItem
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User

class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer (serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=6,decimal_places=2, min_value=0.01)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset = Category.objects.all(),
        source='category',
        write_only=True
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'title','price','featured','category','category_id']        

class CartSerializer (serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = Cart
        fields = ['id','user','menuitem','menuitem_id','quantity','unit_price','price']
        read_only_fields = ['id', 'user', 'unit_price', 'price']

    def validate(self,attrs):
        user = self.context['request'].user
        menuitem_id = attrs['menuitem_id']

        try:
            menuitem = MenuItem.objects.get(pk=attrs['menuitem_id'])
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError({"menuitem_id" : ' this item does not exist'})

        if Cart.objects.filter(user = user ,menuitem_id=menuitem_id).exists():
            raise serializers.ValidationError({"menuitem_id" :' this item is already in your cart'})

        attrs['unit_price']= menuitem.price
        attrs['price']= attrs['quantity']* menuitem.price
        return attrs

class OrderItemsSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['id','order','menuitem','quantity','unit_price','price']
        read_only_fields = ['id', 'user','order','quantity','unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemsSerializer(read_only=True,many=True)

    class Meta:
        model = Order
        fields = ['id','user','delivery_crew','status','total','date','order_items']
        read_only_fields = ['user', 'total', 'date', 'order_items']

    def validate_delivery_crew(self, value):
        if value and not value.groups.filter(name='Delivery crew').exists():
            raise serializers.ValidationError("The assigned user does not belong to the Delivery crew.")
        return value


