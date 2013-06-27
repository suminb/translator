var global = {};

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

    if (global.serial) {
        displayPermalink(global.serial);
        populateValues({
            t: global.translation.original_text,
            s: global.translation.translated_text,
            m: global.translation.mode,
            sl: global.translation.source,
            tl: global.translation.target
        });
        askForRating();
    }
    else {
        if (getParameterByName("t")) {
            initWithParameters();
        }
        else {
            $("select[name=sl]").val("ko");
            $("select[name=tl]").val("en");
            $("#radio-mode-2").attr("checked", "checked");
            
            // indicates the initial state
            if (global.ei == -1) {
                refreshExample();
            }
            hashChanged(window.location.hash ? window.location.hash : "");
        }
    }
    
    $("#text").autoResize({
        // On resize:
        onResize : function() {
            $(this).css({opacity:0.8});
        },
        // After resize:
        animateCallback : function() {
            $(this).css({opacity:1});
        },
        // Quite slow animation:
        animateDuration : 300,
        // More extra space:
        extraSpace : 40
    })
    .keypress(function (event) {
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
};

window.onpopstate = function(event) {
    console.log(event);
    populateValues(event.state);
};

/**
 * When $GET[t] is a non-trivial value, pre-populate the input fields and perform the translation.
 */
function initWithParameters() {
    populateValues({
        t: getParameterByName("t"),
        m: getParameterByName("m"),
        sl: getParameterByName("sl"),
        tl: getParameterByName("tl")
    });

    performTranslation();
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
    if(results == null)
        return "";
    else
        return decodeURIComponent(results[1].replace(/\+/g, " "));
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
    var currentState = serializeCurrentState();

    var source = currentState.sl;
    var target = currentState.tl;
    var text = currentState.t;

    if (source == target) {
        // simply displays the original text when the source language and the target language are identical
        displayResult(text);
    } else {
        // translates if the source language and the target language are not identical
        if (text !== "") {
            $("#result").html("");
            $("#progress-message").html("Translation in progress...");
            $("#page-url").hide("medium");
            //$("form input[type=submit]").attr("disabled", "disabled");
            global.serial = null;

            $.post("/v1.0/translate", currentState, function(response) {
                displayResult(response.translated_text);

                global.serial = response.serial_b62;
                window.location.hash = "";
                //window.history.pushState(currentState, "", window.location.href);

                if (global.serial) {
                    //$("#request-permalink").show("medium");
                    askForRating();
                    displayPermalink(global.serial);
                }

            }).fail(function(response) {
                displayError(response.responseText);
            
            }).always(function() {
                $("#progress-message").html("");
                //$("form input[type=submit]").removeAttr("disabled");
            });
        }
    }
    
    return false;
}

// // TODO: Refactor this function
// function displayExample() {
//     global.ei = parseInt(getParameterByName("example"));
//     if (isNaN(global.ei)) {
//         // Randomly chooses an example sentence
//         global.ei = Math.floor(Math.random() * examples.ko.length)
//     }

//     var example = examples.ko[global.ei % examples.ko.length];

//     $("#text").val(example);
//     performTranslation();
// }

// TODO: Refactor this function
function refreshExample() {
    var language = $("select[name=sl]").val();

    // Randomly chooses an example sentence
    global.ei = Math.floor(Math.random() * examples.ko.length);
    var example = examples[language][global.ei % examples[language].length];

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
    $("#error-message").html(message);
    $("#result").html("");
}

function hashChanged(hash) {
    phash = parseHash(hash.substr(1));

    var serial = phash.sr ? phash.sr[0] : "";

    if (serial) {
        $("#request-permalink").hide();

        // If a translation record is not newly loaded
        if (serial != global.serial) {
            fetchTranslation(serial);
        }

        global.serial = serial;
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

function swapLanguages() {
    var source = $("select[name=sl]").val();
    var target = $("select[name=tl]").val();

    $("select[name=sl]").val(target);
    $("select[name=tl]").val(source);
    $("#text").val($("#result").html());
    performTranslation();
}

function toggleScreenshot() {
    $("#google-translate").toggle("medium");
}

// FIXME: Deprecated
toggle_screenshot = toggleScreenshot;

function fetchTranslation(serial) {
    $("#progress-message").html("Fetching requested resources...");

    $.get("/v0.9/fetch/"+serial, function(response) {
        // TODO: Refactor this part
        $("#text").val(response.original_text);
        $("#result").html(response.translated_text);

        $("select[name=sl]").val(response.source);
        $("select[name=tl]").val(response.target);

        var mode = response.mode == "1";
        $(mode ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");

        console.log("Replacing current history");
        window.history.replaceState(serializeCurrentState(), "", window.location.href);

        askForRating();

    }).fail(function(response) {
        displayError(response.responseText)
    
    }).always(function() {
        $("#progress-message").html("");
    });
}

function rate(rating) {
    // if not already store (has a permalink)

    var original = $("text").val();
    var encoded = encodeURIComponent(original);

    if (global.serial) {
        $.post("/v0.9/rate/"+global.serial, {r:rating}, function(response) {
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

/**
 * @param pairs Key-value pairs
 * @param sendRating A function to be called when parmalink generation was successful
 */
function generatePermalink(sendRating, rating) {

    $("#request-permalink").hide("medium");

    $.post("/v0.9/store", serializeCurrentState(), function(response) {
        displayPermalink(response.base62);

        if (sendRating !== null) {
            sendRating(response.base62, rating);
        }

    }).fail(function(response) {
        displayError(response.responseText)
    
    }).always(function() {

    });
}

function displayPermalink(serial) {
    if (serial) {
        var url = $.sprintf("%s/sr/%s", window.location.origin, serial);

        $("#request-permalink").hide("medium");
        $("#page-url").show("medium");
        $("#page-url-value").html($.sprintf("<a href=\"%s\">%s</a>", url, url));

        global.serial = serial;
        window.history.pushState(serializeCurrentState(), "", $.sprintf("/sr/%s", serial));
    }
}

function submitAlternativeTranslation() {
    expressAppreciation();
    return false;
}

function skipAlternativeTranslation() {
    expressAppreciation();
}

function askForRating() {
    $("#appreciation").hide("medium");
    $("#rating").show("medium");
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

function serializeCurrentState() {
    return {
        t: $("#text").val(),
        m: $("input[name=m]:checked").val(),
        sl: $("select[name=sl]").val(),
        tl: $("select[name=tl]").val(),
        s: $("#result").html()
    };
}

function populateValues(state) {
    if (state !== null) {
        $("#text").val(state.t ? state.t : "");
        $("select[name=sl]").val(state.sl ? state.sl : "ko");
        $("select[name=tl]").val(state.tl ? state.tl : "en");
        $(state.m == "1" ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");
        $("#result").html(state.s ? state.s : "")
    }
}