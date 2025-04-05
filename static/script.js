document.getElementById('searchForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (query) {
        fetch('/search?q=' + query)
            .then(response => response.json())
            .then(data => {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = ''; // Clear previous results

                if (data.results) {
                    data.results.forEach(result => {
                        const careerCard = document.createElement('div');
                        careerCard.classList.add('career-card');
                        careerCard.innerHTML = `
                            <h2>${result.name}</h2>
                            <p><strong>Course Required:</strong> ${result.course_required}</p>
                            <p><strong>Skills Required:</strong> ${result.skills_required}</p>
                            <p><strong>Related Jobs:</strong> ${result.related_jobs}</p>
                            <p>${result.description}</p>
                        `;
                        resultsDiv.appendChild(careerCard);
                    });
                } else if (data.message) {
                    const message = document.createElement('p');
                    message.textContent = data.message;
                    resultsDiv.appendChild(message);
                }
            })
            .catch(error => console.error('Error:', error));
    }
});
