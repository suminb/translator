var BindingView = Backbone.Epoxy.View.extend({
  el: '#translation-form',
  bindings: {
    "select[name=sl]": "value:sourceLanguage,options:languages",
    "select[name=il]": "value:intermediateLanguage,options:intermediateLanguages",
    "select[name=tl]": "value:targetLanguage,options:languages",
    "#source-text": "value:sourceText,events:['keyup']",
    "#target-text": "text:targetText"
  },
  events: {
    'change select[name=sl]': 'onChangeSourceLanguage',
    'change select[name=il]': 'onChangeIntermediateLanguage',
    'change select[name=tl]': 'onChangeTargetLanguage'
  },

  // FIXME: The following event handlers could be further simplified
  onChangeSourceLanguage: function(e) {
    $.cookie('sourceLanguage', model.get('sourceLanguage'));
  },
  onChangeIntermediateLanguage: function(e) {
    $.cookie('intermediateLanguage', model.get('intermediateLanguage'));
  },
  onChangeTargetLanguage: function(e) {
    $.cookie('targetLanguage', model.get('targetLanguage'));
  },
});

var Model = Backbone.Model.extend({
  defaults: {
    languages: [],
    intermediateLanguages: [],
    sourceLanguage: null,
    intermediateLanguage: null,
    targetLanguage: null,
    sourceText: '',
    targetText: '',
    raw: null
  },
  hasIntermediateLanguage: function() {
    return this.get('intermediateLanguage') != null &&
           this.get('intermediateLanguage') != '';
  }
});

var model = new Model();
var bindingView = new BindingView({model: model});

var examples = {
    en: [
        "The Google translator that you did not know about",
        "Google is dreaming of the world conquest.",
        "When in Rome do as the Romans do.",
        "An eigenvector of a square matrix A is a non-zero vector v that, \
          when multiplied by A, yields the original vector multiplied by ai \
          single number L; that is, Av = Lv. The number L is called the \
          eigenvalue of A corresponding to v.",
        "What the hell is going on"
    ],
    ko: [
        "여러분이 몰랐던 구글 번역기",
        "샌디에고에 살고 있는 김근모씨는 오늘도 힘찬 출근",
        "구글은 세계 정복을 꿈꾸고 있다.",
        "호준이는 비싼 학비 때문에 허리가 휘어집니다.",
        "청년들을 타락시킨 죄로 독콜라를 마시는 홍민희",
        "강선구 이사님은 오늘도 새로운 기술을 찾아나선다."
    ],
    // TODO: Fill in some example sentences.
    fr: [""],
    es: [""],
    ja: [""],
    ru: [""],
    id: [""]
};

// URL encoded length, exclusively less than
var SHORT_TRANSLATION_THRESHOLD = 256;

var TAGS_TO_REPLACE = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;'
};

/**
 * Copied from http://homework.nwsnet.de/releases/9132/
 */
function _ajax_request(url, data, callback, type, method) {
    if (jQuery.isFunction(data)) {
        callback = data;
        data = {};
    }
    return jQuery.ajax({
        type: method,
        url: url,
        data: data,
        success: callback,
        dataType: type
        });
}
jQuery.extend({
    put: function(url, data, callback, type) {
        return _ajax_request(url, data, callback, type, 'PUT');
    },
    delete_: function(url, data, callback, type) {
        return _ajax_request(url, data, callback, type, 'DELETE');
    }
});

/**
 * Copied from http://stackoverflow.com/questions/9614622/equivalent-of-jquery-hide-to-set-visibility-hidden
 */
$.fn.visible = function() {
    return this.css('visibility', 'visible');
};
$.fn.invisible = function() {
    return this.css('visibility', 'hidden');
};

$.fn.disable = function() {
    return this.attr("disabled", "disabled");
};
$.fn.enable = function() {
    return this.removeAttr("disabled");
};

//
// Facebook API
//
window.fbAsyncInit = function() {
// init the FB JS SDK
FB.init({
  appId      : '551432311581596', // App ID from the app dashboard
  channelUrl : '//better-translator.com/static/channel.html',
                // Channel file for x-domain comms
  status     : true, // Check Facebook Login status
  xfbml      : true  // Look for social plugins on the page
});

// Additional initialization code such as adding Event Listeners goes here
};

// FIMXE: This 'state' object shall be gone completely
var state = {

    id: null,
    requestId: null,
    serial: null,
    exampleIndex: 0,

    pending: false,

    initWithParameters: function() {
      model.set('sourceLanguage', getParameterByName("sl"));
      model.set('intermediateLanguage', getParameterByName("il"));
      model.set('targetLanguage', getParameterByName("tl"));
      model.set('sourceText', getParameterByName("t"));
    },

    initWithTranslation: function(t) {
        this.id = t.id;
        this.requestId = t.request_id;
        this.serial = t.serial;
        this.source = t.source;
        this.intermediate = t.intermediate; // FIXME: This is not implemented on the server side
        this.target = t.target;
        this.text = t.original_text;
        //this.result = t.translated_text;
    },

    updateWithTranslation: function(t) {
        // this.id = t.id;
        // this.requestId = t.request_id;
        // this.result = t.translated_text;

        this.result = t;
    }
};

function msie() {
    return $('html').is('.ie6, .ie7, .ie8');
}

/**
 * Parsing a URL query string
 * http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values
 */
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.search);
    if(results == null) {
        return "";
    }
    else {
        return decodeURIComponent(results[1].replace(/\+/g, " "));
    }
}

/**
 * Copied from http://codereview.stackexchange.com/questions/9574/ \
 *     faster-and-cleaner-way-to-parse-parameters-from-url-in-javascript-jquery
 */
function parseHash(hash) {
    var query = (window.location.search || '#').substr(1),
        map   = {};
    hash.replace(/([^&=]+)=?([^&]*)(?:&+|$)/g, function(match, key, value) {
        (map[key] = map[key] || []).push(value);
    });
    return map;
}

function resizeTextarea(t) {
    var a = t.value.split('\n');
    var b = 1;
    for (var x=0;x < a.length; x++) {
        if (a[x].length >= t.cols) b+= Math.floor(a[x].length/t.cols);
    }
    b+= a.length;
    if (b > t.rows) t.rows = b;
}

function buildTranslateURL(sl, tl, text, method) {
    var url = "http://translate.google.com/translate_a/single";

    // Some extra values that Google Translate sends to its server
    var extra = "dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&dt=at";

    if (method.toLowerCase() == 'get') {
        return sprintf("%s?client=at&sl=%s&tl=%s&%s&q=%s", url, sl, tl, extra,
            encodeURIComponent(text));
    }
    else if (method.toLowerCase() == 'post') {
        return sprintf("%s?client=t&sl=%s&tl=%s&%s", url, sl, tl, extra);
    }
    else {
        throw "Unsupported method";
    }
}

function extractSentences(raw) {
  return $.map(raw[0], (function(v) { return v[0]; })).join('');
}

/**
 * Initializes things with URL hashes or HTTP GET parameters depending on
 * what's available.
 */
function initWithHashesOrParameters() {
  // The following code was copied from
  // http://stackoverflow.com/questions/2161906/handle-url-anchor-change-event-in-js
  if ("onhashchange" in window) { // event supported?
      window.onhashchange = function () {
          hashChanged(window.location.hash);
      };
  }
  else { // event not supported:
      var storedHash = window.location.hash;
      window.setInterval(function () {
          if (window.location.hash != storedHash) {
              storedHash = window.location.hash;
              hashChanged(storedHash);
          }
      }, 250);
  }

  if (getParameterByName("t")) {
      state.initWithParameters();
      performTranslation();
  }
  else {
      hashChanged(window.location.hash ? window.location.hash : "");
  }
}

/**
 * Swap between the source language and the target language.
 */
function swapLanguages(evt) {
  evt.preventDefault();
  var sourceLang = model.get('sourceLanguage');
  model.set('sourceLanguage', model.get('targetLanguage'));
  model.set('targetLanguage', sourceLang);
}

/**
 * Dynamically loads available languages from the server
 */
function loadLanguages() {
  var sltlLoaded = false;
  var lurl = sprintf('/api/v1.3/languages?locale=%s&field=source', locale);
  $.get(lurl, function(response) {
    var languages = $.map(response.languages, function(pair) {
      return {label: pair[1], value: pair[0]};
    });
    var sl = $.cookie('sourceLanguage');
    var tl = $.cookie('targetLanguage');
    model.set('languages', languages);
    model.set('sourceLanguage', sl ? sl : 'en');
    model.set('targetLanguage', tl ? tl : 'ko');
    sltlLoaded = true;
  });

  var ilLoaded = false;
  var ilurl = sprintf('/api/v1.3/languages?locale=%s&field=intermediate&sortby=-1', locale);
  $.get(ilurl, function(response) {
    var languages = $.map(response.languages, function(pair) {
      return {label: pair[1], value: pair[0]};
    });
    var il = $.cookie('intermediateLanguage');
    model.set('intermediateLanguages', languages);
    model.set('intermediateLanguage', il != null ? il : 'ja');
    ilLoaded = true;
  });

  var timer = setInterval(function() {
    if (sltlLoaded && ilLoaded) {
      initWithHashesOrParameters();
      clearInterval(timer);
    }
  }, 100);
}

function performTranslation() {

  var sourceLang = model.get('sourceLanguage');
  var intermediateLang = model.get('intermediateLanguage');
  var targetLang = model.get('targetLanguage');

  var sourceText = model.get('sourceText');

    // Function currying
    // Rationale: It would be almost impossible to get the value of 'target'
    // unless it is declared as a global variable, which I do not believe it is
    // a good practice in general
    var onSuccess = function(target) {
        return function(response) {
            if (!response) {
                displayError("sendTranslationRequest(): response body is null.",
                    null);
            }
            else if (String(response).substring(0, 1) == "<") {
                showCaptcha(response);
            }
            else {
                // FIXME: Potential security vulnerability
                var raw = eval(response);
                var targetText = extractSentences(raw);

                model.set('raw', raw);
                model.set('targetText', targetText);

                // detected source language
                var source = raw[2];

                uploadRawCorpora(source, target, JSON.stringify(targetText));
            }
        };
    };

    var onAlways = function() {
        $("#progress-message").hide();
        enableControls(true);

        state.pending = false;
    };

    if (state.pending) {
        // If there is any pending translation request,
        // silently abort the request.
        return false;
    }

    if (sourceLang == targetLang) {
        // simply displays the original text when the source language and
        // the target language are identical
        model.set('targetText', sourceText);
    }
    else if (sourceLang == '' || targetLang == '') {
         // TODO: Give some warning
    }
    else if (sourceLang == null || sourceText == '') {
         // TODO: Give some warning
    }
    else if (encodeURIComponent(sourceText).length > 8000) {
        displayError("Text is too long.",
            "<a href=\"/download-clients\">Try the Better Translator client</a> to circumvent this issue.");
    }
    else {
        // translates if the source language and the target language are not
        // identical

        hideError();
        $("#progress-message").show();

        enableControls(false);

        state.pending = true;

        if (intermediateLang) {

            sendTranslationRequest(sourceLang, intermediateLang, sourceText, function(response) {

                onSuccess(intermediateLang)(response);

                // Delay for a random interval (0.5-1.5 sec)
                var delay = 500 + Math.random() * 1000;

                setTimeout(function() {
                    state.pending = true;
                    sendTranslationRequest(intermediateLang, targetLang,
                        extractSentences(model.get('raw')),
                        onSuccess(targetLang),
                        onAlways
                    );
                }, delay);

            }, function() {
                $("#progress-message").show();
            });
        }
        else {
            sendTranslationRequest(sourceLang, targetLang, sourceText,
                onSuccess(targetLang), onAlways);
        }

        ga('send', 'event', 'api', 'translate',
           sprintf('sl=%s&il=%s&tl=%s', sourceLang, intermediateLang, targetLang));
    }

    return false;
}

function sendXDomainRequest(url, method, data, onSuccess, onAlways) {
    var xdr = new XDomainRequest();

    xdr.onload = function() {
        onSuccess(xdr.responseText);
        onAlways();
    };

    xdr.onerror = function() {
        onAlways();
    }

    xdr.open(method, url);

    if (method == "POST") {
        xdr.send(JSON.stringify(data) + '&ie=1');
    }
    else {
        xdr.send();
    }
    // TODO: Handle exceptions
}

function sendTranslationRequest(source, target, text, onSuccess, onAlways) {

    var header = "Referer|http://translate.google.com";

    // Use GET for short requests and POST for long requests
    var textLength = encodeURIComponent(text).length;

    // TODO: also consider 'header' value which can be quite long sometimes

    var requestFunction = textLength < 550 ?
        $.get : $.post;

    var requestMethod = textLength < 550 ?
        "GET" : "POST";

    /*
    var url = sprintf(
        "http://goxcors-clone.appspot.com/cors?method=%s&header=%s&url=%s",
        //"http://goxcors-clone.appspot.com/jsonp?callback=&method=%s&header=%s&url=%s",
        requestMethod, header, encodeURIComponent(
            buildTranslateURL(source, target, text, requestMethod))
    );
    */

    var url = '/api/v1.3/translate';

    if (msie()) {
        sendXDomainRequest(url, requestMethod, {q: text}, onSuccess, onAlways);
    }
    else {
        requestFunction(url, {text: text, source: source, target: target}, onSuccess).fail(function(response) {
            displayError(response.responseText, null);

        }).always(onAlways);
    }
}

function uploadRawCorpora(source, target, raw) {
    $.post("/corpus/raw", {sl:source, tl:target, raw:raw});
}

function showCaptcha(body) {

    body = body.replace("/sorry/image",
        "http://translate.google.com/sorry/image");

    body = body.replace("action=\"CaptchaRedirect\"",
        "action=\"http://sorry.google.com/sorry/CaptchaRedirect\"");

    $("#captcha-dialog .modal-body").html(body);
    $("#captcha-dialog").modal("show");
}

// TODO: Refactor this function
function refreshExample() {
    var language = state.source;

    // Randomly chooses an example sentence
    //state.ei = Math.floor(Math.random() * examples.ko.length);

    var example = examples[language][state.exampleIndex++ % examples[language].length];

    $("#text").val(example);

    performTranslation();
}

function displayResult(result) {
    hideError();
    $("#result").html(result);
}

function displayError(message, postfix) {
    if (postfix == null) {
        postfix = 'If problem persists, please report it <a href="/discuss?rel=bug_report">here</a>.';
    }
    $("#error-message").html(sprintf("%s %s", message, postfix)).show();
    $("#result").empty();
}
function hideError() {
	$("#error-message").hide();
}

function hashChanged(hash) {
  var phash = parseHash(hash.substr(1));

  if(getParameterByName("t")) {
      // Perform no action
  }
  else {
    var source = phash.sl;
    var target = phash.tl;
    var intermediate = phash.il;
    var text = phash.t;

    if (source)
      model.set('sourceLanguage', source);
    if (target)
      model.set('targetLanguage', target);
    if (intermediate)
      model.set('intermediateLanguage', intermediate);
    if (text) {
      model.set('sourceText', decodeURIComponent(text));
      performTranslation();
    }
  }
}

function toggleScreenshot() {
    $("#google-translate").toggle("medium");
}

// FIXME: Deprecated
var toggle_screenshot = toggleScreenshot;

function fetchTranslation(serial) {
    $("#progress-message").show();

    $.get("/v0.9/fetch/"+serial, function(response) {
        // TODO: Refactor this part
        $("#text").val(response.original_text);
        $("#result").html(response.translated_text_dictlink);

        $("select[name=sl]").val(response.source);
        $("select[name=il]").val(response.intermediate); // FIXME: Not implemented on server side
        $("select[name=tl]").val(response.target);

        window.history.replaceState(state.serialize(), "", window.location.href);

        //askForRating(response.request_id);

    }).fail(function(response) {
        displayError(response.responseText, null);
    }).always(function() {
        $("#progress-message").hide();
    });
}

function deleteTranslation(id) {
    $("div.alert").hide();

    $.delete_(sprintf("/v1.0/trs/%s", id), function(response) {
        location.href = sprintf("/trequest/%s/response", response.request_id);
    }).fail(function(response) {
        $("div.alert-error").text(response.responseText).show();
    }).always(function() {

    });
}

function displayPermalink(id) {
    var origin = window.location.origin ? window.location.origin
        : window.location.protocol+"//"+window.location.host;
    var path = sprintf("?tr=%s", id);
    var url = origin + path;

    $("#request-permalink").hide();

    window.history.pushState(state.serialize(), "", path);
}

/**
 * @param state True or false
 */
function enableControls(state) {
    if (state) {
        $("form input").enable();
        $("form select").enable();
        $("form button").enable();
    }
    else {
        $("form input").disable();
        $("form select").disable();
        $("form button").disable();
    }
}
