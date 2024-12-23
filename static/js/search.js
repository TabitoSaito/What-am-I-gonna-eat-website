document.getElementById('searchBar').addEventListener('input', function () {
    const filter = this.value.toLowerCase();
    const dishes = document.querySelectorAll('#dishList .dish');

    dishes.forEach(dish => {
        const dishNameElement = dish.querySelector('.dish-name');
        if (dishNameElement) {
            const dishName = dishNameElement.textContent.toLowerCase();
            if (dishName.includes(filter)) {
                dish.style.display = ''; // Show the dish
            } else {
                dish.style.display = 'none'; // Hide the dish
            }
        } else {
            console.warn('No .dish-name found in:', dish); // Warn if .dish-name is missing
        }
    });
});
