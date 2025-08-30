# Muhavi's Blog

A modern, responsive blog application built with Django and Bootstrap. This project includes user authentication, post creation/editing, image uploads, and a commenting system.

![Django](https://img.shields.io/badge/Django-4.2.7-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🚀 **Modern UI**: Beautiful, responsive design with Bootstrap 5
- 👤 **User Authentication**: Login/logout functionality with Django admin
- ✍️ **Post Management**: Create, edit, and delete blog posts
- 🖼️ **Image Uploads**: Add images to your blog posts
- 💬 **Comments System**: Users can comment on posts
- 📱 **Responsive Design**: Works perfectly on desktop and mobile
- 🔒 **Security**: CSRF protection and user permissions

## Project Structure

```
Django Project/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── myproject/               # Main project directory
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── blog/                    # Blog application
│   ├── __init__.py
│   ├── admin.py             # Admin interface configuration
│   ├── apps.py              # App configuration
│   ├── forms.py             # Django forms
│   ├── models.py            # Database models
│   ├── urls.py              # App URL patterns
│   └── views.py             # View functions
└── templates/               # HTML templates
    ├── base.html            # Base template
    └── blog/                # Blog-specific templates
        ├── home.html
        ├── post_detail.html
        ├── create_post.html
        ├── edit_post.html
        └── delete_post.html
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Download

If you haven't already, make sure you have all the project files in your directory.

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Step 5: Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user account.

### Step 6: Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Admin Panel

1. Go to `http://127.0.0.1:8000/admin/`
2. Login with your superuser credentials
3. Manage users, posts, and comments from the admin interface

### Blog Features

1. **View Posts**: Visit the home page to see all blog posts
2. **Create Post**: Click "New Post" (requires login)
3. **Edit Post**: Click "Edit" on your own posts
4. **Delete Post**: Click "Delete" on your own posts
5. **Add Comments**: Comment on any post (requires login)

## Configuration

### Environment Variables

Create a `.env` file in the project root for production settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### For GitHub Deployment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/muhavi-blog.git
   cd muhavi-blog
   ```

2. **Set up environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure settings**:
   - Copy `.env.example` to `.env`
   - Update `SECRET_KEY` with a secure key
   - Set `DEBUG=False` for production

4. **Database setup**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Database

The project uses SQLite by default. For production, consider using PostgreSQL or MySQL by updating the `DATABASES` setting in `settings.py`.

## Customization

### Adding New Features

1. **New Models**: Add to `blog/models.py`
2. **New Views**: Add to `blog/views.py`
3. **New Templates**: Add to `templates/blog/`
4. **New URLs**: Add to `blog/urls.py`

### Styling

- Modify `templates/base.html` for global styles
- Update individual templates for specific page styling
- Add custom CSS in the `<style>` section of templates

## Technologies Used

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, Font Awesome
- **Database**: SQLite (default)
- **Forms**: Django Crispy Forms
- **Configuration**: python-decouple

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions, please create an issue in the repository or contact the development team.

---

**Happy Blogging! 🚀**
