from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('rosary', '0004_mysterygroup_audio_file'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            CREATE OR REPLACE FUNCTION rosary_prayer_tsvector_trigger() RETURNS trigger AS $$
            begin
              new.tsv := setweight(to_tsvector('french', coalesce(new.text, '')), 'A');
              return new;
            end
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
            ON rosary_prayer FOR EACH ROW EXECUTE FUNCTION rosary_prayer_tsvector_trigger();
            
            -- Update existing rows to populate the TSV column initially
            UPDATE rosary_prayer SET id = id;
            ''',
            reverse_sql='''
            DROP TRIGGER IF EXISTS tsvectorupdate ON rosary_prayer;
            DROP FUNCTION IF EXISTS rosary_prayer_tsvector_trigger();
            '''
        ),
    ]
