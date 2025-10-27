document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 1200,
        once: true,
        offset: 100,
        easing: 'ease-out-cubic'
    });

    const locationCards = document.querySelectorAll('.location-card.clickable, .luxury-location-card');
    locationCards.forEach(card => {
        card.addEventListener('click', function(e) {
            const location = this.getAttribute('data-location');
            const link = this.querySelector('a');
            if (location) {
                window.location.href = location;
            } else if (link) {
                window.location.href = link.getAttribute('href');
            }
        });
    });

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        } else {
            navbar.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
    }
});
