
# CMPSC 431W Project Phase 2: NittanyMarket - README

**Name:** Yihua Yang  
**Date:** 4/26/2022

## Introduction
This project contains HTML and Python files related to the second phase of the CMPSC 431W project. The key files include:

### HTML Files (14 files)
- `categoryHierarchy.html`
- `checkingInfo.html`
- `Delete_patient.html`
- `fail.html`
- `index.html`
- `input.html`
- `login.html`
- `Main_webpage.html`
- `placeOrder.html`
- `publishProductListing.html`
- `searching.html`
- `shoppingCart.html`
- `success.html`
- `viewOrders.html`

### Python Files
- `app.py`
- `Create_Insert.ipynb`

Other files in the submission are not critical to this phase and are not explained.

## File Descriptions

### `Create_Insert.ipynb`
- Creates database tables and populates them with data.
- Handles user password hashing, data insertion for `Categories`, and shopping cart creation.

### `app.py`
- Adapts from Phase 1 and provides key functionalities for Phase 2.
- Handles user login, shopping cart management, product listings, and order placement.
- Key functions include:
  - `index()`: Displays the main page.
  - `login()`: Manages user login and authentication.
  - `getInfo()`: Retrieves user information.
  - `categoryHierarchy()`: Handles category browsing and product searching.
  - `placeOrderHTML()`: Manages product purchases.
  - `viewOrder()`: Displays order history.
  - Extra features: shopping cart, password change, product listing management.

## Extra Credit Functions
- `placeOrder`
- `viewOrder`
- `searching`
- `shoppingCart`

## NOTE: Database Assumptions

**This project assumes the database connection information is as follows: the MySQL server is hosted on `localhost`, with `root` as the username and `admin` as the password. Additionally, the project will connect to a database named `phase2`, which is automatically created if it does not already exist. The code initializes the database connection and ensures that the necessary database is available for operations. Ensure that the MySQL server is running locally with these credentials, or modify the connection parameters accordingly.**


For further details, refer to the comments in the `app.py` and `Create_Insert.ipynb` files.

Thank you for reading!
