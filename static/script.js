const searchBox = document.getElementById("searchBox");

if (searchBox) {
    searchBox.addEventListener("keyup", function() {
        fetch("/api/search?q=" + this.value)
            .then(response => response.json())
            .then(data => {
                let html = "";
                data.forEach(item => {
                    html += `
                    <div class="card mb-2">
                        <div class="card-body">
                            <h5>${item.subject}</h5>
                            <p>Reference: ${item.reference_no}</p>
                            <a href="/edit/${item.id}" class="btn btn-warning btn-sm">Edit</a>
                            <form action="/delete/${item.id}" method="POST" style="display:inline;">
                                <button class="btn btn-danger btn-sm">Delete</button>
                            </form>
                        </div>
                    </div>`;
                });
                document.getElementById("results").innerHTML = html;
            });
    });
}