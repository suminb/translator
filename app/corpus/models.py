from winnowing import winnow, kgrams, winnowing_hash, sanitize
from google.appengine.ext import ndb


FINGERPRINT_K = 4


class Corpus(ndb.Model):
    source_lang = ndb.StringProperty(indexed=True)
    target_lang = ndb.StringProperty(indexed=True)


class _Corpus():
    """A corpus is a pair of strings shorter than 255 characters each."""

    # __table_args__ = ( db.UniqueConstraint('source_lang', 'target_lang',
    #    'source_text', 'target_text'), )

    # id = db.Column(UUID, primary_key=True)
    # source_lang = db.Column(db.String(16))
    # target_lang = db.Column(db.String(16))
    # source_text = db.Column(db.String(255)) # NOTE: Not sure if this is the number of bytes or the number of characters
    # target_text = db.Column(db.String(255))
    # confidence = db.Column(db.Integer)
    # frequency = db.Column(db.Integer)
    # aux_info = db.Column(db.String(255))
    # avg_confidence = confidence / frequency


    # def create_index(self):
    #     import json

    #     fingerprints = winnow(self.source_text, FINGERPRINT_K)
    #     #fingerprints = kgrams(self.source_text, 4)

    #     for i, h in fingerprints:
    #         #print i, h, self.source_text[i:]
    #         if i != -1:
    #             if CorpusIndex.query.filter_by(
    #                 source_hash=h,
    #                 source_index=i,
    #                 corpus_id=self.id).first() == None:

    #                 CorpusIndex.insert(
    #                     source_hash=h,
    #                     source_index=i,
    #                     corpus_id=self.id,
    #                     commit=False,
    #                 )

    #     self.aux_info = json.dumps(dict(processed_index=True))

    #     try:
    #         db.session.commit()
    #     except:
    #         db.session.rollback()

    @staticmethod
    def match(text, source_lang=None, target_lang=None):
        #fingerprints = winnow(text)

        agtext = zip(xrange(len(text)), text)
        agtext = sanitize(agtext)

        #print list(kgrams(agtext, FINGERPRINT_K))

        hashes = map(lambda x: winnowing_hash(x), kgrams(agtext, FINGERPRINT_K))

        #print zip(*hashes)

        # for kgram in kgrams(agtext, FINGERPRINT_K):
        #     print kgram, ', ',
        # print
        # print hashes

        indices = CorpusIndex.query \
                    .filter(CorpusIndex.source_hash.in_(zip(*hashes)[1]))

        if source_lang != None:
            indices = indices.filter(Corpus.source_lang == source_lang)

        if target_lang != None:
            indices = indices.filter(Corpus.target_lang == target_lang)

        return indices


class CorpusIndex():
    # Without __tablename__ attribute, the following error will occur.
    # sqlalchemy.exc.InvalidRequestError: Class <class 'app.models.Watching'>
    # does not have a __table__ or __tablename__ specified and does not inherit
    # from an existing table-mapped class.
    pass
    # __tablename__ = 'corpus_index'
    # __table_args__ = ( db.PrimaryKeyConstraint('source_hash', 'source_index',
    #     'corpus_id'), {} )

    # source_hash = db.Column(db.Integer)
    # source_index = db.Column(db.Integer)
    # corpus_id = db.Column(UUID, db.ForeignKey('corpus.id'))
    # corpus = relationship('Corpus')

    # def serialize(self):
    #     data = super(CorpusIndex, self).serialize()

    #     data['corpus'] = self.corpus.serialize()

    #     return data


class CorpusRaw(ndb.Model):
    timestamp = ndb.DateTimeProperty()
    source_lang = ndb.StringProperty(indexed=True)
    target_lang = ndb.StringProperty(indexed=True)
    # How do we enforce 'unique' constraints?
    hash = ndb.StringProperty(indexed=True)
    raw = ndb.TextProperty()
    flags = ndb.IntegerProperty()

    def extract_corpora(self):

        import json

        def insert_corpora(source_lang, source_text, target_lang, target_text,
                           confidence):

            #
            # FIXME: Any better idea?
            #
            PUNCTUATION = '.,:;-_+={}[]()<>|\'"`~!@#$%^&*?'

            if source_text == '' or source_text in PUNCTUATION:
                return
            if target_text == '' or target_text in PUNCTUATION:
                return
            if source_text == target_text:
                return

            corpus = Corpus.query.filter_by(
                source_lang=source_lang, target_lang=target_lang,
                source_text=source_text, target_text=target_text,
            ).first()

            if corpus is None:
                corpus = Corpus.insert(
                    source_lang=source_lang, target_lang=target_lang,
                    source_text=source_text, target_text=target_text,
                    confidence=confidence, frequency=1,
                    commit=False,
                )
            else:
                corpus.confidence += confidence
                corpus.frequency += 1

        raw = json.loads(self.raw)
        if len(raw) >= 6 \
            and raw[4] != None and len(raw[4]) > 0 \
            and raw[5] != None and len(raw[5]) > 0:

            for source, target in zip(raw[5], raw[4]):

                source_text, target_text = source[0], target[0]
                confidence = int(target[4])

                insert_corpora(self.source_lang.strip(), source_text.strip(),
                    self.target_lang.strip(), target_text.strip(), confidence)

        self.flags |= 1
        db.session.commit()
