# Generated by Django 4.1.5 on 2023-02-13 19:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0002_alter_category_options_alter_productimages_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreview",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="product.product",
            ),
        ),
    ]
