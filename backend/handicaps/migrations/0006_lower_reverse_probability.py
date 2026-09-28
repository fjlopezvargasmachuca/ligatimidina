from decimal import Decimal
from django.db import migrations, models


def normalize_reverse_probabilities(apps, schema_editor):
    Definition = apps.get_model("handicaps", "HandicapDefinition")
    # Solo migramos configuraciones que conservan exactamente los valores
    # por defecto antiguos. Las probabilidades personalizadas por el admin
    # se respetan.
    Definition.objects.filter(
        reversal_base_percent=Decimal("50.00"),
        reversal_rank_step_percent=Decimal("5.00"),
        reversal_min_percent=Decimal("5.00"),
        reversal_max_percent=Decimal("95.00"),
    ).update(
        reversal_base_percent=Decimal("8.00"),
        reversal_rank_step_percent=Decimal("0.50"),
        reversal_min_percent=Decimal("2.00"),
        reversal_max_percent=Decimal("12.00"),
    )


class Migration(migrations.Migration):
    dependencies = [("handicaps", "0005_handicapgrant_reversed")]
    operations = [
        migrations.AlterField(model_name="handicapdefinition", name="reversal_base_percent", field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name="Probabilidad base de reversión (%)")),
        migrations.AlterField(model_name="handicapdefinition", name="reversal_rank_step_percent", field=models.DecimalField(decimal_places=2, default=0.5, max_digits=5, verbose_name="Ajuste por puesto (%)")),
        migrations.AlterField(model_name="handicapdefinition", name="reversal_min_percent", field=models.DecimalField(decimal_places=2, default=2, max_digits=5, verbose_name="Probabilidad mínima de reversión (%)")),
        migrations.AlterField(model_name="handicapdefinition", name="reversal_max_percent", field=models.DecimalField(decimal_places=2, default=12, max_digits=5, verbose_name="Probabilidad máxima de reversión (%)")),
        migrations.RunPython(normalize_reverse_probabilities, migrations.RunPython.noop),
    ]
