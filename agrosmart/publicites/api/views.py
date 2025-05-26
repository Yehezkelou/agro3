from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from ..models import Advertisement, Category , Favorite
from .serializers import AdvertisementSerializer, CategorySerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class AdvertisementListAPI(generics.ListCreateAPIView):
    queryset = Advertisement.objects.filter(status='published').select_related('author', 'category')
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'publish']
    ordering = ['-publish']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class AdvertisementDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'

class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class UserAdvertisementsAPI(generics.ListAPIView):
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.filter(
            author=self.request.user
        ).select_related('category')

class FavoriteAdvertisementAPI(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Advertisement.objects.filter(
            favorited_by__user=self.request.user
        ).select_related('author', 'category')
    
    def post(self, request, *args, **kwargs):
        ad = get_object_or_404(Advertisement, pk=request.data.get('advertisement'))
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            advertisement=ad
        )
        if created:
            return Response({'status': 'added'}, status=201)
        return Response({'status': 'already_exists'}, status=200)
    
    def delete(self, request, *args, **kwargs):
        ad = get_object_or_404(Advertisement, pk=kwargs.get('pk'))
        Favorite.objects.filter(
            user=request.user,
            advertisement=ad
        ).delete()
        return Response({'status': 'removed'}, status=204)