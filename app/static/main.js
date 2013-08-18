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

// URL encoded length, exclsively less than
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
}
$.fn.invisible = function() {
    return this.css('visibility', 'hidden');
}

$.fn.disable = function() {
    return this.attr("disabled", "disabled");
}
$.fn.enable = function() {
    return this.removeAttr("disabled");
}

//
// Facebook API
//
window.fbAsyncInit = function() {
// init the FB JS SDK
FB.init({
  appId      : '551432311581596',                        // App ID from the app dashboard
  channelUrl : '//translator.suminb.com/static/channel.html', // Channel file for x-domain comms
  status     : true,                                 // Check Facebook Login status
  xfbml      : true                                  // Look for social plugins on the page
});

// Additional initialization code such as adding Event Listeners goes here
};


var state = {
    source: 'ko',
    target: 'en',
    mode: 2,
    text: null,
    result: null,

    id: null,
    requestId: null,
    serial: null,
    exampleIndex: 0,

    setSource: function(v) {
        this.source = v;
        $("select[name=sl]").val(v);
    },

    setTarget: function(v) {
        this.target = v;
        $("select[name=tl]").val(v);
    },

    setMode: function(v) {
        this.mode = v;
        $("button.to-mode").removeClass("active");
        $(sprintf("button.to-mode[value=%s]", v)).addClass("active");
    },

    setText: function(v) {
        this.text = v;
        $("#text").val(v);
    },

    setResult: function(v) {
        $("#result").text(v);
    },

    selectSource: function(v) {
        this.source = v;
        this.setResult("");

        if (v == 'ja') {
            this.setMode(1);
            $("button.to-mode[value=2]").disable();
        }
        else {
            $("button.to-mode[value=2]").enable();
        }
    },

    selectTarget: function(v) {
        this.target = v;
        this.setResult("");

        if (v == 'ja') {
            this.setMode(1);
            $("button.to-mode[value=2]").disable();
        }
        else {
            $("button.to-mode[value=2]").enable();
        }
    },

    init: function() {
        // TODO: Use a cookie
        this.setSource("ko");
        this.setTarget("en");
        this.setMode(2);
    },

    initWithParameters: function() {
        this.setSource(getParameterByName("sl"));
        this.setTarget(getParameterByName("tl"));
        this.setMode(getParameterByName("m"));
        this.setText(getParameterByName("t"));
    },

    initWithTranslation: function(t) {
        this.id = t.id;
        this.requestId = t.request_id;
        this.serial = t.serial;
        this.source = t.source;
        this.target = t.target;
        this.mode = t.mode;
        this.text = t.original_text;
        this.result = t.translated_text;
    },

    updateWithTranslation: function(t) {
        this.id = t.id;
        this.requestId = t.request_id;
        this.result = t.translated_text;
    },

    swapLanguages: function() {
        var source = this.source;
        var target = this.target;

        this.setSource(target);
        this.setTarget(source);
        this.setText($("#result").text());

        performTranslation();
    },

    invalidateUI: function() {
        $("select[name=sl]").val(this.source);
        $("select[name=tl]").val(this.target);
        $("button.to-mode").removeClass("active");
        $(sprintf("button.to-mode[value=%s]", this.mode)).addClass("active");
        $("#text").val(this.text);

        if (this.result) {
            $("#result").text(this.result);
        }
        if (this.id) {
            displayPermalink(this.id);
            askForRating(this.requestId);
        }
    },

    serialize: function() {
        this.text = $("#text").val();

        return {
            sl: this.source,
            tl: this.target,
            m: this.mode,
            t: this.text
        };
    }
};


/**
 * Copied from http://stackoverflow.com/questions/5499078/fastest-method-to-escape-html-tags-as-html-entities
 */
function replaceTag(tag) {
    return TAGS_TO_REPLACE[tag] || tag;
}
function replaceTags(str) {
    return str.replace(/[&<>]/g, replaceTag);
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
 * Copied from http://codereview.stackexchange.com/questions/9574/faster-and-cleaner-way-to-parse-parameters-from-url-in-javascript-jquery
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
    a = t.value.split('\n');
    b = 1;
    for (x=0;x < a.length; x++) {
        if (a[x].length >= t.cols) b+= Math.floor(a[x].length/t.cols);
    }
    b+= a.length;
    if (b > t.rows) t.rows = b;
}

function performTranslation() {

    if (state.source == state.target) {
        // simply displays the original text when the source language and the target language are identical
        state.setResult(state.text);
    }
    else {
        // translates if the source language and the target language are not identical
        if (state.text !== "") {
            $("#error-message").html("");
            $("#result").html("");
            $("#progress-message").show();
            $("#page-url").invisible();
            $("#rating").invisible();
            enableControls(false);

            $.post("/v1.0/translate", state.serialize(), function(response) {
                state.updateWithTranslation(response);

                window.location.hash = "";
                //window.history.pushState(currentState, "", window.location.href);

                if (state.id) {
                    askForRating(response.request_id);
                    displayPermalink(response.id);

                    if (state.text.length <= 180) {
                        $("a.to-mode")
                            .attr("href", sprintf("/trq/%s/responses", response.request_id))
                            .show();
                    }
                    else {
                        $("a.to-mode").hide();
                    }
                }

                state.invalidateUI();

            }).fail(function(response) {
                displayError(response.responseText);
            
            }).always(function() {
                $("#progress-message").hide();
                enableControls(true);
            });
        }
    }
    
    return false;
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
    $("#error-message").html("");
    $("#result").html(result);
}

/**
 * @deprecated
 */
function displayPageURL(source, target, mode, text) {
    var encoded = encodeURIComponent(text);
    if (encoded.length < SHORT_TRANSLATION_THRESHOLD) {
        var url = sprintf("%s/#sl=%s&tl=%s&m=%s&t=%s", window.location.origin, source, target, mode, encoded);

        $("#page-url").visible();
        $("#page-url-value").html(sprintf("<a href=\"%s\">%s</a>", url, url));
    }
    else {
        $("#page-url").invisible();
    }
}

function displayError(message) {
    var postfix = ' If problem persists, please report it <a href="/discuss">here</a>.'
    $("#error-message").html(message + postfix);
    $("#result").html("");
}

function hashChanged(hash) {
    phash = parseHash(hash.substr(1));

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
        var mode = phash.m;
        var text = phash.t;

        $("select[name=sl]").val(source ? source : "ko");
        $("select[name=tl]").val(target ? target : "en");

        //var mode = getParameterByName("m") == "1";
        //$(mode ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");

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
toggle_screenshot = toggleScreenshot;

function fetchTranslation(serial) {
    //$("#progress-message").html("Fetching requested resources...");
    $("#progress-message").show();

    $.get("/v0.9/fetch/"+serial, function(response) {
        // TODO: Refactor this part
        $("#text").val(response.original_text);
        $("#result").html(response.translated_text);

        $("select[name=sl]").val(response.source);
        $("select[name=tl]").val(response.target);

        var mode = response.mode == "1";
        $(mode ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");

        window.history.replaceState(serializeCurrentState(), "", window.location.href);

        askForRating(response.request_id);

    }).fail(function(response) {
        displayError(response.responseText)
    
    }).always(function() {
        $("#progress-message").hide();
    });
}

function rateTranslation(button) {
    //var original = $("text").val();
    //var encoded = encodeURIComponent(original);

    var buttonGroup = button.parent();
    var translationId = button.attr("translation-id");
    var rating = parseInt(button.attr("rating"));
    var url = sprintf("/v1.0/tr/%s/rate", translationId);

    $.post(url, {r:rating}, function(response) {
        buttonGroup.children().removeClass("active");
        button.addClass("active");

        $(sprintf("span.rating-plus[translation-id=%s]", translationId)).text(response.plus_ratings);
        $(sprintf("span.rating-minus[translation-id=%s]", translationId)).text(response.minus_ratings);
    }).fail(function(response) {
    
    }).always(function() {

    });
}

function deleteTranslation(id) {
    $("div.alert").hide();

    $.delete_(sprintf("/v1.0/trs/%s", id), function(response) {
        location.href = sprintf("/trq/%s/response", response.request_id);
    }).fail(function(response) {
        $("div.alert-error").text(response.responseText).show();
    }).always(function() {

    });
}

function displayPermalink(id) {
    var origin = window.location.origin ? window.location.origin
        : window.location.protocol+"//"+window.location.host;
    var url = sprintf("%s/tr/%s", origin, id);

    $("#request-permalink").hide();
    $("#page-url").visible();
    $("#page-url-value").html(sprintf("<a href=\"%s\">%s</a>", url, url));

    //window.history.pushState(serializeCurrentState(), "", sprintf("/tr/%s", id));
}

function askForRating(id) {
    console.log(id);
    $("#appreciation").hide();

    if (state.text.length <= 180) {
        $("#rating").visible();
        //$("#rating a.translation-challenge").attr("href", sprintf("/trq/%s/response", id));
    }
}

function expressAppreciation() {
    $("#text").removeAttr("disabled");
    $("#rating").invisible();
    $("#alternative-translation-form").hide("medium");
    $("#appreciation").show("medium");
    setTimeout(function() { $("#appreciation").hide("medium"); }, 5000);
}

/**
 * @param state True or false
 */
function enableControls(state) {
    if (state) {
        $("form input").removeAttr("disabled");
        $("form select").removeAttr("disabled");
        $("form button").removeAttr("disabled");
    }
    else {
        $("form input").attr("disabled", "disabled");
        $("form select").attr("disabled", "disabled");
        $("form button").attr("disabled", "disabled");
    }
}
