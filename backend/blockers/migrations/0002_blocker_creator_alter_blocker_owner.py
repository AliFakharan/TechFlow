# Generated manually — make owner optional and add creator.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blockers", "0001_initial"),
        ("teams", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blocker",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="blockers",
                to="teams.member",
                verbose_name="صاحب مانع",
            ),
        ),
        migrations.AddField(
            model_name="blocker",
            name="creator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_blockers",
                to="teams.member",
                verbose_name="ثبت‌کننده",
            ),
        ),
    ]
