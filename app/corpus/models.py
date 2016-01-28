from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, UTCDateTimeAttribute


class Corpus():
    pass


class Phrase(Model):
    class Meta:
        table_name = 'phrase'

    id = NumberAttribute(hash_key=True)
    observed_at = UTCDateTimeAttribute
    source_lang = UnicodeAttribute
    target_lang = UnicodeAttribute
    source_text = UnicodeAttribute
    target_text = UnicodeAttribute


class Sentence(Model):
    class Meta:
        table_name = 'sentence'

    id = NumberAttribute(hash_key=True)
    observed_at = None
    source_lang = UnicodeAttribute
    target_lang = UnicodeAttribute
    source_text = UnicodeAttribute
    target_text = UnicodeAttribute


if __name__ == '__main__':
    if not Phrase.exists():
        Phrase.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

    import pdb
    pdb.set_trace()

    item = Phrase(1)
    item.save()
