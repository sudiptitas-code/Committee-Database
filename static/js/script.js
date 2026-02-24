const searchBox = document.getElementById('searchBox');
const resultsContainer = document.getElementById('resultsContainer');

if (searchBox) {
    searchBox.addEventListener('input', async () => {
        const query = searchBox.value.trim();

        if (!query) {
            resultsContainer.innerHTML = '';
            return;
        }

        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (data.length === 0) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">No results found.</div>`;
            return;
        }

        let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead class="table-dark">
                    <tr>
                        <th>Ref No</th>
                        <th>Subject</th>
                        <th>Date</th>
                        <th>Convener</th>
                        <th>Members</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>`;

        data.forEach(row => {
            tableHTML += `
            <tr>
                <td>${row.reference_no}</td>
                <td>${row.subject}</td>
                <td>${row.date}</td>
                <td>${row.convener}</td>
                <td>${row.member1}, ${row.member2}, ${row.member3}, ${row.secretary}</td>
                <td>
                    <a href="/edit/${row.id}" class="btn btn-warning btn-sm">Edit</a>
                    <form method="POST" action="/delete/${row.id}" class="d-inline" onsubmit="return confirm('Are you sure?');">
                        <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                    </form>
                </td>
            </tr>`;
        });

        tableHTML += `</tbody></table></div>`;
        resultsContainer.innerHTML = tableHTML;
    });
}