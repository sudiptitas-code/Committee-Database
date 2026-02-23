const box = document.getElementById('searchBox');
const tbody = document.querySelector('#results tbody');

box.addEventListener('keyup', async () => {
    const q = box.value;
    const res = await fetch(`/api/search?q=${q}`);
    const data = await res.json();

    tbody.innerHTML = '';

    if(data.length === 0){
        tbody.innerHTML = '<tr><td colspan="8">No results found</td></tr>';
        return;
    }

    data.forEach(row => {
        tbody.innerHTML += `
        <tr>
            <td>${row['Committee Subject']}</td>
            <td>${row['Reference No']}</td>
            <td>${row['Date']}</td>
            <td>${row['Convener']}</td>
            <td>${row['Member-1']}</td>
            <td>${row['Member-2']}</td>
            <td>${row['Member-3']}</td>
            <td>${row['Member Secretary']}</td>
        </tr>`;
    });
});