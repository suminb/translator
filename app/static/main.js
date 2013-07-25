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

var state = {
    source: 'ko',
    target: 'en',
    mode: 2,
    text: null,
    result: null,

    id: null,
    id_b62: null,
    serial: null,
    example_index: 0,

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
        $($.sprintf("button.to-mode[value=%s]", v)).addClass("active");
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
    },

    selectTarget: function(v) {
        this.target = v;
        this.setResult("");
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
        this.id_b62 = t.id_b62;
        this.serial = t.serial;
        this.source = t.source;
        this.target = t.target;
        this.mode = t.mode;
        this.text = t.original_text;
        this.result = t.translated_text;
    },

    updateWithTranslation: function(t) {
        this.id = t.id;
        this.id_b62 = t.id_b62;
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
        $($.sprintf("button.to-mode[value=%s]", this.mode)).addClass("active");
        $("#text").val(this.text);

        if (this.result) {
            $("#result").text(this.result);
        }
        if (this.id) {
            displayPermalink(this.id_b62);
            askForRating(this.id_b62);
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

window.onload = function() {
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

    if (state.id) {
        askForRating(state.id_b62);
    }
    else {
        if (getParameterByName("t")) {
            state.initWithParameters();
        }
        else {
            state.init();
            
            // indicates the initial state
            if (state.example_index == 0) {
                refreshExample();
            }
            hashChanged(window.location.hash ? window.location.hash : "");
        }
    }

    state.invalidateUI();
    
    $("#text, #result").autoResize({
        // On resize:
        onResize: function() {
            $(this).css({opacity:0.8});
        },
        // After resize:
        animateCallback: function() {
            $(this).css({opacity:1});
        },
        // Quite slow animation:
        animateDuration: 300,
        // More extra space:
        extraSpace: 40
    })
    .keypress(function (event) {
        state.text = $("#text").val();
        if (event.keyCode == 13) {
            performTranslation();
        }
    })
    .bind('paste', function (event) {
        // http://stackoverflow.com/questions/9494283/jquery-how-to-get-the-pasted-content
        // When pasting to an input the "paste" event is fired before the value has time to update
        // Therefore, performTranslation() function has to be called after the completion of this event handling function
        setTimeout(performTranslation, 100);
    })
    .trigger("change");

    $("button.to-mode").click(function(evt) {
        var button = $(evt.target);
        button.addClass("active");

        state.mode = button.attr("value");
        performTranslation();
    });
};

window.onpopstate = function(event) {
    
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
        state.setResult(text);
    }
    else {
        // translates if the source language and the target language are not identical
        if (state.text !== "") {
            $("#error-message").html("");
            $("#result").html("");
            $("#progress-message").show();
            $("#page-url").hide();
            $("#rating").hide();
            enableControls(false);
            state.serial = null;

            $.post("/v1.0/translate", state.serialize(), function(response) {
                state.updateWithTranslation(response);

                window.location.hash = "";
                //window.history.pushState(currentState, "", window.location.href);

                if (state.serial) {
                    askForRating(response.id_b62);
                    displayPermalink(response.id_b62);
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

    var example = examples[language][state.example_index++ % examples[language].length];

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
        var url = $.sprintf("%s/#sl=%s&tl=%s&m=%s&t=%s", window.location.origin, source, target, mode, encoded);

        $("#page-url").show("medium");
        $("#page-url-value").html($.sprintf("<a href=\"%s\">%s</a>", url, url));
    }
    else {
        $("#page-url").hide("medium");
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

        askForRating();

    }).fail(function(response) {
        displayError(response.responseText)
    
    }).always(function() {
        $("#progress-message").hide();
    });
}

function rate(rating) {
    //var original = $("text").val();
    //var encoded = encodeURIComponent(original);

    if (state.id) {
        $.post("/v1.0/rate/"+state.id_b62, {r:rating}, function(response) {
            expressAppreciation();

        }).fail(function(response) {
            displayError(response.responseText)
        
        }).always(function() {

        });
    }

    // TODO: I'll do this later
    // if (encoded.length < SHORT_TRANSLATION_THRESHOLD) {

    //     // If negative or neutral rating
    //     if (r < 1) {
    //         askForAlternativeTranslation();
    //     }
    //     else {
    //         expressAppreciation();
    //     }
    // }
}


function displayPermalink(id_b62) {
    var url = $.sprintf("%s/tr/%s", window.location.origin, id_b62);

    $("#request-permalink").hide();
    $("#page-url").show();
    $("#page-url-value").html($.sprintf("<a href=\"%s\">%s</a>", url, url));

    //window.history.pushState(serializeCurrentState(), "", $.sprintf("/tr/%s", id_b62));
}

function submitAlternativeTranslation() {
    expressAppreciation();
    return false;
}

function skipAlternativeTranslation() {
    expressAppreciation();
}

function askForRating(id_b62) {
    $("#appreciation").hide();
    $("#rating").show();
    //$("#rating a.facebook-post").attr("href", $.sprintf("/tr/%s/request", id_b62));
}

function askForAlternativeTranslation() {
    $("#text").attr("disabled", "disabled");
    $("#rating").hide("medium");
    $("#alternative-translation-form").show("medium");
}

function expressAppreciation() {
    $("#text").removeAttr("disabled");
    $("#rating").hide("medium");
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