from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute


class Translation(Model):
    class Meta:
        table_name = 'translation'

        # NOTE: Could we make this to follow the default settings?
        region = 'us-west-2'

    timestamp = UTCDateTimeAttribute(range_key=True)
    raw = UnicodeAttribute()
    hash = UnicodeAttribute(hash_key=True)
    source_lang = UnicodeAttribute()
    target_lang = UnicodeAttribute()


if __name__ == '__main__':
    if not Translation.exists():
        Translation.create_table(read_capacity_units=1,
                                 write_capacity_units=1, wait=True)
