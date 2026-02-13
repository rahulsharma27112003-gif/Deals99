# Migration: change Payment.order from OneToOneField -> ForeignKey (payments)
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_add_stocktransaction_paymentaudit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='payments', to='api.order'),
        ),
    ]
