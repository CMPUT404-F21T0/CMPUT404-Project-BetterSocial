# Generated by Django 3.2.8 on 2021-10-27 04:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bettersocial', '0002_uuid_foreign_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='description',
        ),
    ]