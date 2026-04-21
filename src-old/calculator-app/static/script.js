async function calculate() {
    const num1 = document.getElementById("num1").value;
    const num2 = document.getElementById("num2").value;
    const operation = document.getElementById("operation").value;

    const response = await fetch('/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num1, num2, operation })
    });

    const data = await response.json();
    document.getElementById("result").innerText = "Result: " + data.result;

    loadHistory();
}

async function loadHistory() {
    const response = await fetch('/history');
    const data = await response.json();

    const historyList = document.getElementById("history");
    historyList.innerHTML = "";

    data.forEach(item => {
        const li = document.createElement("li");
        li.innerText = `${item.num1} ${item.operation} ${item.num2} = ${item.result}`;
        historyList.appendChild(li);
    });
}

// Load history on page load
loadHistory();