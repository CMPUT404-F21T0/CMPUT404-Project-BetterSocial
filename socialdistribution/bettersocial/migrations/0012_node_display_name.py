# Generated by Django 3.2.8 on 2021-12-06 03:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bettersocial', '0011_auto_20211205_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name = 'node',
            name = 'display_name',
            field = models.CharField(blank = True, max_length = 127, default = 'A Server'),
        ),
        migrations.AlterField(
            model_name = 'follower',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
        migrations.AlterField(
            model_name = 'following',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
        migrations.AlterField(
            model_name = 'inboxitem',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
        migrations.AlterField(
            model_name = 'like',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
        migrations.AlterField(
            model_name = 'likedremote',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
        migrations.AlterField(
            model_name = 'node',
            name = 'id',
            field = models.BigAutoField(auto_created = True, primary_key = True, serialize = False, verbose_name = 'ID'),
        ),
    ]
