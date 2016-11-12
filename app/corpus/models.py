from logbook import Logger
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute


log = Logger(__name__)


class Translation(Model):
    class Meta:
        table_name = 'translation'

        # NOTE: Could we make this to follow the default settings?
        region = 'ap-northeast-2'

    timestamp = UTCDateTimeAttribute(range_key=True)
    raw = UnicodeAttribute()
    hash = UnicodeAttribute(hash_key=True)
    source_lang = UnicodeAttribute()
    target_lang = UnicodeAttribute()


if __name__ == '__main__':
    if not Translation.exists():
        log.info('Creating a table {}', Translation)
        Translation.create_table(read_capacity_units=1,
                                 write_capacity_units=1, wait=True)
