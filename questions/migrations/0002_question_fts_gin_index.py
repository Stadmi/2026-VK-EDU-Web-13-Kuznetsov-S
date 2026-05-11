from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX question_fts_gin_idx
                ON questions_question
                USING GIN (
                    to_tsvector('russian',
                        coalesce(title, '') || ' ' || coalesce(text, ''))
                );
            """,
            reverse_sql="DROP INDEX IF EXISTS question_fts_gin_idx;",
        ),
    ]
