# Little Lemon API

REST API for the Little Lemon restaurant, built with Django + Django REST Framework. Lets customers, delivery crew, and managers browse the menu, manage carts, place orders, and handle order delivery.

> Capstone project for the **APIs** course (Meta Back-End Developer, Coursera).

---

## Stack

- Django 4.1
- Django REST Framework
- Djoser (user registration + token authentication)
- SQLite (development)
- pipenv (virtual environment management)

---

## Setup and run

```bash
pipenv install
pipenv shell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API available at `http://127.0.0.1:8000/api/`.

---

## User roles

| Role | How it's assigned | Permissions |
|---|---|---|
| **Admin** | `is_staff=True` / superuser (Django admin panel) | Full access, equivalent to Manager on every endpoint |
| **Manager** | belongs to the `Manager` group | Manages menu, groups, and all orders |
| **Delivery crew** | belongs to the `Delivery crew` group | Sees and updates only the orders assigned to them |
| **Customer** | authenticated user with no group assigned | Browses the menu, manages their own cart and orders |

Groups are created and assigned from the Django admin panel (`/admin/`).

---

## Authentication

All calls (except the ones marked public) require the header:

```
Authorization: Token <your_token>
```

The token is obtained by logging in (see the Djoser section below).

### Test users

> Credentials for a local development environment (SQLite). Do not use in production or reuse these passwords outside this project.
>
> Tokens are not listed here: everyone should log in (`POST /api/token/login/`) with their username and password, and **save the token** the API returns, for use in the `Authorization: Token <your_token>` header on every other call.

**Admin**

| Username | Email | Password |
|---|---|---|
| admin | admin@littlelemon.com | lemon@789 |

**Manager**

| Username | Email | Password |
|---|---|---|
| yeimmy | yeimmy@littlelemon.com | lemon@yeii |
| Adrian | adrian@littlelemon.com | lemon@adr |

**Delivery crew**

| Username | Email | Password |
|---|---|---|
| Gaston | gaston@littlelemon.com | lemon@gas |
| Mario | mario@littlelemon.com | lemon@mar! |

**Customers**

| Username | Email | Password |
|---|---|---|
| Elena | elena@littlelemon.com | lemon@ele |
| Sana | sana@littlelemon.com | lemon@san! |
| Hana | hana@littlelemon.com | lemon@han |

---

## Status codes

| Code | Reason |
|---|---|
| 200 OK | Successful GET, PUT, PATCH, DELETE |
| 201 Created | Successful POST |
| 400 Bad Request | Validation failed |
| 401 Unauthorized | Missing authentication or invalid token |
| 403 Forbidden | Authenticated user without permission for the action |
| 404 Not Found | Resource does not exist |
| 429 Too Many Requests | Throttling limit exceeded |

---

## Endpoints

### Users and tokens (Djoser) — prefix `/api/`

| Endpoint | Role | Method | Description |
|---|---|---|---|
| `/api/users/` | public | GET | List users (paginated: `?page=2`) |
| `/api/users/` | public | POST | Create a new user |
| `/api/users/` | authenticated user | DELETE | Delete own account |
| `/api/users/me/` | valid token | GET/PUT/PATCH/DELETE | Current user's profile |
| `/api/users/{id}/` | admin or owner | GET/PUT/PATCH/DELETE | User by id |
| `/api/token/login/` | valid username/password | POST | Generates an access token |
| `/api/token/logout/` | valid token | POST | Invalidates the current token |

**Create user**
```json
POST /api/users/
{
  "username": "name",
  "password": "password",
  "email": "email"
}
```

**Delete user**
```json
DELETE /api/users/
{
  "current_password": "current_password"
}
```

**Login**
```json
POST /api/token/login/
{
  "username": "username",
  "password": "password"
}
```

**Logout**: send the token in the `Authorization` header, no body.

---

### Categories

| Endpoint | Role | Method | Description |
|---|---|---|---|
| `/api/categories/` | public | GET | List categories |
| `/api/categories/` | admin / manager | POST | Create a category |

---

### Menu (`/api/menu-items/`)

| Endpoint | Role | Method | Description |
|---|---|---|---|
| `/api/menu-items/` | customer, delivery crew | GET | List all items |
| `/api/menu-items/` | customer, delivery crew | POST/PUT/PATCH/DELETE | 403 Forbidden |
| `/api/menu-items/` | manager/admin | GET | List all items |
| `/api/menu-items/` | manager/admin | POST | Create item, 201 Created |
| `/api/menu-items/{id}/` | customer, delivery crew | GET | Single item detail |
| `/api/menu-items/{id}/` | customer, delivery crew | POST/PUT/PATCH/DELETE | 403 Forbidden |
| `/api/menu-items/{id}/` | manager/admin | GET/PUT/PATCH | Read / update item |
| `/api/menu-items/{id}/` | manager/admin | DELETE | Delete item |

**Create / update item**
```json
POST /api/menu-items/
{
  "title": "name",
  "price": "10.00",
  "featured": false,
  "category_id": 1
}
```

**Filtering, ordering, and pagination** (all optional, combinable):
```
GET /api/menu-items/?search=pizza
GET /api/menu-items/?ordering=price
GET /api/menu-items/?ordering=-price
GET /api/menu-items/?page=2
```

---

### Groups — role management (manager/admin only)

| Endpoint | Method | Description |
|---|---|---|
| `/api/groups/manager/users/` | GET | List users in the Manager group |
| `/api/groups/manager/users/` | POST | Add user to the Manager group, 201 Created |
| `/api/groups/manager/users/{id}/` | DELETE | Remove the user from the group (does not delete the account). 404 if not a member |
| `/api/groups/delivery-crew/users/` | GET | List users in the Delivery crew group |
| `/api/groups/delivery-crew/users/` | POST | Add user to the Delivery crew group, 201 Created |
| `/api/groups/delivery-crew/users/{id}/` | DELETE | Remove the user from the group. 404 if not a member |

**Add user to a group**
```json
POST /api/groups/manager/users/
{
  "username": "user_name"
}
```

---

### Cart (authenticated customer)

| Endpoint | Method | Description |
|---|---|---|
| `/api/cart/menu-items/` | GET | Current items in the user's cart |
| `/api/cart/menu-items/` | POST | Add item to the cart |
| `/api/cart/menu-items/` | DELETE | Empty the user's entire cart |
| `/api/cart/menu-items/{menuitem_id}/` | DELETE | Remove a specific item from the cart |

**Add to cart**
```json
POST /api/cart/menu-items/
{
  "menuitem_id": 1,
  "quantity": 2
}
```

---

### Orders

| Endpoint | Role | Method | Description |
|---|---|---|---|
| `/api/orders/` | customer | GET | Their own orders |
| `/api/orders/` | customer | POST | Creates an order from the current cart (empties the cart) |
| `/api/orders/` | manager/admin | GET | All orders |
| `/api/orders/` | delivery crew | GET | Orders assigned to them |
| `/api/orders/{id}/` | owning customer | GET | Order detail. Errors if it's not theirs |
| `/api/orders/{id}/` | manager/admin | PUT/PATCH | Assigns `delivery_crew` and/or changes `status` (0 = ready for delivery, 1 = delivered) |
| `/api/orders/{id}/` | delivery crew | PATCH | Can only change `status`, nothing else |
| `/api/orders/{id}/` | manager/admin | DELETE | Deletes the order |

**Create order** (uses whatever is in the user's cart):
```json
POST /api/orders/
{}
```

**Manager assigns delivery crew and marks ready for delivery**
```json
PATCH /api/orders/{id}/
{
  "delivery_crew": 5,
  "status": 0
}
```

**Delivery crew marks as delivered**
```json
PATCH /api/orders/{id}/
{
  "status": 1
}
```

**Filtering, ordering, and pagination**: same as menu (`?ordering=`, `?page=`, page size 5).

---

## Throttling

| User type | Limit |
|---|---|
| Anonymous | 2 requests / minute |
| Authenticated | 10 requests / minute |

Exceeding the limit returns `429 Too Many Requests`.

---

## Tests

```bash
python manage.py test LittleLemonAPI
```
