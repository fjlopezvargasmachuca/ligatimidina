from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("decks", "0002_alter_deck_is_original")]
    operations = [
        migrations.AddField(
            model_name="deck", name="card_list",
            field=models.TextField(blank=True, help_text="Una carta por línea; admite prefijos de cantidad como 1 Sol Ring.", verbose_name="Listado de cartas"),
        ),
    ]
