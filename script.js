function sendMessage() {
    let userInput = document.getElementById("user-input").value;
    let chatBox = document.getElementById("chat-box");

    if (userInput.trim() === "") return;

    displayMessage(chatBox, userInput, "user-message");
    document.getElementById("user-input").value = "";

    // Extract departure, destination, and date from user input
    fetch("/get_response", {
        method: "POST",
        body: JSON.stringify({ message: userInput }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.departure && data.destination && data.date) {
            getAirportCodes(data.departure, data.destination, data.date, chatBox);
        } else {
            displayMessage(chatBox, "I couldn't extract flight details. Please try again.", "bot-message");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        displayMessage(chatBox, "An error occurred while processing your request.", "bot-message");
    });
}

function getAirportCodes(departure, destination, date, chatBox) {
    fetch(`/get_airport_codes?departure=${encodeURIComponent(departure)}&destination=${encodeURIComponent(destination)}`)
    .then(response => response.json())
    .then(data => {
        if (data.origin && data.destination) {
            fetchFlights(
                data.origin.code,
                data.destination.code,
                data.origin.entityId,
                data.destination.entityId,
                date,
                data.origin.currency,
                data.origin.market,
                data.origin.countryCode,
                chatBox
            );
        } else {
            displayMessage(chatBox, "I couldn't find airport codes for these cities.", "bot-message");
        }
    })
    .catch(error => {
        console.error("Error fetching airport codes:", error);
        displayMessage(chatBox, "An error occurred while fetching airport codes.", "bot-message");
    });
}

function fetchFlights(origin, destination, originEntityId, destinationEntityId, date, currency, market, countryCode, chatBox) {
    // Set default values if any parameter is missing
    currency = currency || "USD";  // Default to USD
    market = market || "en-US";    // Default to English market
    countryCode = countryCode || "US"; // Default to United States

    console.log(`📡 Fetching flights with:
    Origin: ${origin}, Destination: ${destination},
    Origin Entity ID: ${originEntityId}, Destination Entity ID: ${destinationEntityId},
    Date: ${date}, Currency: ${currency}, Market: ${market}, Country: ${countryCode}`);

    fetch(`/get_flight?origin=${origin}&destination=${destination}&originEntityId=${originEntityId}&destinationEntityId=${destinationEntityId}&date=${date}&currency=${currency}&market=${market}&countryCode=${countryCode}`)
    .then(response => response.json())
    .then(data => {
        console.log("🚀 Flight Search Response:", data);
        if (data.error) {
            displayMessage(chatBox, "No flights found.", "bot-message");
        } else {
            displayMessage(chatBox, `Found flights: ${JSON.stringify(data)}`, "bot-message");
        }
    })
    .catch(error => {
        console.error("❌ Error fetching flights:", error);
        displayMessage(chatBox, "An error occurred while fetching flight information.", "bot-message");
    });
}


function displayMessage(chatBox, message, className) {
    let messageElement = document.createElement("div");
    messageElement.className = className;
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}
