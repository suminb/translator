var examples = {
    en: [
        "The Google translator that you did not know about",
        "Google is dreaming of the world conquest.",
        "When in Rome do as the Romans do.",
        "An eigenvector of a square matrix A is a non-zero vector v that, when multiplied by A, yields the original vector multiplied by a single number L; that is, Av = Lv. The number L is called the eigenvalue of A corresponding to v.",
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


var state = {
    source: null, // source language
    intermediate: null, // intermediate language
    target: null, // target language
    text: null,
    result: null,

    id: null,
    requestId: null,
    serial: null,
    exampleIndex: 0,

    pending: false,

    setSource: function(v) {
        this.source = v;
        $("select[name=sl]").val(v);
    },

    setIntermediate: function(v) {
        this.intermediate = v;
        $("select[name=il]").val(v);
    },

    setTarget: function(v) {
        this.target = v;
        $("select[name=tl]").val(v);
    },

    setText: function(v) {
        this.text = v;
        $("#text").val(v);
    },

    setResult: function(v) {
        //this.result = v;
        $("#result").html(v);
    },

    selectSource: function(v) {
        this.source = v;
        this.setResult("");

        $.cookie("source", v);
    },

    selectIntermediate: function(v) {
        this.intermediate = v;
        this.setResult("");

        $.cookie("intermediate", v);
    },

    selectTarget: function(v) {
        this.target = v;
        this.setResult("");

        $.cookie("target", v);
    },

    init: function() {
        this.setSource(typeof $.cookie("source") != "undefined" ?
            $.cookie("source") : "auto");
        this.setIntermediate(typeof $.cookie("intermediate") != "undefined" ?
            $.cookie("intermediate") : "jp");
        this.setTarget(typeof $.cookie("target") != "undefined" ?
            $.cookie("target") : "en");
    },

    initWithState: function(state) {
        this.setSource(state.source);
        this.setIntermediate(state.intermediate);
        this.setTarget(state.target);
        this.setText(state.text);
        //this.setResult(state.result);
    },

    initWithParameters: function() {
        this.setSource(getParameterByName("sl"));
        this.setIntermediate(getParameterByName("il"));
        this.setTarget(getParameterByName("tl"));
        this.setText(getParameterByName("t"));
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
    },

    swapLanguages: function() {
        var source = this.source;
        var target = this.target;

        this.setSource(target);
        this.setTarget(source);

        $.cookie("source", target);
        $.cookie("target", source);
    },

    // Sometimes we want to update the textarea, sometimes now.
    // The 'updateText' parameter indicates whether we want to do that. However,
    // this meant to be a temporary solution.
    invalidateUI: function(updateText) {
        updateText = typeof updateText !== 'undefined' ? updateText : true;

        $("select[name=sl]").val(this.source);
        $("select[name=il]").val(this.intermediate);
        $("select[name=tl]").val(this.target);

        if (updateText) {
            $("#text").val(this.text);
        }

        if (this.result) {

            $("#result").html(extractSentences(this.result));

            // var resultDiv = $("#result");
            // var sourceText = this.result[0][0][1];

            // $(this.result[5]).each(function(i, v) {
            //     console.log(v);

            //     var targetCorpus = v[2][0][0];
            //     var sourceRanges = v[3];

            //     $(sourceRanges).each(function(i, v) {
            //         var sourceCorpus = sourceText.substring(v[0], v[1]);
            //         console.log(sourceCorpus);
            //     });

            //     var corpusSpan = $("<span></span>")
            //         .addClass("corpus")
            //         .text(targetCorpus);

            //     resultDiv.append(corpusSpan);
            //     resultDiv.append(" ");
            // });
        }
    },

    /**
     * Updates state based on the values of the UI controls
     */
    update: function() {
        this.source = $("select[name=sl]").val();
        this.intermediate = $("select[name=il]").val();
        this.target = $("select[name=tl]").val();
        this.text = $("#text").val();
    },

    serialize: function() {
        this.update();

        return {
            source: this.source,
            intermediate: this.intermediate,
            target: this.target,
            text: this.text,
            result: this.result
        };
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
    var url = "http://translate.google.com/translate_a/t";

    if (method.toLowerCase() == 'get') {
        return sprintf("%s?client=t&sl=%s&tl=%s&text=%s", url, sl, tl,
            encodeURIComponent(text));
    }
    else if (method.toLowerCase() == 'post') {
        return sprintf("%s?client=t&sl=%s&tl=%s", url, sl, tl);
    }
    else {
        throw "Unsupported method";
    }
}

function extractSentences(raw) {
    return "".concat(
            $.map(raw[0], (function(v) { return v[0]; }))
        );
}

function performTranslation() {

    // Function currying
    // Rationale: It would be almost impossible to get the value of 'target' unless it
    // is declared as a global variable, which I do not believe it is a good practice in general
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
                state.result = eval(response);

                // detected source language
                var source = state.result[2];

                uploadRawCorpora(source, target, JSON.stringify(state.result));
            }
        };
    };

    var onAlways = function() {
        $("#progress-message").hide();
        enableControls(true);

        // This must be called after enableControls()
        state.invalidateUI(false);

        state.pending = false;
    };

    if (state.pending) {
        // If there is any pending translation request,
        // silently abort the request.
        return false;
    }

    state.update();

    if (state.source == state.target) {
        // simply displays the original text when the source language and
        // the target language are identical
        state.setResult(state.text);
    }
    else if (state.source == "" || state.target == "") {
         // TODO: Give some warning
    }
    else if (state.text == null || state.text == "") {
         // TODO: Give some warning
    }
    else if (encodeURIComponent(state.text).length > 8000) {
        displayError("Text is too long.",
            "For more detail, please refer <a href=\"/longtext\">this page</a>.");
    }
    else {
        // translates if the source language and the target language are not
        // identical

        hideError();
        $("#result").empty();
        $("#progress-message").show();

        enableControls(false);
        hideAuxInfo();

        state.pending = true;

        if (state.intermediate) {

            sendTranslationRequest(state.source, state.intermediate, state.text, function(response) {

                onSuccess(state.intermediate)(response);

                // Delay for a random interval (0.5-1.5 sec)
                var delay = 500 + Math.random() * 1000;

                setTimeout(function() {
                    state.pending = true;
                    sendTranslationRequest(state.intermediate, state.target,
                        extractSentences(state.result),
                        onSuccess(state.target),
                        onAlways
                    );
                }, delay);

            }, function() {
                state.invalidateUI();
                $("#progress-message").show();
            });
        }
        else {
            sendTranslationRequest(state.source, state.target, state.text,
                onSuccess(state.target), onAlways);
        }

//        if ($.cookie("locale") == "ko" && state.text.length < 60) {
//            showNaverEndic(state.text);
//        }
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

    var requestFunction = textLength < 900 ?
        $.get : $.post;

    var requestMethod = textLength < 900 ?
        "GET" : "POST";

    var url = sprintf(
        "http://goxcors-clone.appspot.com/cors?method=%s&header=%s&url=%s",
        //"http://goxcors-clone.appspot.com/jsonp?callback=&method=%s&header=%s&url=%s",
        requestMethod, header, encodeURIComponent(
            buildTranslateURL(source, target, text, requestMethod))
    );

    if (msie()) {
        sendXDomainRequest(url, requestMethod, {q: text}, onSuccess, onAlways);
    }
    else {
        requestFunction(url, {q: text}, onSuccess).fail(function(response) {
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

    var serial = phash.sr ? phash.sr[0] : "";

    if (serial) {
        $("#request-permalink").hide();

        // If a translation record is not newly loaded
        if (serial != state.serial) {
            fetchTranslation(serial);
        }

        state.serial = serial;
    }
    else if(getParameterByName("t")) {
        // Perform no action
    }
    else {
        var source = phash.sl;
        var target = phash.tl;
        var intermediate = phash.il;
        var text = phash.t;

        $("select[name=sl]").val(source ? source : state.source);
        $("select[name=il]").val(intermediate ? intermediate : state.intermediate);
        $("select[name=tl]").val(target ? target : state.target);

        if (text) {
            $("#text").val(decodeURIComponent(text));
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

function showNaverEndic(query) {
    var url = sprintf("http://m.endic.naver.com/search.nhn?searchOption=all&query=%s",
        encodeURIComponent(query));

    $("#naver-endic-dialog .modal-body iframe")
        .attr("src", url)
        .load(function() {
            $("#aux-naver-endic").show();
        });   
}

function hideAuxInfo() {
    $("#aux-naver-endic").hide();
}
