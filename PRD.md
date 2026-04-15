# Product Requirements Document (PRD) - Kopmasshop

## 1. Project Overview

**Project Name:** Kopmasshop  
**Project Type:** E-Commerce Platform  
**Core Functionality:** A multi-vendor e-commerce platform enabling buyers to browse products, add to cart, checkout with multiple payment methods, and sellers to manage their online stores. Includes a comprehensive admin panel for platform management.  
**Target Users:**
- **Buyers:** Online shoppers looking to purchase products
- **Sellers:** Small business owners and retailers wanting to sell products online
- **Administrators:** Platform managers overseeing the entire e-commerce ecosystem

---

## 2. Technology Stack Analysis

### 2.1 Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Django** | >=5.0, <5.1 | Full-stack web framework |
| **Python** | 3.x | Programming language |
| **PostgreSQL** | - | Primary relational database |
| **psycopg2-binary** | >=2.9.9 | PostgreSQL adapter for Django |

### 2.2 Frontend

| Technology | Purpose |
|------------|---------|
| **Bootstrap 5** | UI framework for responsive design |
| **Tailwind CSS** | Utility-first CSS framework (custom build) |
| **Chart.js** | Data visualization for admin dashboard |
| **HTML5/CSS3** | Frontend markup and styling |
| **JavaScript (ES6+)** | Client-side interactivity |

### 2.3 Authentication & Security

| Technology | Purpose |
|------------|---------|
| **django-allauth** | OAuth2/social authentication (Google) |
| **PyJWT** | JWT token generation and validation |
| **Custom OTP System** | Email-based OTP for verification |

### 2.4 Payment Integration

| Technology | Purpose |
|------------|---------|
| **Midtrans** | Payment gateway (credit card, e-wallet, etc.) |
| **Bank Transfer** | Manual bank transfer method |
| **COD (Cash on Delivery)** | Cash on delivery payment option |

### 2.5 Deployment & DevOps

| Technology | Purpose |
|------------|---------|
| **Gunicorn** | WSGI HTTP server |
| **Whitenoise** | Static file serving for production |
| **python-dotenv** | Environment variable management |

### 2.6 Additional Libraries

| Library | Purpose |
|---------|---------|
| **Pillow** | Image processing |
| **django-widget-tweaks** | Form template helpers |
| **requests** | HTTP client |
| **pytest/pytest-django** | Testing framework |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Browser   │  │ Mobile App  │  │   Desktop   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼───────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      WEB SERVER LAYER                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Django Application (Gunicorn)              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │   │
│  │  │ Landing App  │  │  Admin Panel │  │  REST API │  │   │
│  │  │  (Storefront)│  │   (Dashboard)│  │           │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────┬─────────────┘
          │                                    │
          ▼                                    ▼
┌──────────────────────┐        ┌──────────────────────────────┐
│   MIDTRANS API       │        │       EXTERNAL SERVICES      │
│   (Payment Gateway)  │        │  ┌────────────────────────┐  │
└──────────────────────┘        │  │   Google OAuth         │  │
                                 │  │   (Social Login)       │  │
                                 │  └────────────────────────┘  │
                                 │  ┌────────────────────────┐  │
                                 │  │   SMTP Email Service   │  │
                                 │  │   (Mailtrap/Production)│  │
                                 │  └────────────────────────┘  │
                                 └──────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 PostgreSQL Database                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │   │
│  │  │ Users  │ │Products│ │ Orders │ │  Payments  │  │   │
│  │  └────────┘ └────────┘ └────────┘ └────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Feature Specification

### 4.1 User Management

#### Registration & Authentication
- [x] Email-based registration with password
- [x] Social login via Google OAuth
- [x] JWT-based API authentication
- [x] OTP email verification
- [x] Password reset via OTP
- [x] Login rate limiting (max 5 attempts per 60 seconds)

#### User Roles
| Role | Description |
|------|-------------|
| **Admin** | Full platform access, user management, global settings |
| **Seller** | Can manage own products and orders |
| **Buyer** | Can browse, purchase, and review products |

#### User Profile
- [x] Avatar upload
- [x] Phone number
- [x] Store information (for sellers)
- [x] Account verification status
- [x] Suspension management

### 4.2 Product Management

#### Category System
- [x] Hierarchical categories (parent/child)
- [x] Category images
- [x] Active/inactive status
- [x] Category tagging/description

#### Product Catalog
- [x] Product CRUD operations
- [x] Multiple product images (main + gallery)
- [x] Price and discount pricing
- [x] Stock management
- [x] SKU generation
- [x] Product status (active/inactive/out_of_stock)
- [x] Featured products
- [x] Product weight for shipping calculation
- [x] Product views and sales tracking
- [x] Product search and filtering

### 4.3 Shopping Cart

- [x] Add to cart functionality
- [x] Update quantity
- [x] Remove items
- [x] Cart persistence (logged in + session-based)
- [x] Price calculation with discounts

### 4.4 Checkout & Orders

#### Checkout Process
- [x] Address selection/entry
- [x] Shipping cost calculation
- [x] Order summary
- [x] Payment method selection

#### Order Management
| Status | Description |
|--------|-------------|
| pending | Order created, awaiting payment |
| confirmed | Payment confirmed |
| processing | Order being prepared |
| shipped | Order dispatched |
| delivered | Order received by customer |
| cancelled | Order cancelled |
| refunded | Payment refunded |

#### Order Features
- [x] Unique order number generation (ORD{date}{unique_id})
- [x] Order tracking (courier, tracking number)
- [x] Order notes
- [x] Order history for buyers
- [x] Seller order management

### 4.5 Payment System

#### Payment Methods
| Method | Description |
|--------|-------------|
| **Midtrans** | Online payment gateway (credit card, BCA KlikPay, GoPay, etc.) |
| **Bank Transfer** | Manual transfer to designated bank account |
| **COD** | Cash on delivery |

#### Payment Flow
1. Buyer selects payment method
2. For Midtrans: Redirect to payment gateway, webhook updates order status
3. For Bank Transfer: Display bank details, manual confirmation
4. For COD: Order marked for COD collection

### 4.6 Reviews & Ratings

- [x] Product rating (1-5 stars)
- [x] Text review with images
- [x] Review approval system
- [x] Only verified purchasers can review

### 4.7 Address Management

- [x] Multiple addresses per user
- [x] Address labels (Home, Office, etc.)
- [x] Default address selection
- [x] Full address details (name, phone, city, province, postal code)

### 4.8 Admin Dashboard

#### Global Dashboard
- [x] Platform overview statistics
- [x] Sales reports
- [x] User statistics
- [x] Recent orders

#### Seller Dashboard
- [x] Personal sales statistics
- [x] Product management
- [x] Order management
- [x] Store settings

#### Admin Features
- [x] User management (view, suspend, activate)
- [x] All products management
- [x] All orders management
- [x] Sales reports
- [x] Product reports
- [x] User reports
- [x] Platform settings

---

## 5. Data Models

### 5.1 Core Entities

```
User
├── id (PK)
├── username
├── email
├── password
├── role (admin/seller/buyer)
├── phone
├── avatar
├── is_verified
├── is_suspended
├── store_name
├── store_description
├── store_logo
├── created_at
└── updated_at

Category
├── id (PK)
├── name
├── slug
├── tagline
├── description
├── image
├── parent (FK to Category)
├── is_active
└── created_at

Product
├── id (PK)
├── seller (FK to User)
├── category (FK to Category)
├── name
├── slug
├── description
├── price
├── discount_price
├── stock
├── weight
├── sku
├── status
├── is_featured
├── views_count
├── sales_count
├── created_at
└── updated_at

ProductImage
├── id (PK)
├── product (FK to Product)
├── image
├── is_main
├── alt_text
└── created_at

Address
├── id (PK)
├── user (FK to User)
├── label
├── recipient_name
├── recipient_phone
├── address
├── city
├── province
├── postal_code
├── is_default
└── created_at
```

### 5.2 Order Entities

```
Order
├── id (PK)
├── order_number (unique)
├── buyer (FK to User)
├── seller (FK to User)
├── status
├── payment_status
├── shipping_address
├── shipping_city
├── shipping_province
├── shipping_postal_code
├── recipient_name
├── recipient_phone
├── subtotal
├── shipping_cost
├── discount
├── total
├── tracking_number
├── courier
├── notes
├── created_at
├── updated_at
├── paid_at
├── shipped_at
└── delivered_at

OrderItem
├── id (PK)
├── order (FK to Order)
├── product (FK to Product)
├── product_name
├── product_image
├── quantity
├── price
└── total

Payment
├── id (PK)
├── order (FK to Order)
├── payment_method
├── amount
├── status
├── transaction_id
├── payment_url
├── paid_at
└── created_at
```

### 5.3 Review & Cart

```
Review
├── id (PK)
├── product (FK to Product)
├── user (FK to User)
├── order (FK to Order)
├── rating
├── comment
├── is_approved
└── created_at

ReviewImage
├── id (PK)
├── image
└── created_at

Cart
├── id (PK)
├── user (FK to User)
├── session_id
├── created_at
└── updated_at

CartItem
├── id (PK)
├── cart (FK to Cart)
├── product (FK to Product)
├── quantity
└── created_at
```

---

## 6. API Endpoints

### 6.1 Authentication API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/api/login/` | Login with JWT |
| POST | `/auth/api/otp/send/` | Send OTP email |
| POST | `/auth/api/otp/verify/` | Verify OTP |
| POST | `/auth/api/password-reset/request/` | Request password reset |
| POST | `/auth/api/password-reset/confirm/` | Confirm password reset |

### 6.2 Storefront API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/products/` | Product listing |
| GET | `/products/<slug>/` | Product detail |
| GET | `/cart/` | View cart |
| POST | `/cart/add/` | Add to cart |
| PUT | `/cart/update/` | Update cart item |
| DELETE | `/cart/remove/<item_id>/` | Remove cart item |
| GET | `/checkout/` | Checkout page |
| POST | `/orders/create/` | Create order |
| GET | `/orders/` | Order history |
| GET | `/orders/<id>/` | Order detail |
| GET | `/profile/` | User profile |
| POST | `/profile/address/` | Add address |

### 6.3 Admin Dashboard API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/` | Admin dashboard |
| GET | `/dashboard/seller/` | Seller dashboard |
| GET | `/dashboard/products/` | Product management |
| GET | `/dashboard/orders/` | Order management |
| GET | `/dashboard/users/` | User management |
| GET | `/dashboard/reports/` | Sales reports |

---

## 7. Security Features

- [x] CSRF protection
- [x] X-Frame-Options header
- [x] SQL injection prevention (Django ORM)
- [x] XSS prevention (Django template auto-escaping)
- [x] Password validation (length, common passwords, numeric)
- [x] Rate limiting on login attempts
- [x] JWT token expiration (15 min access, 7 days refresh)
- [x] Email verification enforcement middleware

---

## 8. Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DB_NAME | PostgreSQL database name | kopmasshop_db |
| DB_USER | Database username | postgres |
| DB_PASSWORD | Database password | - |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |
| SECRET_KEY | Django secret key | - |
| DEBUG | Debug mode | True |
| ALLOWED_HOSTS | Allowed hosts | localhost,127.0.0.1 |
| EMAIL_HOST | SMTP host | sandbox.smtp.mailtrap.io |
| EMAIL_PORT | SMTP port | 2525 |
| MIDTRANS_SERVER_KEY | Midtrans server key | - |
| MIDTRANS_CLIENT_KEY | Midtrans client key | - |
| MIDTRANS_IS_PRODUCTION | Production mode | False |
| JWT_SECRET_KEY | JWT secret key | - |
| JWT_ALGORITHM | JWT algorithm | HS256 |

---

## 9. Project Structure

```
kopmasshop-backend/
├── config/                    # Django configuration
│   ├── settings.py           # Main settings
│   ├── urls.py               # URL routing
│   ├── asgi.py               # ASGI config
│   └── wsgi.py               # WSGI config
├── landing_app/              # Storefront application
│   ├── views/                # View functions
│   │   ├── home_views.py
│   │   ├── product_list_views.py
│   │   ├── product_detail_views.py
│   │   ├── cart_views.py
│   │   ├── checkout_views.py
│   │   ├── order_create_views.py
│   │   ├── order_history_views.py
│   │   ├── auth_login_views.py
│   │   ├── auth_register_views.py
│   │   └── ...
│   ├── urls.py
│   └── context_processors.py
├── panel_admin/              # Admin & Seller panel
│   ├── models.py            # Database models
│   ├── views/               # Admin views
│   ├── services/           # Business logic
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   └── ...
│   ├── middleware/          # Custom middleware
│   ├── permissions.py       # Permission classes
│   └── admin.py            # Django admin config
├── static/                  # Static files
│   └── dashboard/
│       └── assets/
│           ├── css/
│           ├── images/
│           └── src/
├── templates/               # HTML templates
├── manage.py               # Django management
├── requirements.txt        # Python dependencies
└── .env.example            # Environment template
```

---

## 10. Future Enhancements

Based on the current implementation, potential future enhancements could include:

1. **Multi-vendor marketplace** - Multiple sellers per order
2. **Product variants** - Size, color, etc.
3. **Coupon/Discount codes** - Promotional codes
4. **Email notifications** - Order status updates
5. **SMS notifications** - OTP via SMS
6. **Inventory alerts** - Low stock notifications
7. **Analytics dashboard** - Advanced reporting
8. **Mobile API** - RESTful API for mobile apps
9. **WebSocket notifications** - Real-time order updates
10. **Shipping integration** - Multiple courier services (JNE, Tiki, etc.)

---

## 11. Acceptance Criteria

### Buyer Features
- [ ] User can register with email and password
- [ ] User can login via email or Google OAuth
- [ ] User can browse products by category
- [ ] User can search products by name
- [ ] User can view product details
- [ ] User can add products to cart
- [ ] User can update cart quantities
- [ ] User can remove items from cart
- [ ] User can checkout with address selection
- [ ] User can pay via Midtrans
- [ ] User can pay via bank transfer
- [ ] User can select COD payment
- [ ] User can view order history
- [ ] User can add/edit addresses
- [ ] User can write product reviews

### Seller Features
- [ ] Seller can manage products (CRUD)
- [ ] Seller can view orders
- [ ] Seller can update order status
- [ ] Seller can view sales reports
- [ ] Seller can manage store profile

### Admin Features
- [ ] Admin can view dashboard
- [ ] Admin can manage all users
- [ ] Admin can suspend/activate users
- [ ] Admin can manage all products
- [ ] Admin can manage all orders
- [ ] Admin can view sales reports
- [ ] Admin can view product reports
- [ ] Admin can view user reports

---

*Document Version: 1.0*  
*Generated: March 2026*  
*Project: Kopmasshop E-Commerce Platform*
