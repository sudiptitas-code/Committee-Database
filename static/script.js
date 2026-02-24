const box = document.getElementById('searchBox');
const tbody = document.querySelector('#results tbody');

box.addEventListener('keyup', async () => {
    const q = box.value.trim();
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Searching...</td></tr>';

    if (!q) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Start typing to search...</td></tr>';
        return;
    }

    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();

        if (!data.results.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No results found</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        data.results.forEach(row => {
            const members = [row.member1, row.member2, row.member3, row.secretary].filter(Boolean).join(', ');

            tbody.innerHTML += `
                <tr>
                    <td>${row.reference_no}</td>
                    <td>${row.subject}</td>
                    <td>${row.date}</td>
                    <td>${row.convener}</td>
                    <td>${members}</td>
                    <td>
                        <div class="d-flex gap-2">
                            <a href="/edit/${row.id}" class="btn btn-warning btn-sm">✏ Edit</a>
                            <form method="POST" action="/delete/${row.id}" style="display:inline;">
                                <button type="submit" onclick="return confirm('Are you sure?')" class="btn btn-danger btn-sm">🗑 Delete</button>
                            </form>
                        </div>
                    </td>
                </tr>
            `;
        });

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center">Error fetching results</td></tr>`;
        console.error(err);
    }
});