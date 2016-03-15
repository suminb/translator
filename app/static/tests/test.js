QUnit.test('extractSentences', function(assert) {
  var raw = {
    "sentences":[
        {
            "trans":"これはテストです",
            "orig":"This is a test",
            "backend":1
        },
        {
            "translit":"Kore wa tesutodesu"
        }
    ],
    "src":"en",
    "confidence":0.19605306,
    "ld_result":{
        "srclangs":[
            "en"
        ],
        "srclangs_confidences":[
            0.19605306
        ],
        "extended_srclangs":[
            "en"
        ]
    }
  };
  // Single sentence test
  assert.equal(extractSentences(raw), 'これはテストです');

  // TODO: Multi-sentence test
});

QUnit.test('loadIntermediateLanguages', function(assert) {
  var languages = loadIntermediateLanguages('en');
  assert.ok(languages != null);
  assert.equal(languages.length, 3);
  $.each(languages, function(i, v) {
    assert.equal(v.length, 2);
  });
});
