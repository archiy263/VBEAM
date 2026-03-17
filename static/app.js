// // Voice Login for login.html

// function speak(text) {
//   const speech = new SpeechSynthesisUtterance(text)
//   speech.lang = "en-IN"
//   window.speechSynthesis.speak(speech)
// }

// function addMessage(sender, text) {
//   const chat = document.getElementById("chat")
//   if (!chat) return

//   const div = document.createElement("div")
//   div.innerHTML = "<b>" + sender + ":</b> " + text
//   chat.appendChild(div)
//   chat.scrollTop = chat.scrollHeight
// }


// function startListening() {
//   const SpeechRecognition =
//     window.SpeechRecognition || window.webkitSpeechRecognition

//   if (!SpeechRecognition) {
//     alert("Speech Recognition not supported")
//     return
//   }

//   const recognition = new SpeechRecognition()
//   recognition.lang = "en-IN"

//   recognition.start()

//   recognition.onresult = async function (event) {

//     const transcript = event.results[0][0].transcript

//     recognition.stop()

//     addMessage("You", transcript)

//     const res = await fetch("/command", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ command: transcript })
//     })

//     const data = await res.json()

//     addMessage("Assistant", data.response)
//     speak(data.response)
//   }

// }

// document.addEventListener("DOMContentLoaded", function () {

//   const voiceButton = document.querySelector(".voice")

//   if (!voiceButton) return

//   voiceButton.addEventListener("click", function (e) {
//     e.preventDefault()   // stop normal link redirect

//     const SpeechRecognition =
//       window.SpeechRecognition || window.webkitSpeechRecognition

//     if (!SpeechRecognition) {
//       alert("Speech Recognition not supported in this browser")
//       return
//     }

//     const recognition = new SpeechRecognition()
//     recognition.lang = "en-IN"

//     recognition.start()
//     speak("Say login to continue")

//     recognition.onresult = async function (event) {
//       const transcript = event.results[0][0].transcript.toLowerCase()

//       recognition.stop() // stop listening after first result

//       if (transcript.includes("login")) {

//         speak("Logging you in")

//         setTimeout(() => {
//             window.location.href = "/login/oauth"
//         }, 1500)

//       } else {
//         speak("Voice not recognized")
//       }
//     }

//     recognition.onerror = function () {
//       speak("Microphone error")
//     }

//   })

// })

// ===============================
// GLOBAL STATE
// ===============================

let isListening = false;
let countdownInterval = null;
let voicesLoaded = false;

// Load voices properly (important for Chrome)
window.speechSynthesis.onvoiceschanged = function () {
    voicesLoaded = true;
};

// SPEAK FUNCTION (Natural Voice)

function speak(text, language = "en-IN") {

    window.speechSynthesis.cancel(); // Stop previous speech

    if (!voicesLoaded) {
        window.speechSynthesis.getVoices();
    }

    const speech = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v =>
        v.lang.toLowerCase().includes(language.split("-")[0])
    );
    const preferred = voices.find(v =>
        v.name.includes("Heera") ||
        v.name.includes("Google UK English Female") ||
        v.name.includes("Zira") ||
        v.name.includes("Microsoft")
    );

    if (voice) {
        speech.voice = voice;
    }

    speech.lang = language;
    speech.rate = 0.95;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}


// COUNTDOWN TIMER

function startCountdown(seconds) {

    const recordingText = document.getElementById("recordingText");

    let remaining = seconds;

    recordingText.innerText = `Recording... (${remaining}s)`;

    countdownInterval = setInterval(() => {

        remaining--;

        recordingText.innerText = `Recording... (${remaining}s)`;

        if (remaining <= 0) {
            clearInterval(countdownInterval);
        }

    }, 1000);
}


// START LISTENING

function startListening() {

    if (isListening) return;

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech Recognition not supported in this browser");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.maxAlternatives = 3;
    recognition.continuous = false;
    recognition.interimResults = false;

    isListening = true;

    const mic = document.getElementById("micButton");
    mic.classList.add("recording");

    startCountdown(10);

    // document.getElementById("assistantText").innerText = "Listening...";

    recognition.start();

    const timeout = setTimeout(() => {
        recognition.stop();
    }, 10000);


    recognition.onresult = async function (event) {

        clearTimeout(timeout);

        if (!event.results[0].isFinal) return;

        const transcript = event.results[0][0].transcript
            .toLowerCase()
            .trim();

        document.getElementById("userText").innerText = transcript;

        try {

            const res = await fetch("/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: transcript })
            });

            // const data = await res.json();

            // document.getElementById("assistantText").innerText = data.response;

            // speak(data.response);
            
            const data = await res.json();

            document.getElementById("assistantText").innerText = data.response;

            const langMap = {
                        "en": "en-IN",
                        "hi": "hi-IN",
                        "gu": "gu-IN"
                        };

const ttsLang = langMap[data.language] || "en-IN";

speak(data.response, ttsLang);
            

        } catch (error) {
            document.getElementById("assistantText").innerText =
                "Server error occurred.";
        }

        stopUI();
    };


    recognition.onerror = function (event) {
        console.error(event.error);

    document.getElementById("assistantText").innerText =
        "Sorry, I couldn't hear you clearly.";
        stopUI();
    };

    recognition.onend = function () {
        stopUI();
    };
}


// STOP UI RESET

function stopUI() {

    isListening = false;

    clearInterval(countdownInterval);

    document.getElementById("recordingText").innerText = "";

    const mic = document.getElementById("micButton");
    mic.classList.remove("recording");
}


// SPEECH CONTROL BUTTONS

function pauseSpeech() {
    window.speechSynthesis.pause();
}

function resumeSpeech() {
    window.speechSynthesis.resume();
}

function stopSpeech() {
    window.speechSynthesis.cancel();
}

function startVoiceLogin() {

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech recognition not supported in this browser");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.maxAlternatives = 2;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.start();

    recognition.onresult = function (event) {

        const transcript = event.results[0][0].transcript
            .toLowerCase()
            .trim();

        if (transcript.includes("login") || transcript.includes("log in")) {

            window.location.href = "/login/oauth";

        } else {

            alert("Please say login to continue");

        }
    };

    recognition.onerror = function () {
        alert("Microphone error");
    };
}