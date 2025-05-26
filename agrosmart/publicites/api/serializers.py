from rest_framework import serializers
from ..models import Advertisement, Category, AdvertisementImage
from user.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class AdvertisementImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvertisementImage
        fields = ['id', 'image', 'caption', 'is_main']

class AdvertisementSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer()
    images = AdvertisementImageSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Advertisement
        fields = [
            'id', 'title', 'slug', 'description', 'price', 
            'category', 'author', 'publish', 'updated', 
            'status', 'is_premium', 'images', 'is_favorite'
        ]
        read_only_fields = ['slug', 'publish', 'updated']
    
    def get_is_favorite(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False
    
    def create(self, validated_data):
        category_data = validated_data.pop('category')
        category = Category.objects.get(id=category_data['id'])
        advertisement = Advertisement.objects.create(
            category=category,
            author=self.context['request'].user,
            **validated_data
        )
        return advertisement