# Generated by Django 5.2.1 on 2025-05-25 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Advertisement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('slug', models.SlugField(unique_for_date='publish', verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix')),
                ('publish', models.DateTimeField(auto_now_add=True, verbose_name='Date de publication')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
                ('status', models.CharField(choices=[('draft', 'Brouillon'), ('published', 'Publié'), ('archived', 'Archivé')], default='draft', max_length=10, verbose_name='Statut')),
                ('is_premium', models.BooleanField(default=False, verbose_name='Annonce premium')),
            ],
            options={
                'verbose_name': 'Annonce',
                'verbose_name_plural': 'Annonces',
                'ordering': ('-publish',),
            },
        ),
        migrations.CreateModel(
            name='AdvertisementImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='publicites/images/', verbose_name='Image')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='Légende')),
                ('is_main', models.BooleanField(default=False, verbose_name='Image principale')),
            ],
            options={
                'verbose_name': "Image d'annonce",
                'verbose_name_plural': "Images d'annonce",
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Catégorie',
                'verbose_name_plural': 'Catégories',
            },
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")),
            ],
            options={
                'verbose_name': 'Favori',
                'verbose_name_plural': 'Favoris',
            },
        ),
    ]
