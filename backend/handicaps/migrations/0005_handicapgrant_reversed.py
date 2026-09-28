from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("handicaps", "0004_alter_handicapgrant_definition")]

    operations = [
        migrations.AddField(
            model_name="handicapgrant",
            name="reversed",
            field=models.BooleanField(default=False, verbose_name="Lanzamiento revertido"),
        ),
    ]
