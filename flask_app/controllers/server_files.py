from flask_app import app


@app.route('/robots.txt')
def show_robots_txt_file():
    return app.send_static_file('server/robots.txt')


@app.route('/sitemap.txt')
def show_sitemap_txt_file():
    return app.send_static_file('server/sitemap.txt')


@app.route('/google819397e3929bb667.html')
def show_google_search_console_html_file():
    return app.send_static_file('server/google/google819397e3929bb667.html')


