const searchBox = document.getElementById("searchBox");

if (searchBox) {
    searchBox.addEventListener("keyup", function () {
        fetch("/api/search?q=" + this.value)
            .then(response => response.json())
            .then(data => {

                let html = "";

                if (data.length === 0) {
                    html = `
                        <div class="alert alert-info text-center">
                            No matching committees found
                        </div>
                    `;
                } else {

                    data.forEach(item => {
                        html += `
                        <div class="card mb-4 shadow border-0 committee-card">
                            <div class="card-body">

                                <h4 class="fw-bold text-primary">
                                    ${item.subject}
                                </h4>

                                <div class="row mt-3">

                                    <div class="col-md-6">
                                        <p><strong>Reference No:</strong> ${item.reference_no || '-'}</p>
                                        <p><strong>Date:</strong> ${item.date || '-'}</p>
                                        <p><strong>Convener:</strong> ${item.convener || '-'}</p>
                                        <p><strong>Secretary:</strong> ${item.secretary || '-'}</p>
                                    </div>

                                    <div class="col-md-6">
                                        <p><strong>Member 1:</strong> ${item.member1 || '-'}</p>
                                        <p><strong>Member 2:</strong> ${item.member2 || '-'}</p>
                                        <p><strong>Member 3:</strong> ${item.member3 || '-'}</p>
                                    </div>

                                </div>

                                <div class="mt-3">
                                    <a href="/edit/${item.id}" class="btn btn-warning btn-sm me-2">
                                        ✏ Edit
                                    </a>

                                    <form action="/delete/${item.id}" method="POST"
                                          style="display:inline;">
                                        <button class="btn btn-danger btn-sm">
                                            🗑 Delete
                                        </button>
                                    </form>
                                </div>

                            </div>
                        </div>
                        `;
                    });
                }

                document.getElementById("results").innerHTML = html;
            });
    });
}