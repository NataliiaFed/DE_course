/*
 Завдання на SQL до лекції 03.
 */


/*
1.
Вивести кількість фільмів в кожній категорії.
Результат відсортувати за спаданням.
*/
SELECT
    category_id,
    COUNT(film_category.film_id) AS film_count
FROM film_category
GROUP BY
    category_id
ORDER BY
    film_count DESC;


/*
2.
Вивести 10 акторів, чиї фільми брали на прокат найбільше.
Результат відсортувати за спаданням.
*/
-- count how many times each film was rented
WITH film_rental_count AS (
    SELECT
        inventory.film_id,
        COUNT(rental.rental_id) AS rental_count
    FROM rental
    JOIN inventory
        ON rental.inventory_id = inventory.inventory_id
    GROUP BY
        inventory.film_id
)
-- aggregate rental counts for each actor across all their films and select of top 10 most rented actors
SELECT
    film_actor.actor_id,
    SUM(film_rental_count.rental_count) AS total_rentals
FROM film_rental_count
JOIN film_actor
    ON film_actor.film_id = film_rental_count.film_id
GROUP BY
    film_actor.actor_id
ORDER BY
    total_rentals DESC
LIMIT 10;



/*
3.
Вивести категорія фільмів, на яку було витрачено найбільше грошей
в прокаті
*/
SELECT
    film_category.category_id
FROM rental
JOIN payment
    ON rental.rental_id = payment.rental_id
JOIN inventory
    ON rental.inventory_id = inventory.inventory_id
JOIN film_category
    ON inventory.film_id = film_category.film_id
GROUP BY film_category.category_id
ORDER BY SUM(payment.amount) DESC
LIMIT 1;


/*
4.
Вивести назви фільмів, яких не має в inventory.
Запит має бути без оператора IN
*/
SELECT
    film.title
FROM film
LEFT JOIN inventory
    ON film.film_id = inventory.film_id
WHERE
    inventory.inventory_id IS NULL;

/*
5.
Вивести топ 3 актори, які найбільше зʼявлялись в категорії фільмів “Children”.
*/
SELECT
    film_actor.actor_id
FROM film_category
JOIN category
    ON film_category.category_id = category.category_id
JOIN film_actor
    ON film_actor.film_id = film_category.film_id
WHERE category.name = 'Children'
GROUP BY film_actor.actor_id
ORDER BY COUNT(film_category.film_id) DESC
LIMIT 3;
