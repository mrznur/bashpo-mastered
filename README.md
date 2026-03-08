# Bashpo - Gaming Marketplace

A modern gaming platform built with Flask and Tailwind CSS. Buy, sell, and manage games with a clean Twitch-inspired design.

## Quick Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit: **https://bashpo-mastered.onrender.com/**

## Demo Accounts

**Admin**
- Username: `LordGaben`
- Password: `123456`

**Buyer**
- Username: `faiyaz`
- Password: `123456`

## Features

### Buyers
- Browse and search games
- Shopping cart and wishlist
- Wallet system (credit card, gift cards)
- Reviews and ratings
- Friend system
- Game library and downloads

### Developers
- Upload and publish games
- Revenue tracking
- Generate activation keys
- Manage sales and discounts

### Admins
- Approve game submissions
- User management
- Generate gift cards
- Platform analytics

## Tech Stack

- **Backend:** Flask + SQLite
- **Frontend:** HTML, Tailwind CSS, DaisyUI, JavaScript
- **Payment:** SSLCommerz integration

## Project Structure

```
bashpo/
├── app.py                      # Main application
├── model/
│   ├── req_auth.py            # Auth & database
│   └── route_help.py          # Helper functions
├── templates/                  # HTML pages
├── static/
│   ├── img/                   # Images
│   └── uploads/               # Game files
└── requirements.txt
```

## Key Routes

- `/` - Login page
- `/buyer_dashboard` - Game storefront
- `/dev_dashboard` - Developer panel
- `/admin_dashboard` - Admin panel
- `/ViewCart` - Shopping cart
- `/AddMonitorWallet` - Wallet management


**Port in use?**
Change port in `app.py` or kill the process using port 5001

**Database issues?**
Database auto-creates on first run. Just restart the app.

## Development

The platform is fully functional with:
- User authentication (3 roles)
- Complete e-commerce flow
- Payment integration
- Responsive design
- Friend and review systems

## Deployment

For production:
1. Set `debug=False` in app.py
2. Use PostgreSQL instead of SQLite
3. Set up SSL certificate
4. Configure environment variables

---

**Status:** Production Ready ✅

Built with Flask • Styled with 

