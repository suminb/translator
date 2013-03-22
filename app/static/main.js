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
        "청년들을 타락시킨 죄로 독콜라를 마시는 홍민희",
        "샌디에고에 살고 있는 김근모씨는 오늘도 힘찬 출근",
        "구글은 세계 정복을 꿈꾸고 있다.",
        "강선구 이사님은 오늘도 새로운 기술을 찾아나선다.",
        "전망 좋은 카페에 앉아 먹었던 티라미수",
        "호준이는 비싼 학비 때문에 허리가 휘어집니다."
    ]
};

var global = {};

window.onload = function() {
    var mode = getParameterByName("mode") == "1";
    $(mode ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");

    // The following code was copied from
    // http://stackoverflow.com/questions/2161906/handle-url-anchor-change-event-in-js
    if ("onhashchange" in window) { // event supported?
        window.onhashchange = function () {
            hashChanged(window.location.hash);
        }
    }
    else { // event not supported:
        var storedHash = window.location.hash;
        window.setInterval(function () {
            if (window.location.hash != storedHash) {
                storedHash = window.location.hash;
                hashChanged(storedHash);
            }
        }, 100);
    }
    
    hashChanged(window.location.hash ? window.location.hash : "");
    
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
            _translate();
        }
    })
    .bind('paste', function (event) {
        // http://stackoverflow.com/questions/9494283/jquery-how-to-get-the-pasted-content
        // When pasting to an input the "paste" event is fired before the value has time to update
        // Therefore, _translate() function has to be called after the completion of this event handling function
        setTimeout(_translate, 100);
    })
    .trigger("change");
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

function resizeTextarea(t) {
    a = t.value.split('\n');
    b = 1;
    for (x=0;x < a.length; x++) {
        if (a[x].length >= t.cols) b+= Math.floor(a[x].length/t.cols);
    }
    b+= a.length;
    if (b > t.rows) t.rows = b;
}

function _translate() {
    if ($("select[name=source]").val() == $("select[name=target]").val()) {
        // simply displays the original text when the source language and the target language are identical
        displayResult($("#text").val());
    }
    else {
        // translates if the source language and the target language are not identical
        $.post("/translate", $("form").serializeArray(), function(response) {
                displayResult(response);
            }
        ).fail(function(response) {
                displayError(response.responseText)
            }
        );
    }
    
    return false;
}

// TODO: Refactor this function
function displayExample() {
    global.ei = parseInt(getParameterByName("example"));
    if (isNaN(global.ei)) {
        // Randomly chooses an example sentence
        global.ei = Math.floor(Math.random() * examples.ko.length)
    }

    var example = examples.ko[global.ei % examples.ko.length];

    $("#text").val(example);
    _translate();
}

// TODO: Refactor this function
function refreshExample() {
    var language = $("select[name=source]").val();

    console.log(language);
    console.log(examples[language]);

    var example = examples[language][++global.ei % examples[language].length];

    console.log(example);

    //window.location.hash = "#text=" + example;

    console.log(example);

    $("#text").val(example);
    _translate();
}

function displayResult(result) {
    $("#error-message").html("");
    $("#result").html(result);
}

function displayError(message) {
    $("#error-message").html(message);
    $("#result").html("");
}

function hashChanged(hash) {
    if(hash.match(/^#text=/)) {
        $("#text").val(decodeURIComponent(hash.substring(6)));
        _translate();
    }
    else {
        displayExample();
    }
}

function toggle_screenshot() {
    $("#google-translate").toggle();
}